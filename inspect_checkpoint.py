import torch
import json
import os

# Try to read and analyze format_version and other metadata
meta_dir = "best_model.pth/best_model"

files_info = {}
total_size = 0

for root, dirs, files in os.walk(meta_dir):
    for f in files:
        path = os.path.join(root, f)
        size = os.path.getsize(path)
        rel_path = os.path.relpath(path, meta_dir)
        files_info[rel_path] = {
            'size_bytes': size,
            'size_floats': size // 4
        }
        total_size += size
        print(f"{rel_path}: {size:,} bytes ({size//4:,} floats)")

print(f"\nTotal size: {total_size:,} bytes ({total_size//4:,} floats)")

# Try to understand the checkpoint format by reading metadata files
print("\n--- Metadata Files ---")
try:
    with open(f"{meta_dir}/version", "r") as f:
        print(f"version: {f.read().strip()}")
except:
    try:
        with open(f"{meta_dir}/version", "rb") as f:
            print(f"version (binary): {f.read()}")
    except Exception as e:
        print(f"version read error: {e}")

try:
    with open(f"{meta_dir}/.format_version", "r") as f:
        print(f".format_version: {f.read().strip()}")
except:
    with open(f"{meta_dir}/.format_version", "rb") as f:
        print(f".format_version (binary): {f.read()}")

try:
    with open(f"{meta_dir}/byteorder", "r") as f:
        print(f"byteorder: {f.read().strip()}")
except:
    with open(f"{meta_dir}/byteorder", "rb") as f:
        print(f"byteorder (binary): {f.read()}")

# Try to see if this is a standard format that torch can load
print("\n--- Trying torch.load on subdirectories ---")
try:
    cp = torch.load(f"{meta_dir}/best_model", map_location='cpu')
    print(f"Loaded best_model subdir: {type(cp)}")
except Exception as e:
    print(f"Can't load best_model subdir: {e}")

try:
    from torch.distributed.checkpoint import load
    from torch.distributed.checkpoint.filesystem import FileSystemReader
    
    print("\n--- Trying torch.distributed.checkpoint API ---")
    storage_reader = FileSystemReader(meta_dir)
    print(f"Created FileSystemReader: {storage_reader}")
except Exception as e:
    print(f"DCP API error: {e}")
