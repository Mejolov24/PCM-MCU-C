import soundfont_generator_library as sfg
import os
import re

def ask_mode():
    selected_option = input("Mode : ")
    if selected_option == "1" or selected_option == "2" or selected_option == "3":
        return int(selected_option)
    else:
        print("Please choose an abalivble option.")
        ask_mode()

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


print("Pulse Code Modulation - MicroController - Converter")
print("Convert any file into an uncompressed format stored as .raw via ffmpeg, useful for playing audio in microcontrollers with low processing power")
print("Please select what you want to do:")
print("""
1 : convert files
2 : convert files and parse into h file
3 : parse existing files to h file
 """)

configuration = [0,0,0]
configuration[2] = ask_mode()

print("\n")
print("Past configuration :")


configuration[0] = sfg.get_cache()[0]
configuration[1] = sfg.get_cache()[1]

print(f"""
Sample Rate : {configuration[0]}
Bit_Depth : {configuration[1]}
 """)

print("Set configuration (Leave empty to use past configuration) : ")

requested_config = [0,0]
requested_config[0] = input("Sample Rate :")
requested_config[1] = input("Bith Depth : ")

for i in range(len(requested_config)):
    config = requested_config[i]
    if config != "":
        configuration[i] = int(config)
        

match configuration[2]:
    case 1:
        files = ask_files()
        sfg.convert_files(files,configuration[0],configuration[1])
    case 2: 
        files = ask_files()
        sfg.convert_files(files,configuration[0],configuration[1])
        sfg.parse_to_h_file(configuration[0],configuration[1])
    case 3:
        sfg.parse_to_h_file(configuration[0],configuration[1])
print("\n")
        
input("Press Enter to exit...")