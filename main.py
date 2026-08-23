import soundfont_generator_library as sfg
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

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_file(path):
    file = Path(path)
    if not file.exists():
        file.touch(exist_ok=True)

def fix_missing_files():
    ensure_dir(input_dir)
    ensure_dir(output_dir)
    ensure_file(output_h)
    ensure_file(settings_path)


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
    ##print("\033[H\033[2J")
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

def clear_directory(dir_path):
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        shutil.rmtree(path)  
    path.mkdir(parents=True, exist_ok=True)

def cleanup_stale_files(source_dir, output_dir):
    for item in sorted(output_dir.rglob("*"), reverse=True):
        if item.name in ["output.h", "output.spack"]:
            continue
        rel_path = item.relative_to(output_dir)
        source_item = source_dir / rel_path

        if item.is_file() and item.suffix == ".pcm":
            parent_dir = source_dir / rel_path.parent
            stem = item.stem
            matching_sources = False
            if parent_dir.exists():
                for src_file in parent_dir.iterdir():
                    if src_file.stem == stem:
                        matching_sources = True
                        break
            if not matching_sources:
                item.unlink()
                colors.cprint(f"[WARN] Removing stale file: {item.name}\nThis is caused by deleting, removing or renaming a file in /input, if this wasnt intended, convert files again.", "yellow")
        
        elif item.is_dir():
            if not source_item.exists():
                shutil.rmtree(item)
                colors.cprint(f"[WARN] Removing stale folder: {item.name}\nThis is caused by deleting, removing or renaming a folder in /input, if this wasnt intended, convert files again.", "yellow")

def convert_files():
    new_settings : bool = (previous_settings != settings)

    if new_settings:
        clear_directory(output_dir)
        colors.cprint("\n[WARN] Settings changed, deleting /output...\n", "yellow")
    else:
         colors.cprint("\n[INFO] No settings changed, skipping existing files...\n", "blue")

    sfg.convert_files(settings["sampling_rate"], settings["bit_depth"], new_settings)

def convert_to_h():
    sfg.parse_to_h_file(settings["sampling_rate"], settings["bit_depth"])

def convert_to_spack():
    sfg.parse_to_spack(settings["sampling_rate"], settings["bit_depth"], settings["padding"])

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
    menu.MenuItem("Configure", menu.Menu, target=ConfigurationMenu),
    menu.MenuItem(colors.ctext("Exit","orange"),menu.Exit)
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
        print_info()
        cleanup_stale_files(input_dir,output_dir)
    except KeyboardInterrupt: continue
print("\033[?1049l", end="") ## drop screen buffer
print("Thanks for using!")
