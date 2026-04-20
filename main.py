import soundfont_generator_library as sfg
import consolecolors as colors
from pathlib import Path

Logo : str = (
r"""
 _______    ______   __       __          __       __   ______   __    __           ______  
/       \  /      \ /  \     /  |        /  \     /  | /      \ /  |  /  |         /      \ 
$$$$$$$  |/$$$$$$  |$$  \   /$$ |        $$  \   /$$ |/$$$$$$  |$$ |  $$ |        /$$$$$$  |
$$ |__$$ |$$ |  $$/ $$$  \ /$$$ | ______ $$$  \ /$$$ |$$ |  $$/ $$ |  $$ | ______ $$ |  $$/ 
$$    $$/ $$ |      $$$$  /$$$$ |/      |$$$$  /$$$$ |$$ |      $$ |  $$ |/      |$$ |      
$$$$$$$/  $$ |   __ $$ $$ $$/$$ |$$$$$$/ $$ $$ $$/$$ |$$ |   __ $$ |  $$ |$$$$$$/ $$ |   __ 
$$ |      $$ \__/  |$$ |$$$/ $$ |        $$ |$$$/ $$ |$$ \__/  |$$ \__$$ |        $$ \__/  |
$$ |      $$    $$/ $$ | $/  $$ |        $$ | $/  $$ |$$    $$/ $$    $$/         $$    $$/ 
$$/        $$$$$$/  $$/      $$/         $$/      $$/  $$$$$$/   $$$$$$/           $$$$$$/  
                                                                                            """)

def ask_mode():
    selected_option = input("Mode : ")
    if selected_option == "1" or selected_option == "2" or selected_option == "3":
        return int(selected_option)
    else:
        colors.cprint("[ERR] Please choose an abalivble option.","red")
        return ask_mode()

def ask_config(allow_default: bool):
    global configuration

    while True:
        # Ask for Bit Depth until valid
        while True:
            bit_depth_str = input("Bit Depth (8 or 16): ").strip()
            if bit_depth_str == "" and allow_default:
                break
            try:
                bit_depth = int(bit_depth_str)
                if bit_depth in (8, 16):
                    configuration[1] = bit_depth
                    break
                else:
                    colors.cprint("[ERR] Must use 8 or 16 bits!","red")
            except ValueError:
                colors.cprint("[ERR] Invalid input, enter an integer!","red")

        # Ask for Sample Rate
        while True:
            sample_rate_str = input("Sample Rate : ").strip()
            if sample_rate_str == "" and allow_default:
                break
            try:
                configuration[0] = int(sample_rate_str)
                break
            except ValueError:
                colors.cprint("[ERR] Invalid input, enter an integer!","red")

        # If we reach here, both are valid
        break

configuration = [0, 0, 0]  # sample_rate, bit_depth, mode
def handle_convert_configuration():
    cache = sfg.get_cache()
    print("\n")
    if cache is None:
        colors.cprint("[WARN] Old settings missing or corrupted, please input settings:","yellow")
        ask_config(False)
    else:
        configuration[0], configuration[1] = cache
        colors.cprint("\n[INFO] Past configuration found:", "blue")
        print(f"Sample Rate: {configuration[0]}")
        print(f"Bit Depth : {configuration[1]}\n")
        if not configuration[2] == 3:
            print("Set configuration (Leave empty to use past configuration):")
            ask_config(True)

colors.cprint(Logo,"bright_blue")
print("Pulse Code Modulation - MicroController - Converter - by Guillermo Beckers (Mejolov24 in github)")
print("Convert any file into an uncompressed format stored as .pcm via ffmpeg, useful for playing audio in microcontrollers with low processing power")

while True:
    sfg.fix_missing_files()
    print("Please select what you want to do:")
    print("\n")
    colors.cprint("1 : convert files","blue")
    colors.cprint("2 : parse sample into .h file ","green")
    #colors.cprint("3 : parse samples into .bin file","yellow")
    colors.cprint("3 : Exit","orange")
    print("\n")
    configuration[2] = ask_mode()
    
    match configuration[2]:
        case 1:
            handle_convert_configuration()
            sfg.convert_files(configuration[0], configuration[1])
            sfg.save_settings(configuration[0],configuration[1])
        case 2:
            if sfg.get_cache() == None:
                colors.cprint("[ERR] Missing or corrupted settings, convert again","red")
            else:
                configuration[0], configuration[1] = sfg.get_cache()
                sfg.parse_to_h_file(configuration[0], configuration[1])
        case 3:
            break

    print("\n")  
    input("Done! Press Enter to return to the menu...")
    print("\n")