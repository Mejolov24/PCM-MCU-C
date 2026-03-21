import os
import re
import ffmpeg
import numpy as np
# sys.argv is a list of command-line arguments
# sys.argv[0] is the path to the script itself
# sys.argv[1:] contains the paths of the dropped files

run_path = os.path.dirname(os.path.abspath(__file__))
cache_dir = os.path.join(run_path, "output")
cache_file = os.path.join(cache_dir, "settings.txt")
output_file = os.path.join(cache_dir, "output.h")
def convert_to_pcm(input_file, sample_rate, bit_depth):
    output_file = os.path.join(
    run_path,
    "output",
    os.path.basename(input_file) + ".raw"
)

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
            ar=sample_rate     # sample rate
        )
        .overwrite_output()
        .run()
    )

    return output_file

def check_missing_files():
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    if not os.path.exists(cache_file):
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("")
    
    if not os.path.exists(output_file):
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("")

def sanitize_filename(file_path):
    # Get the base name without extension
    base = os.path.splitext(os.path.basename(file_path))[0]
    
    # Remove any suffix
    base = re.sub(r'.(mp3|wav)$', '', base, flags=re.IGNORECASE)
    
    # Replace any non-alphanumeric characters with underscore
    base = re.sub(r'\W|^(?=\d)', '_', base)
    
    return base

import os


def get_cache():
    #Return [sample_rate, bit_depth] or None if cache is missing/corrupted
    if not os.path.exists(cache_file):
        return None
    try:
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        parts = content.split(";")[:2]
        # ensure both parts are valid integers
        sample_rate = int(parts[0])
        bit_depth = int(parts[1])
        return [sample_rate, bit_depth]
    except (ValueError, IndexError):
        return None  # corrupted or incomplete cache
    except Exception:
        return None  # any other unexpected error

def check_cache(sample_rate, bit_depth):
    #Return True if settings changed, False otherwise
    cache = get_cache()
    if cache is None:
        return True  # new settings needed
    return cache != [sample_rate, bit_depth]

def save_cache(sample_rate, bit_depth):
    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(f"{sample_rate};{bit_depth};")
    


def convert_files(files,sample_rate,bit_depth):
    new_settings : bool = check_cache(sample_rate,bit_depth)

    if new_settings:
        print("Settings changed, overwritting existing files...")
    else:
         print("No settings changed, skiping existing files...")

    print("\n")

    for file_path in files:

        file_name = os.path.basename(file_path)
        cache_file_path = os.path.join(run_path, "output",f"{file_name}.raw")

        if new_settings:
            convert_to_pcm(file_path,sample_rate,bit_depth)
           
        elif not os.path.exists(cache_file_path):
            
            convert_to_pcm(file_path,sample_rate,bit_depth)
    
    print("\n")
    print("Converted succesfully!")


def parse_to_h_file(sample_rate, bit_depth):
    print("Converting files...\n")
    raw_files = [
        os.path.join(cache_dir, f)
        for f in os.listdir(cache_dir)
        if f.lower().endswith(".raw")
    ]
    
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

        for file in raw_files:
                with open(file, "rb") as f2:
                    content = f2.read() 
                    name = sanitize_filename(file)
                    sample = np.frombuffer(content,dtype_map[bit_depth])
                    f.write(f"extern const int {name}_len = {len(sample)}; \n")
                    # Write the PROGMEM array
                    f.write(f"extern const {c_type_map[bit_depth]} {name}[] PROGMEM ={{\n")

                    for i in range(0, len(sample), 16):  # 16 per line
                        chunk = sample[i:i+16]
                        f.write(", ".join(str(int(s)) for s in chunk))
                        f.write(",\n")
                    f.write("};\n\n")
    print("Done!\n")


