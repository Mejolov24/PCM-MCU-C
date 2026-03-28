# PCM-MCU-C
![Alt text](https://raw.githubusercontent.com/Mejolov24/PCM-MCU-C/refs/heads/main/thumbnails/Captura%20de%20pantalla%202026-03-21%20204050.png)
Convertion of files to .raw pcm format to allow fast acces in micro controllers via single .h file or multiple files if you have an sd card

## Required dependencies:
[ffmpeg-python](https://pypi.org/project/ffmpeg-python/)

## Usage
create a folder and extract the zip in it.
run main.py
then choose from the 3 avalible options:

1 : convert files
2 : convert files and parse into h file
3 : parse existing files to h file

If its the first time running the script or something went wrong with the settings.txt file,
then you must configure how you want the audio to be processed.

If you already have a config.txt file (made automaticly when missing and updated when changing setttings)
then you can skip configurating by pressing enter


## Output folder
after filling out the settings and conversion finishes, everything will be saved onto /output

when picking modes 1 or 2, all audio will be saved in a .raw format, used as cache for when settings dont change,
you can use thosose .raw files in a sd card and read them directly since they dont have a header, just pure PCM (use config.txt to know sample and bit depth)

when picking mode 2 or 3, all audios will be saved into  a single output.h file with the minimum info needed.

## output.h file

### Constants :

const int SampleRate = number;
const int BitDepth = number;

### Samples are stored like this:

const int name_len = number;

const int16_t name[] PROGMEM ={}
