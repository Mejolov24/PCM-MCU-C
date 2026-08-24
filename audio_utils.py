from pathlib import Path
import file_utils
import re
import ffmpeg
import numpy as np
import struct
import consolecolors as colors

def get_sample_rate(file):
    probe = ffmpeg.probe(str(file))
    
    for stream in probe['streams']:
        if stream['codec_type'] == 'audio':
            return int(stream['sample_rate'])
    
    return None

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


def resample_loop(loop,original_rate,target_rate):
    if not loop : return None
    ratio = target_rate / original_rate
    return (round(loop[0] * ratio), round(loop[1] * ratio))



def convert_files(sample_rate,bit_depth, new_settings : bool, input_dir, output_dir):
    global errors
    errors = 0

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
                colors.cprint(f"[ERR] File {file_path.name} name index out of range, skiping file","red")
                errors += 1
        else: unnumbered.append(file_path)
    un_idx = 0
    for i in range(128):
        if slots[i] is None and un_idx < len(unnumbered):
            slots[i] = unnumbered[un_idx]
            un_idx += 1
    return slots

def organize_folders(dirs):
    global errors
    slots = [None] * 128
    unnumbered = []

    for d in dirs:
        match = re.match(r'^(\d+)', d.name)
        if match:
            idx = int(match.group(1))
            if idx < 128:
                slots[idx] = d
        else:
            unnumbered.append(d)
            colors.cprint(f"[WARN] File {d.name} name index too big or unnumbered, assigned on freee space ","yellow")
            errors += 1


    un_idx = 0
    for i in range(128):
        if slots[i] is None and un_idx < len(unnumbered):
            slots[i] = unnumbered[un_idx]
            un_idx += 1
    if un_idx < len(unnumbered):
        for f in unnumbered[un_idx:]:
            colors.cprint(f"[ERR] File {f.name} ignored no free slot available in 128-slot bank","red")
            errors += 1

    return [d for d in slots if d is not None]

def parse_to_h_file(sample_rate,bit_depth, input_dir, output_file):
    global errors
    errors = 0
    colors.cprint("\n[INFO] Parsing samples...\n", "blue")
    dtype_map = {
        8: np.int8,
        16: np.int16,
        32: np.int32,
        64: np.int64,
    }
    with open(output_file, "w") as file:
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

        all_dirs = [input_dir] + [d for d in input_dir.rglob("*") if d.is_dir()]

        for current_dir in all_dirs:
            folder_array_name = file_utils.sanitize_filename(current_dir)
            raw_files = [f for f in current_dir.glob("*.pcm") if f.is_file()]
            slots = organize_sample(raw_files)
            occupied_entries = {}
            colors.cprint(f"\n[INFO] Processing Folder : {current_dir.relative_to(input_dir)}", "blue")
            for i, file_path in enumerate(slots):
                if file_path is None : continue
                colors.cprint(f"[INFO] Processing File : {file_path.name}", "blue")
                var_name = f"{folder_array_name}_{file_utils.sanitize_filename(file_path)}"
                var_name = re.sub(r'_+', '_', var_name)
                display_name = file_utils.sanitize_filename(file_path).lstrip('_')
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


def parse_to_spack(sample_rate, bit_depth, ALIGNMENT, input_dir, output_file):
    global errors
    errors = 0

    raw_dirs = [d for d in input_dir.iterdir() if d.is_dir()]
    target_dirs = organize_folders(raw_dirs)

    with open(output_file, "wb") as file:

        # ---------------- HEADER ----------------
        file.write(b"SPK1")
        file.write(struct.pack("<III",
            len(target_dirs),
            sample_rate,
            bit_depth
        ))

        # reserve directory
        directory_pos = file.tell()
        file.write(b"\x00" * (len(target_dirs) * 4))

        folder_offsets = []
        metadata_entries = []
        string_entries = []

        # ---------------- WRITE METADATA TABLES ----------------
        for current_dir in target_dirs:
            colors.cprint(f"\n[INFO] Processing Folder : {current_dir.relative_to(input_dir)}", "blue")
            folder_offsets.append(file.tell())

            raw_files = [f for f in current_dir.glob("*.pcm")]
            slots = organize_sample(raw_files)

            for i in range(128):
                file_path = slots[i]
                if (file_path) : colors.cprint(f"[INFO] Processing File : {Path(file_path).name}", "blue")

                if file_path is None:
                    file.write(b"\x00" * 20)
                    continue

                magic, size, sr, bd, loopA, loopB = read_header(file_path)
                name = file_utils.sanitize_filename(file_path).lstrip('_')

                meta_pos = file.tell()

                # write EMPTY struct (we'll fill later)
                file.write(struct.pack("<IIIII", 0, 0, 0, 0, 0))

                metadata_entries.append({
                    "meta_pos": meta_pos,
                    "file": file_path,
                    "name": name,
                    "length": size // (bit_depth // 8),
                    "loopA": loopA,
                    "loopB": loopB
                })

        # ---------------- STRING POOL ----------------
        for entry in metadata_entries:
            entry["name_offset"] = file.tell()
            file.write(entry["name"].encode() + b'\x00')

        # ---------------- AUDIO DATA ----------------
        for entry in metadata_entries:
            # align
            curr = file.tell()
            padding = (ALIGNMENT - (curr % ALIGNMENT)) % ALIGNMENT
            file.write(b'\x00' * padding)

            entry["data_offset"] = file.tell()

            pcm_bytes = entry["file"].read_bytes()[24:]
            file.write(pcm_bytes)

        # ---------------- PATCH METADATA ----------------
        for entry in metadata_entries:
            file.seek(entry["meta_pos"])

            file.write(struct.pack("<IIIII",
                entry["name_offset"],
                entry["data_offset"],
                entry["length"],
                entry["loopA"],
                entry["loopB"]
            ))

        # ---------------- PATCH DIRECTORY ----------------
        file.seek(directory_pos)
        for off in folder_offsets:
            file.write(struct.pack("<I", off))

    if errors == 0:
        colors.cprint(f"\n[OK] Finished with no errors.","green")
    else:
        colors.cprint(f"\n[WARN] Finished with {errors} errors.","red")