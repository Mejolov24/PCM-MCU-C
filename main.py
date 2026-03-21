import soundfont_generator_library as sfg
import os
import re

def ask_mode():
    selected_option = input("Mode : ")
    if selected_option == "1" or selected_option == "2" or selected_option == "3":
        return int(selected_option)
    else:
        print("Please choose an abalivble option.")
        return ask_mode()

def ask_files():
    print("Drag and drop one or more files into this window and press Enter:")

    user_input = input()

    # Grab all quoted paths (handles spaces)
    files = re.findall(r'"([^"]+)"', user_input)

    # Fallback: if only one file and unquoted
    if not files and user_input.strip():
        files = [user_input.strip()]

    # Clean paths
    clean_files = []
    for f in files:
        f = f.strip().rstrip('&')  # remove trailing spaces and '&'
        f = os.path.abspath(f)     # full path
        clean_files.append(f)

    files = clean_files
    
    if not files:
        print("No files were dropped onto the script.")
        return ask_files()
    else:
        return files

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
                    print("Must use 8 or 16 bits!")
            except ValueError:
                print("Invalid input, enter an integer!")

        # Ask for Sample Rate
        while True:
            sample_rate_str = input("Sample Rate : ").strip()
            if sample_rate_str == "" and allow_default:
                break
            try:
                configuration[0] = int(sample_rate_str)
                break
            except ValueError:
                print("Invalid input, enter an integer!")

        # If we reach here, both are valid
        break






sfg.check_missing_files()
print(r"""
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


print("Pulse Code Modulation - MicroController - Converter - by Guillermo Beckers (Mejolov24 in github)")
print("Convert any file into an uncompressed format stored as .raw via ffmpeg, useful for playing audio in microcontrollers with low processing power")
print("Please select what you want to do:")
print("""
1 : convert files
2 : convert files and parse into h file
3 : parse existing files to h file
 """)

configuration = [0, 0, 0]  # sample_rate, bit_depth, mode
configuration[2] = ask_mode()

cache = sfg.get_cache()
if cache is None:
    print("Cache missing or corrupted, please input settings:")
    ask_config(False)
else:
    configuration[0], configuration[1] = cache
    print(f"""
    Past configuration found:
    Sample Rate: {configuration[0]}
    Bit Depth : {configuration[1]}
    """)
    if not configuration[2] == 3:
        print("Set configuration (Leave empty to use past configuration):")
        ask_config(True)
sfg.save_cache(configuration[0],configuration[1])


match configuration[2]:
    case 1:
        files = ask_files()
        sfg.convert_files(files, configuration[0], configuration[1])
    case 2:
        files = ask_files()
        sfg.convert_files(files, configuration[0], configuration[1])
        sfg.parse_to_h_file(configuration[0], configuration[1])
    case 3:
        sfg.parse_to_h_file(configuration[0], configuration[1])


print("\n")
        
input("Press Enter to exit...")