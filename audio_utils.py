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

    raw_dirs = [d for d in input_dir.iterdir() if d.is_dir() and d.name != "sf2"]
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


def sanitize(name):
  return "".join(
      c if c.isalnum() or c in (" ", "_", "-") else "_" for c in name
  ).strip()


def parse_sf2(file_path):
  with open(file_path, "rb") as f:
    if f.read(4) != b"RIFF" or f.read(4) and f.read(4) != b"sfbk":
      raise ValueError("Invalid SoundFont")
    f.seek(12)
    chunks = {}

    def walk(end):
      while f.tell() < end:
        cid, size = f.read(4), struct.unpack("<I", f.read(4))[0]
        pos = f.tell()
        if cid == b"LIST":
          f.read(4)
          walk(pos + size)
        else:
          chunks[cid] = f.read(size)
        if size % 2:
          f.seek(1, 1)

    walk(file_path.stat().st_size)
  return chunks


def get_gens(bag_data, gen_data, idx):
  if not bag_data or not gen_data or idx >= len(bag_data) // 4 - 1:
    return []
  s, _ = struct.unpack("<HH", bag_data[idx * 4 : idx * 4 + 4])
  e, _ = struct.unpack("<HH", bag_data[(idx + 1) * 4 : (idx + 1) * 4 + 4])
  return [
      struct.unpack("<Hh", gen_data[g * 4 : g * 4 + 4]) for g in range(s, e)
  ]


def resample(data, ratio):
  if ratio == 1.0 or not data:
    return data
  orig = struct.unpack(f"<{len(data)//2}h", data)
  new_len = max(1, int(len(orig) / ratio))
  res = []
  for i in range(new_len):
    idx = i * ratio
    lo = int(idx)
    if lo >= len(orig) - 1:
      res.append(orig[-1])
    else:
      val = int(orig[lo] + (orig[lo + 1] - orig[lo]) * (idx - lo))
      res.append(max(-32768, min(32767, val)))
  return struct.pack(f"<{len(res)}h", *res)

def write_wav(path, data, rate, loop_s, loop_e, pitch):
  has_loop = loop_e > loop_s > 0
  smpl = (
      struct.pack(
          "<15I", 0, 0, 0, pitch, 0, 0, 0, 1, 0, 0, 0, loop_s, loop_e, 0, 0
      )
      if has_loop
      else b""
  )
  sz = 4 + 24 + 8 + len(data) + (len(smpl) + 8 if has_loop else 0)
  with open(path, "wb") as f:
    f.write(
        b"RIFF"
        + struct.pack("<I", sz)
        + b"WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00"
        + struct.pack("<IIHH", rate, rate * 2, 2, 16)
    )
    if has_loop:
      f.write(b"smpl" + struct.pack("<I", len(smpl)) + smpl)
    f.write(b"data" + struct.pack("<I", len(data)) + data)


def sf2_to_wav(sf2 : Path, out_dir : Path, do_resample : bool, base_note : int):
  c = parse_sf2(sf2)
  if not all(k in c for k in (b"smpl", b"phdr", b"shdr")):
    raise ValueError("Missing essential chunks")

  samples = []
  for i in range(len(c[b"shdr"]) // 46 - 1):
    e = c[b"shdr"][i * 46 : (i + 1) * 46]
    n, st, ed, lst, led, rate, pit, _, _, typ = struct.unpack("<20s5IBbHH", e)
    samples.append({
        "name": n.decode("ascii", errors="ignore").rstrip("\x00") or f"s_{i}",
        "st": st,
        "ed": ed,
        "lst": lst,
        "led": led,
        "rate": rate,
        "pit": pit,
        "typ": typ,
    })

  insts = []
  for i in range(len(c[b"inst"]) // 22 - 1):
    n, bdx = struct.unpack("<20sH", c[b"inst"][i * 22 : (i + 1) * 22])
    insts.append({
        "name": n.decode("ascii", errors="ignore").rstrip("\x00") or f"i_{i}",
        "bdx": bdx,
    })
  insts.append({"name": "EOP", "bdx": len(c[b"ibag"]) // 4 if b"ibag" in c else 0})

  base_out_dir = Path(out_dir)
  phdr, count = c[b"phdr"], 0

  for p in range(len(phdr) // 38 - 1):
    p_bytes = phdr[p * 38 : (p + 1) * 38]
    nxt_bytes = phdr[(p + 1) * 38 : (p + 2) * 38]
    name, pnum, bank, bdx = struct.unpack("<20sHHH", p_bytes[:26])
    next_bdx = struct.unpack("<20sHHH", nxt_bytes[:26])[3]
    pname = name.decode("ascii", errors="ignore").rstrip("\x00") or f"p_{p}"

    tdir = base_out_dir / f"{bank}_bank"
    tdir.mkdir(parents=True, exist_ok=True)

    is_perc = bank == 128
    active_inst = None

    for bi in range(bdx, next_bdx):
      for op, amt in get_gens(c.get(b"pbag"), c.get(b"pgen"), bi):
        if op == 41:
          active_inst = amt
      if active_inst is None or not (0 <= active_inst < len(insts) - 1):
        continue

      ins = insts[active_inst]
      zones = []

      # Collect all valid zones for this instrument configuration
      for ib in range(ins["bdx"], insts[active_inst + 1]["bdx"]):
        s_idx, root, lo, hi = None, 60, 0, 127
        for op, amt in get_gens(c.get(b"ibag"), c.get(b"igen"), ib):
          if op == 53:
            s_idx = amt
          elif op == 58 and amt >= 0:
            root = amt
          elif op == 43:
            lo, hi = amt & 0xFF, (amt >> 8) & 0xFF

        if (
            s_idx is not None
            and 0 <= s_idx < len(samples)
            and not (samples[s_idx]["typ"] & 0x8000)
        ):
          smpl = samples[s_idx]
          if root == 60 and smpl["pit"] > 0:
            root = smpl["pit"]
          zones.append({"s_idx": s_idx, "root": root, "lo": lo, "hi": hi})

      if not zones:
        continue

      # For melodic instruments, pick the single zone closest to MIDI base_note
      if not is_perc:
        valid_zones = [z for z in zones if z["lo"] <= base_note <= z["hi"]]
        if not valid_zones:
          # Fallback: pick the zone whose root/center is closest to base_note if none explicitly bracket it
          valid_zones = zones
        best_zone = min(valid_zones, key=lambda z: abs(z["root"] - base_note))
        target_zones = [best_zone]
      else:
        target_zones = zones  # Percussion maps all individual drum pads

      for z in target_zones:
        s_idx = z["s_idx"]
        root = z["root"]
        smpl = samples[s_idx]

        audio = c[b"smpl"][smpl["st"] * 2 : smpl["ed"] * 2]
        ls = smpl["lst"] - smpl["st"] if smpl["led"] > smpl["lst"] else 0
        le = smpl["led"] - smpl["st"] if smpl["led"] > smpl["lst"] else 0
        if ls < 0 or le > len(audio) // 2:
          ls = le = 0

        # Conditional Resampling
        if not is_perc and root != base_note and do_resample:
          ratio = 2.0 ** ((base_note - root) / 12.0)
          audio = resample(audio, ratio)
          ls, le = (
              (int(ls / ratio), int(le / ratio))
              if ls > 0 and le > ls
              else (0, 0)
          )
          pitch = base_note
        else:
          pitch = root

        fname = f"{pnum:03d}_{sanitize(smpl['name'])}.wav"
        write_wav(
            tdir / fname,
            audio,
            smpl["rate"],
            ls,
            le,
            pitch,
        )
        colors.cprint(f"[INFO] [Bank {bank}] Saved: {fname}","blue")
        count += 1
