# PCM-MCU-C
![Alt text](https://raw.githubusercontent.com/Mejolov24/PCM-MCU-C/refs/heads/main/thumbnails/thumbnail02.png)
Python utility to convert multiple audio files onto .pcm, .spack and .h files for microcontroller usage

## Required dependencies (uv/venv supported):
[ffmpeg-python](https://pypi.org/project/ffmpeg-python/)
[numpy](https://pypi.org/project/numpy/)

## Usage
create a folder and extract the zip in it.
run main.py
then choose from the avalible options:

 - Convert to .pcm
 - Convert .sf2 to .pcm
 - Convert to .h
 - Convert to .spack
 - Configure

if you want to use any of the other file types, you must first convert to .pcm

## Output folder
after the conversion finishes, everything will be saved onto /output, wich is an exact replica of /input, so your folder structure is kept.

upon making .spacks, /output and /output/sf2 are treated as if they were separate dirs, everytime you convert, it will make a .spack for all sf2 sub folders, and one .spack for /output


### .pcm Binary Structure
The header is composed of **6 unsigned 32-bit integers** (4 bytes each) using **Little-Endian** byte order.

| Offset | Size | Name | Description |
| :--- | :--- | :--- | :--- |
| **0** | 4 | `Magic Number` | Always `0x50434D21` (ASCII for **"PCM!"**). Used to verify the file format. |
| **4** | 4 | `Data Size` | The size of the raw audio data in bytes (excluding this header). |
| **8** | 4 | `Sample Rate` | The playback frequency (e.g., `44100`, `22050`). |
| **12** | 4 | `Bit Depth` | Either `8` or `16`. Tells the MCU how to cast the data pointer. |
| **16** | 4 | `Loop Start` | The sample index where the loop begins. |
| **20** | 4 | `Loop End` | The sample index where the loop ends. |

### .spack Binary Structure

| Offset | Size | Name | Description |
| :--- | :--- | :--- | :--- |
| **0** | 4 | `Magic Number` | Always `SPK1` (`0x53504B31`). Used to verify the container format. |
| **4** | 4 | `Bank Count` | Total number of Bank sections contained in the file. |
| **8** | 4 | `Sample Rate` | Global playback frequency for the audio assets. |
| **12** | 4 | `Bit Depth` | Bit depth per sample (e.g., `8` or `16`). |
| **16** | 4 * N | `Folder Offsets` | Array of N unsigned 32-bit integers storing absolute byte offsets to each folder block. |
| **Variable** | 128 * 20 | `Folder Block (Slots)` | Array of 128 fixed-size slot entries per folder (20 bytes each: `name_offset`, `data_offset`, `length`, `loopA`, `loopB`). Empty slots are 20 zero bytes. |
| **Variable** | Variable | `String Pool` | Sequential null-terminated UTF-8 strings (`\0`) for all sample names. |
| **Variable** | Variable | `Audio Data` | Raw PCM audio payloads, stripped of their 24-byte source headers and aligned to the custom `ALIGNMENT` byte boundary. |


## output.h file

### Constants :
```c
const int SampleRate = uint16_t;
const int BitDepth = uint8_t;
```

### .h structure:
For each folder inside /input, it will generate an array of 128 elements of SampleData for storing the samples in that folder. their index is determined by the number next to the name, so you can name the file 01_sample, 2_sample, 003_sample, etc. if it doesnt have a number, it will use whatever index is free.

```c

struct SampleData {
    const char* name;          // Sanitized filename for UI/display
    const intX_t *data;       // Pointer to the raw PCM data
    uint32_t length;           // Total number of samples
    uint32_t sample_rate;      // The sample rate of this specific file
    uint32_t loop_start;       // Loop start point (0 if no loop)
    uint32_t loop_end;         // Loop end point (0 if no loop)
};

// then they are put into the array this way:

const uint32_t name_len = ;
const intX_t name[] ={}

const struct SampleData folder[128] = {
    [0] = { "name", folder_name, name_len, sample rate, loop point A, loop point B },
    }
```

### .h example:
```c

#include <stdint.h>
const int SampleRate = 10;
const int BitDepth = 8;
struct SampleData {
    const char* name;
    const int8_t *data;
    uint32_t length;
    uint32_t sample_rate;
    uint32_t loop_start;
    uint32_t loop_end;

};

const struct SampleData output[128] = {
};

const int teto_001_kasane_len = 0; 
const int8_t teto_001_kasane[] ={
};

const int teto_002_teto_len = 0; 
const int8_t teto_002_teto[] ={
};

const int teto_003_is_len = 0; 
const int8_t teto_003_is[] ={
};

const int teto_004_the_len = 0; 
const int8_t teto_004_the[] ={
};

const int teto_005_best_len = 0; 
const int8_t teto_005_best[] ={
};

const struct SampleData teto[128] = {
    [1] = { "001_kasane", teto_001_kasane, teto_001_kasane_len, 10, 0, 0 },
    [2] = { "002_teto", teto_002_teto, teto_002_teto_len, 10, 0, 0 },
    [3] = { "003_is", teto_003_is, teto_003_is_len, 10, 0, 0 },
    [4] = { "004_the", teto_004_the, teto_004_the_len, 10, 0, 0 },
    [5] = { "005_best", teto_005_best, teto_005_best_len, 10, 0, 0 },
};
```
