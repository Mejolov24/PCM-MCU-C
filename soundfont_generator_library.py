from pathlib import Path
import shutil
import re
import ffmpeg
import numpy as np
import struct
import consolecolors as colors


run_path = Path(__file__).parent.resolve()
input_dir = run_path / "input"
output_dir = run_path / "output"
output_settings = output_dir / "settings.txt"
output_h = output_dir / "output.h"

errors = 0

def has_loop_log(loop):
    if loop:
        colors.cprint(f"[INFO] loop point found :  {colors.ctext("true", "green")}","blue")
        print(f"point A : {loop[0]}")
        print(f"point B : {loop[1]}")
    else:
        colors.cprint(f"[INFO] loop point found :  {colors.ctext("false", "red")}", "blue")


def build_header(data_byte_size,sample_rate,bit_depth,loop):
    magic = 0x50434D21  # "PCM!"
    loopA = loop[0] if loop else 0
    loopB = loop[1] if loop else 0
    
    header = struct.pack(
        "<I I I I I I",
        magic,
        data_byte_size,
        sample_rate,
        bit_depth,
        loopA,
        loopB
    )

    return header

def read_header(file_path):
    with open(file_path, "rb") as f:
        header_bytes = f.read(24)

    magic, size, sr, bd, loopA, loopB = struct.unpack("<I I I I I I", header_bytes)

    return magic, size, sr, bd, loopA, loopB


def cleanup_stale_files(source_dir, output_dir):
    for item in sorted(output_dir.rglob("*"), reverse=True):
        if item.name in ["settings.txt", "output.h"]:
            continue
        rel_path = item.relative_to(output_dir)
        source_item = source_dir / rel_path

        if item.is_file():
            base_name = rel_path.with_suffix('')
            if not list(source_dir.glob(f"{base_name}.*")):
                item.unlink()
                colors.cprint(f"[WARN] Removing stale file: {item.name}\nThis is caused by deleting, removing or renaming a file in /input, if this wasnt intended, convert files again.", "yellow")
        
        elif item.is_dir():
            if not source_item.exists():
                shutil.rmtree(item)
                colors.cprint(f"[WARN] Removing stale folder: {item.name}\nThis is caused by deleting, removing or renaming a folder in /input, if this wasnt intended, convert files again.", "yellow")
def convert_to_pcm(input_file, output_file, sample_rate, bit_depth,loop):
    codec = 'pcm_s16le' if bit_depth == 16 else 'pcm_s8'
    fmt   = 's16le'     if bit_depth == 16 else 's8'
    try:
        pcm_data, _ = (
            ffmpeg
            .input(str(input_file))
            .output(
                'pipe:',
                format=fmt,
                acodec=codec,
                ac=1,              # mono
                ar=sample_rate
            )
            .run(capture_stdout=True, capture_stderr=True)
        )
        header = build_header(len(pcm_data),sample_rate,bit_depth,loop)
        
        with open(output_file,"wb") as file:
            file.write(header)
            file.write(pcm_data)
        
        colors.cprint("[OK] File Done","green")

    except ffmpeg.Error as e:
        print(f"{colors.ctext("[ERR] ffmpeg failed", "red")} Error Code : {e.stderr.decode()}")

def read_wav_loops(filename):
    with open(filename, "rb") as f:
        data = f.read()

    offset = 12

    while offset < len(data):
        chunk_id = data[offset:offset+4]
        chunk_size = struct.unpack("<I", data[offset+4:offset+8])[0]

        if chunk_id == b'smpl':
            num_loops = struct.unpack("<I", data[offset+36:offset+40])[0]

            if num_loops == 0:
                return None

            loop_offset = offset + 44

            start = struct.unpack("<I", data[loop_offset+8:loop_offset+12])[0]
            end   = struct.unpack("<I", data[loop_offset+12:loop_offset+16])[0]

            return (start, end)

        offset += 8 + chunk_size

    return None

def clear_directory(dir_path):
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)  
    path.mkdir(parents=True, exist_ok=True)

def get_sample_rate(file):
    probe = ffmpeg.probe(str(file))
    
    for stream in probe['streams']:
        if stream['codec_type'] == 'audio':
            return int(stream['sample_rate'])
    
    return None

def resample_loop(loop,original_rate,target_rate):
    if not loop : return None
    ratio = target_rate / original_rate
    return (round(loop[0] * ratio), round(loop[1] * ratio))

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_file(path):
    file = Path(path)
    if not file.exists():
        file.touch(exist_ok=True)

def fix_missing_files():
    ensure_dir(input_dir)
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



def convert_files(sample_rate,bit_depth):
    global errors
    errors = 0
    cleanup_stale_files(input_dir,output_dir)
    current_config = [int(sample_rate), int(bit_depth)]
    new_settings : bool = (get_cache() != current_config)

    if new_settings:
        clear_directory(output_dir)
        colors.cprint("\n[WARN] Settings changed, deleting /output...\n", "yellow")
    else:
         colors.cprint("\n[INFO] No settings changed, skipping existing files...\n", "blue")

    all_dirs = [input_dir] + [d for d in input_dir.rglob("*") if d.is_dir()]

    for current_dir in all_dirs:
        files_in_foler = [f for f in current_dir.glob("*") if f.is_file()]
        if not files_in_foler:
            continue
    
        colors.cprint(f"\n[INFO] Processing Folder : {current_dir.relative_to(input_dir)}", "blue")
        for file_path in files_in_foler:
            relative_path = file_path.relative_to(input_dir)
            output_file_path = output_dir / relative_path.with_suffix(".pcm")
            output_file_path.parent.mkdir(parents=True,exist_ok=True)
            if new_settings or not output_file_path.exists():

                original_sample_rate = get_sample_rate(file_path)
                original_loop_point = read_wav_loops(file_path)
                
                colors.cprint(f"\n[INFO] Processing File : {file_path.name}", "blue")
                new_loop_points =  resample_loop(original_loop_point, original_sample_rate, sample_rate)
                has_loop_log(new_loop_points)
                convert_to_pcm(file_path,output_file_path,sample_rate,bit_depth,new_loop_points)
    colors.cprint("\n[OK] Converted successfully!","green")


def organize_sample(files_in_folder):
    global errors
    slots = [None] * 128
    unnumbered = []
    for file_path in files_in_folder:
        match = re.match(r'^(\d+)',file_path.name)
        if match:
            idx = int(match.group(1))
            if idx < 128:
                slots[idx] = file_path
            else: 
                colors.cprint(f"[ERR] File {file_path.name} name index too big, skiping file","red")
                errors += 1
        else: unnumbered.append(file_path)
    un_idx = 0
    for i in range(128):
        if slots[i] is None and un_idx < len(unnumbered):
            slots[i] = unnumbered[un_idx]
            un_idx += 1
    return slots

def parse_to_h_file(sample_rate,bit_depth):
    global errors
    errors = 0
    cleanup_stale_files(input_dir,output_dir)
    colors.cprint("\n[INFO] Parsing samples...\n", "blue")
    dtype_map = {
        8: np.int8,
        16: np.int16,
        32: np.int32,
        64: np.int64,
    }

    with open(output_h, "w") as file:
        file.write(f"#include <stdint.h>\n")
        file.write(f"const int SampleRate = {sample_rate};\n")
        file.write(f"const int BitDepth = {bit_depth};\n")

        file.write("struct SampleData {\n")
        file.write("    const char* name;\n")
        file.write(f"    const int{bit_depth}_t *data;\n")
        file.write("    uint32_t length;\n")
        file.write("    uint32_t sample_rate;\n")
        file.write("    uint32_t loop_start;\n")
        file.write("    uint32_t loop_end;\n\n")
        file.write("};\n\n")

        all_dirs = [output_dir] + [d for d in output_dir.rglob("*") if d.is_dir()]

        for current_dir in all_dirs:
            folder_array_name = sanitize_filename(current_dir)
            raw_files = [f for f in current_dir.glob("*.pcm") if f.is_file()]
            slots = organize_sample(raw_files)
            occupied_entries = {}
            colors.cprint(f"\n[INFO] Processing Folder : {current_dir.relative_to(output_dir)}", "blue")
            for i, file_path in enumerate(slots):
                if file_path is None : continue
                colors.cprint(f"[INFO] Processing File : {file_path.name}", "blue")
                var_name = f"{folder_array_name}_{sanitize_filename(file_path)}"
                var_name = re.sub(r'_+', '_', var_name)
                display_name = sanitize_filename(file_path).lstrip('_')
                display_name = re.sub(r'_+', '_', display_name)
                magic, size, sr, bd, loopA, loopB = read_header(file_path)
                occupied_entries[i] = f'{{ "{display_name}", {var_name}, {var_name}_len, {sr}, {loopA}, {loopB} }}'
                
                raw_data = file_path.read_bytes()
                sample_data = np.frombuffer(raw_data[24:], dtype=dtype_map[bit_depth])

                file.write(f"const int {var_name}_len = {len(sample_data)}; \n")
                file.write(f"const int{bit_depth}_t {var_name}[] ={{\n")
                colors.cprint("[OK] Parsed successfully!","green")
                for j in range(0, len(sample_data), 16):
                    chunk = sample_data[j:j+16]
                    file.write(", ".join(str(int(s)) for s in chunk))
                    file.write(",\n")
                file.write("};\n\n")
            file.write(f"const struct SampleData {folder_array_name}[128] = {{\n")

            for index, sample in occupied_entries.items():
                file.write(f"    [{index}] = {sample},\n")
            file.write("};\n\n")
    if errors == 0:
        colors.cprint(f"\n[OK] Finished with no errors.","green")
    else:
        colors.cprint(f"\n[WARN] Finished with {errors} errors.","red")


