from pathlib import Path
import re
import shutil
import consolecolors as colors

def sanitize_filename(file_path):
    name = Path(file_path).stem
    
    name = re.sub(r'\W+', '_', name)
    
    if name[0].isdigit():
        name = "_" + name
        
    return name

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

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)

def ensure_file(path):
    file = Path(path)
    if not file.exists():
        file.touch(exist_ok=True)