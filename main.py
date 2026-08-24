import audio_utils
import file_utils
import consolecolors as colors
from pathlib import Path
import shutil
import json
import menucli as menu
import logo
import copy

script_path = Path(__file__).parent.resolve()
input_dir = script_path / "input"
output_dir = script_path / "output"
output_settings = output_dir / "settings.txt"
output_h = output_dir / "output.h"
settings_path = script_path / "settings.json"

settings = {}
previous_settings = {}

DEFAULT_SETTINGS = {
    "bit_depth" : 16,
    "sampling_rate": 22050,
    "padding": 16
}

def fix_missing_files():
    file_utils.ensure_dir(input_dir)
    file_utils.ensure_dir(output_dir)
    file_utils.ensure_file(output_h)
    file_utils.ensure_file(settings_path)


def init_settings():
    global settings

    try:
        with open(settings_path, "rb") as file:
            settings = json.load(file)
    except json.decoder.JSONDecodeError:
        with open(settings_path, "w") as file:
            json.dump(DEFAULT_SETTINGS, file, indent=4)
        with open(settings_path, "rb") as file:
            settings = json.load(file)

def sync_json_settings():
    global settings

    with open(settings_path, "w") as file:
        json.dump(settings, file, indent=4)


def print_info():
    print("\033[H\033[2J")
    colors.cprint(logo.logo,"green")
    print("Pulse Code Modulation - MicroController - Converter - by Guillermo Beckers (Mejolov24 in github)")
    print("Convert any file into an uncompressed format stored as .pcm via ffmpeg, useful for playing audio in microcontrollers with low processing power")

def set_and_store_settings(index, value = None):
    global previous_settings, settings
    previous_settings = copy.deepcopy(settings)
    match index:
        case 0:
            settings["bit_depth"] = value
        case 1:
            settings["sampling_rate"] = value
        case 2:
            settings["padding"] = value
    sync_json_settings()
    init_settings()
    print_info()

def convert_files():
    new_settings : bool = (previous_settings != settings)

    if new_settings:
        file_utils.clear_directory(output_dir)
        colors.cprint("\n[WARN] Settings changed, deleting /output...\n", "yellow")
    else:
         colors.cprint("\n[INFO] No settings changed, skipping existing files...\n", "blue")

    audio_utils.convert_files(settings["sampling_rate"], settings["bit_depth"], new_settings,input_dir,output_dir)
    input(colors.ctext("Press Enter...","orange"))
    print_info()

def convert_to_h():
    audio_utils.parse_to_h_file(settings["sampling_rate"], settings["bit_depth"],output_dir, output_h)
    input(colors.ctext("Press Enter...","orange"))
    print_info()

def convert_to_spack():
    file_count = sum(1 for item in output_dir.rglob("*.spack") if item.is_file())
    output_spack = output_dir / f"{file_count}_{settings["bit_depth"]}_bits_{settings["sampling_rate"]}_hz.spack"
    audio_utils.parse_to_spack(settings["sampling_rate"], settings["bit_depth"], settings["padding"], output_dir, output_spack)
    input(colors.ctext("Press Enter...","orange"))
    print_info()

ConfigurationMenu = menu.Menu([
    menu.MenuItem("Bit Depth", int, "Enter bit depth : "),
    menu.MenuItem("Sampling Rate", int, "Enter a rate in hz : "),
    menu.MenuItem(".spack padding", int, "Enter a size in bytes : "),
    menu.MenuItem("Exit",menu.Exit)
],
set_and_store_settings, False)

Menu = menu.Menu([
    menu.MenuItem(colors.ctext("Convert files","blue"), callable, target=convert_files),
    menu.MenuItem(colors.ctext("Convert to .h","green"), callable, target=convert_to_h),
    menu.MenuItem(colors.ctext("Convert to .spack","yellow"), callable, target=convert_to_spack),
    menu.MenuItem(colors.ctext("Configure","orange"), menu.Menu, target=ConfigurationMenu),
    menu.MenuItem(colors.ctext("Exit","red"),menu.Exit)
],
None, False)

print("\033[?1049h", end="") ## enable alternate screen buffer
print_info()
fix_missing_files()
init_settings()
previous_settings = copy.deepcopy(settings)
menu.goToMenu(Menu)
while menu.render():
    try:
        fix_missing_files()
        file_utils.cleanup_stale_files(input_dir,output_dir)
    except KeyboardInterrupt: continue
print("\033[?1049l", end="") ## drop screen buffer
print("Thanks for using!")
