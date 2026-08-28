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
sf2_intermedium_output = input_dir / "sf2"
sf2_final_output = output_dir / "sf2"
settings = {}
settings_changed = False

DEFAULT_SETTINGS = {
    "bit_depth" : 16,
    "sampling_rate": 22050,
    "padding": 16,
    "base_note" : 69,
    "base_note_enabled" : False
}

def fix_missing_files():
    file_utils.ensure_dir(input_dir)
    file_utils.ensure_dir(output_dir)
    file_utils.ensure_dir(sf2_intermedium_output)
    file_utils.ensure_dir(sf2_final_output)
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
    colors.cprint(logo.logo,"blue")
    print("Pulse Code Modulation - MicroController - Converter - by Guillermo Beckers (Mejolov24 in github)")
    print("Convert any file into an uncompressed format stored as .pcm via ffmpeg, useful for playing audio in microcontrollers with low processing power")

def set_and_store_settings(index, value = None):
    global settings_changed, settings
    settings_changed = True
    match index:
        case 0:
            settings["bit_depth"] = value
        case 1:
            settings["sampling_rate"] = value
        case 2:
            settings["padding"] = value
        case 3:
            settings["base_note"] = value
        case 4:
            settings["base_note_enabled"] = value
    sync_json_settings()
    init_settings()
    print_info()

def convert_files(auto_skip : bool = False):
    global settings_changed
    if settings_changed:
        file_utils.clear_directory(output_dir)
        colors.cprint("\n[WARN] Settings changed, deleting /output...\n", "yellow")
    else:
         colors.cprint("\n[INFO] No settings changed, skipping existing files...\n", "blue")

    audio_utils.convert_files(settings["sampling_rate"], settings["bit_depth"], settings_changed,input_dir,output_dir)
    if not auto_skip :
        input(colors.ctext("Press Enter...","orange"))
        print_info()
    settings_changed = False

def convert_to_h():
    audio_utils.parse_to_h_file(settings["sampling_rate"], settings["bit_depth"],output_dir, output_h)
    input(colors.ctext("Press Enter...","orange"))
    print_info()

def convert_to_spack():
    ##process /output/ but not /output/sf2
    file_count = sum(1 for item in output_dir.rglob("*.spack") if item.is_file())
    output_spack = output_dir / f"{file_count}_{settings["bit_depth"]}_bits_{settings["sampling_rate"]}_hz.spack"
    audio_utils.parse_to_spack(settings["sampling_rate"], settings["bit_depth"], settings["padding"], output_dir, output_spack)

    ##process /output/sf2 separately and make an individual .spack per folder
    for sub_dir in sf2_final_output.glob("*"):
        if not sub_dir.is_dir(): continue
        file_count = sum(1 for item in output_dir.rglob("*.spack") if item.is_file())
        output_spack = sf2_final_output / f"{file_count}_{sub_dir.name}_{settings["bit_depth"]}_bits_{settings["sampling_rate"]}_hz.spack"
        spack_input_path = sf2_final_output / sub_dir.name

        audio_utils.parse_to_spack(settings["sampling_rate"], settings["bit_depth"], settings["padding"], spack_input_path, output_spack)
    input(colors.ctext("Press Enter...","orange"))
    print_info()

def convert_Sf2():
    while True:
        raw_path = menu.ask_value(str, "Enter Path : ")
        if raw_path is KeyboardInterrupt: return
        file_path = Path(raw_path)
        output_path = sf2_intermedium_output / file_path.name

        if file_path.is_file():
            audio_utils.sf2_to_wav(file_path,output_path,settings["base_note_enabled"],settings["base_note"])
            convert_files(True)

            input(colors.ctext("Press Enter...","orange"))
            print_info()
            break
        else:
            colors.cprint("[ERR] File doesn't exist or isn't a valid file!", "red")

ConfigurationMenu = menu.Menu([
    menu.MenuItem("Bit Depth", int, "Enter bit depth : "),
    menu.MenuItem("Sampling Rate", int, "Enter a rate in hz : "),
    menu.MenuItem(".spack padding", int, "Enter a size in bytes : "),
    menu.MenuItem(".sf2 base note", int, "Enter a base note : "),
    menu.MenuItem(".sf2 base note resample enabled", bool, "True or False : "),
    menu.MenuItem("Exit",menu.Exit)
],
set_and_store_settings, False)

Menu = menu.Menu([
    menu.MenuItem(colors.ctext("Convert to .pcm","bright_blue"), callable, target=convert_files),
    menu.MenuItem(colors.ctext("Convert .sf2 to .pcm","blue"), callable, target=convert_Sf2),
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
