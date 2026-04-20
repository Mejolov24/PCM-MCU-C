# PCM-MCU-C
![Alt text](https://raw.githubusercontent.com/Mejolov24/PCM-MCU-C/refs/heads/main/thumbnails/thumbnail01.png)
Convertion of files to .pcm format to allow fast access in micro controllers via single .h file or multiple files if you have an sd card

## Required dependencies:
[ffmpeg-python](https://pypi.org/project/ffmpeg-python/)
[numpy](https://pypi.org/project/numpy/)

## Usage
create a folder and extract the zip in it.
run main.py
then choose from the 2 avalible options:

1 : convert files
2 : parse into .h file

If its the first time running the script or something went wrong with the settings.txt file,
then you must configure how you want the audio to be processed.

If you already have a config.txt file (made automaticly when missing and updated when changing setttings)
then you can skip configurating by pressing enter and use your past settings.

To ensure anyone using your files can read them correctly (whether in Godot, Arduino, or plain C), here is the technical breakdown of the **24-byte custom header** your script generates.

This header is prepended to every `.pcm` file when you run **Mode 1**.

### Binary Structure
The header is composed of **6 unsigned 32-bit integers** (4 bytes each) using **Little-Endian** byte order.

| Offset | Size | Name | Description |
| :--- | :--- | :--- | :--- |
| **0** | 4 | `Magic Number` | Always `0x50434D21` (ASCII for **"PCM!"**). Used to verify the file format. |
| **4** | 4 | `Data Size` | The size of the raw audio data in bytes (excluding this header). |
| **8** | 4 | `Sample Rate` | The playback frequency (e.g., `44100`, `22050`). |
| **12** | 4 | `Bit Depth` | Either `8` or `16`. Tells the MCU how to cast the data pointer. |
| **16** | 4 | `Loop Start` | The sample index where the loop begins. |
| **20** | 4 | `Loop End` | The sample index where the loop ends. |

---

### Why this is better than a standard WAV header:
1.  **Fixed Size:** Unlike WAV headers (which can have extra "metadata" chunks that vary in length), your header is **always exactly 24 bytes**. You can simply skip the first 24 bytes to get straight to the audio.
2.  **Integrated Loop Points:** Standard audio files don't store loop information. By baking the `loop_start` and `loop_end` directly into the file, your microcontroller doesn't need a separate config file to know how to loop a sample.
3.  **Low Overhead:** It uses only 24 bytes of storage, whereas a full WAV header is usually 44 bytes or more.

### How to read it in C
If you are reading these files from an SD card, you can map a struct directly onto the first 24 bytes:

```c
typedef struct {
    uint32_t magic;      // 0x50434D21
    uint32_t size;       // Total audio bytes
    uint32_t rate;       // Hz
    uint32_t depth;      // 8 or 16
    uint32_t loopA;      // Start
    uint32_t loopB;      // End
} PCMHeader;

```

## Output folder
after filling out the settings and conversion finishes, everything will be saved onto /output, wich is an exact replica of /input, so your folder structure is kept.

when picking mode 1, all audio will be saved in a .pcm format, used as cache for when settings dont change.

when picking mode 2, all audios will be saved into a single output.h file

## output.h file

### Constants :

const int SampleRate = uint16_t;
const int BitDepth = uint8_t;

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
