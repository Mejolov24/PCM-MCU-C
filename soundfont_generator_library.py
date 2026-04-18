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

def convert_to_pcm(input_file,output_file, sample_rate, bit_depth):

    codec = 'pcm_s16le' if bit_depth == 16 else 'pcm_s8'
    fmt   = 's16le'     if bit_depth == 16 else 's8'

    (
        ffmpeg
        .input(str(input_file))
        .output(
            str(output_file),
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

def ensure_file(path):
    file = Path(path)
    if not file.exists():
        file.touch(exist_ok=True)

def fix_missing_files():
    ensure_dir(output_dir)
    ensure_file(output_settings)
    ensure_file(output_h)


def sanitize_filename(file_path):
    name = Path(file_path).stem
    
    name = re.sub(r'\W+', '_', name)
    
    if name[0].isdigit():
        name = "_" + name
        
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


def save_settings(sample_rate, bit_depth):
    output_settings.write_text(f"{sample_rate};{bit_depth};", encoding="utf-8")


def convert_filesold(files,sample_rate,bit_depth):
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

def convert_files(InputPath,sample_rate,bit_depth):
    current_config = [int(sample_rate), int(bit_depth)]
    new_settings : bool = (get_cache() != current_config)

    if new_settings:
        print("Settings changed, overwritting existing files...")
    else:
         print("No settings changed, skiping existing files...") 
    print("\n")

    all_dirs = [InputPath] + [d for d in InputPath.rglob("*") if d.is_dir()]

    for current_dir in all_dirs:
        files_in_foler = [f for f in current_dir.glob("*") if f.is_file()]
        if not files_in_foler:
            continue
    
        print(f"Processing Folder : {current_dir.relative_to(InputPath)}")
        for file_path in files_in_foler:
            relative_path = file_path.relative_to(InputPath)
            output_file_path = output_dir / relative_path.with_suffix(".pcm")
            output_file_path.parent.mkdir(parents=True,exist_ok=True)
            if new_settings or not output_file_path.exists():
                convert_to_pcm(file_path,output_file_path,sample_rate,bit_depth)
    print("\nConverted successfully!")

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

    with open(output_h, "w") as f:
        
        f.write(f"const int SampleRate = {sample_rate};\n")
        f.write(f"const int BitDepth = {bit_depth};\n")

        for file_path in raw_files:
            content = file_path.read_bytes()
            name = sanitize_filename(file_path)
            sample = np.frombuffer(content, dtype=dtype_map[bit_depth])
            f.write(f"const int {name}_len = {len(sample)}; \n")
            f.write(f"const {c_type_map[bit_depth]} {name}[] ={{\n")

            for i in range(0, len(sample), 16):
                chunk = sample[i:i+16]
                f.write(", ".join(str(int(s)) for s in chunk))
                f.write(",\n")
            f.write("};\n\n")
    print("Done!\n")


