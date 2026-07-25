from pathlib import Path

def add_header_to_md_files(root_folder: str):
    folder = Path(root_folder)
    
    # Recursively find all files ending in .md (case-insensitive)
    for file_path in folder.rglob("*.[mM][dD]"):
        if file_path.is_file():
            # Extract filename without the .md extension
            header = f"# {file_path.stem}\n\n"
            
            try:
                # Read original contents
                content = file_path.read_text(encoding="utf-8")
                
                # Check if header is already present to prevent duplicate runs
                if content.startswith(header.strip()):
                    print(f"Skipped (Header already present): {file_path}")
                    continue
                
                # Write back with the header prepended
                file_path.write_text(header + content, encoding="utf-8")
                print(f"Updated: {file_path}")
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    # Replace with your target directory path
    target_dir = "/Users/nikhil/Notes"
    add_header_to_md_files(target_dir)

