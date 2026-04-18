from pathlib import Path
import re
import ffmpeg
import numpy as np
# sys.argv is a list of command-line arguments
# sys.argv[0] is the path to the script itself
# sys.argv[1:] contains the paths of the dropped files

run_path = Path(__file__).parent.resolve()
output_dir = run_path / "output"
output_settings = output_dir / "settings.txt"
output_h = output_dir / "output.h"

def convert_to_pcm(input_file, sample_rate, bit_depth):
    input_path = Path(input_file)
    output_file = output_dir / (input_path.name + ".pcm")

    codec = 'pcm_s16le' if bit_depth == 16 else 'pcm_s8'
    fmt   = 's16le'     if bit_depth == 16 else 's8'

    (
        ffmpeg
        .input(input_file)
        .output(
            output_file,
            format=fmt,
            acodec=codec,
            ac=1,              # mono
            ar=sample_rate
        )
        .overwrite_output()
        .run()
    )

    return output_file

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def sanitize_filename(file_path):
    # Get the filepath file name sanitized for C, removing extension and special characters.
    name = Path(file_path).stem
    name = re.sub(r'\W^(?=\d)', '_',name)
    return name

def get_cache():
    #Return [sample_rate, bit_depth] or None if cache is missing/corrupted
    if not output_settings.exists():
        return None
    try:
        content = output_settings.read_text(encoding="utf-8").strip()
        parts = content.split(";"[:2])
        return [int(parts[0]),int(parts[1])]
    except (ValueError,IndexError,Exception):
        return None


def save_cache(sample_rate, bit_depth):
    output_settings.mkdir(parents=True,exist_ok=True)
    output_settings.write_text(f"{sample_rate};{bit_depth};", encoding="utf-8")


def convert_files(files,sample_rate,bit_depth):
    new_settings : bool = (get_cache() != [sample_rate, bit_depth])

    if new_settings:
        print("Settings changed, overwritting existing files...")
    else:
         print("No settings changed, skiping existing files...")

    print("\n")

    for file_path in files:
        file_path = Path(file_path)
        output_file_path = output_dir / f"{file_path}.pcm"
        if new_settings or not output_file_path.exists():
            convert_to_pcm(file_path,sample_rate,bit_depth)
        
    
    print("\n")
    print("Converted succesfully!")


def parse_to_h_file(sample_rate, bit_depth):
    print("Converting files...\n")
    raw_files = list(output_dir.glob("*.pcm"))
    dtype_map = {
        8: np.int8,
        16: np.int16,
        32: np.int32,
        64: np.int64,
    }

    c_type_map = {
        8: "unsigned char",
        16: "int16_t",
        32: "int32_t",
        64: "int64_t",
    }

    with open(output_file, "w") as f:
        
        f.write(f"const int SampleRate = {sample_rate};\n")
        f.write(f"const int BitDepth = {bit_depth};\n")

        for file_path in raw_files:
            content = file_path.read_bytes()
            name = sanitize_filename(file_path)
            sample = np.frombufer(content, dtype=dtype_map[bit_depth])
            file_path.write(f"const int {name}_len = {len(sample)}; \n")
            file_path.write(f"const {c_type_map[bit_depth]} {name}[] PROGMEM ={{\n")

            for i in range(0, len(sample), 16):
                chunk = sample[i:i+16]
                file_path.write(", ".join(str(int(s)) for s in chunk))
                file_path.write(",\n")
            file_path.write("};\n\n")
    print("Done!\n")


