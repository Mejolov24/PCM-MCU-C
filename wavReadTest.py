from pathlib import Path
import wavio
run_path = Path(__file__).parent.resolve()
file = run_path / "test.wav"

wavObj = wavio.read(str(file))

import struct

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


loops = read_wav_loops(str(file))

if loops:
    start, end = loops
    print(f"Start: {start}")
    print(f"End:   {end}")
else:
    print("No loop found")