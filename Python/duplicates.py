import os
import hashlib

def calculate_sha256(file_path, chunk_size=4096):
    """Calculates the SHA-256 hash of a file by reading it in chunks."""
    sha256_hash = hashlib.sha256()
    try:
        print("# Processing:", file_path)
        with open(file_path, "rb") as f:
            # Read the file in small chunks to protect memory usage
            for byte_block in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (PermissionError, FileNotFoundError) as e:
        # Handle files that can't be accessed/read
        return f"Error reading file: {e}"

def map_folder(root_folder):
    """Traverses a folder recursively and maps filenames to their SHA-256 hash."""
    file_hash_map = {}

    # os.walk handles the recursive aspect automatically
    for dirpath, dirnames, filenames in os.walk(root_folder):
        for filename in filenames:
            # Get the absolute or relative path to actually open the file
            full_path = os.path.join(dirpath, filename)

            # Calculate the hash
            file_hash = calculate_sha256(full_path)

            # Store in the dictionary
            # Note: If two different folders have a file with the same name,
            # using 'filename' as a key will overwrite the previous entry.
            # To fix this, you can change the key to 'full_path' instead.
            file_hash_map[full_path] = file_hash

    return file_hash_map

# --- Example Usage ---
def main():
    m = map_folder('/home/nikhil/Dropbox/Nikhil')
    r = {}
    files = list(m.keys())
    for r1 in files:
        for r2 in files:
            if r1 == r2:
                continue

            if m[r1] == m[r2]:
                k = min(r1, r2)
                v = max(r1, r2)
                r[k] = v
                print("# Duplicates:", r1, r2)
    print("# Count = " + str(len(r)))
    for k in r.keys():
        print("rm -rf \"" + k + "\"  \"" + r[k] + "\"")



main()
