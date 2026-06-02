import nbformat as nbf
from pathlib import Path
import sys

def build_doctored_data(target_path):
    # Set the root to the folder you want to scan (e.g., TrainingDB)
    root = Path(target_path).expanduser().resolve()
    
    # 1. DISCOVERY: Find every subdirectory recursively
    for subdir in root.rglob('*'):
        if not subdir.is_dir():
            continue

        # 2. CATALOGING: Find all .py files in THIS folder
        py_files = sorted([f for f in subdir.glob('*.py') if f.name != "__init__.py"])
        
        # Only proceed if the folder actually has code
        if py_files:
            # 3. UNIQUE NAMING: Use the folder's path to create the filename
            # This ensures 'ciphers' and 'hashes' get different filenames
            rel_path = subdir.relative_to(root.parent)
            output_name = f"{'_'.join(rel_path.parts)}.ipynb"

            # 4. PROCESSING: Create the notebook and drop the data
            nb = nbf.v4.new_notebook()
            nb['cells'].append(nbf.v4.new_markdown_cell(f"# Subject: {subdir.name}\nSource: {subdir}"))
            
            for py_file in py_files:
                # Add the filename as a label
                nb['cells'].append(nbf.v4.new_markdown_cell(f"### File: {py_file.name}"))
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        code = f.read().strip()
                        if code:
                            nb['cells'].append(nbf.v4.new_code_cell(code))
                except Exception:
                    continue

            # 5. OUTPUT: Save the final doctored file
            with open(output_name, 'w', encoding='utf-8') as f:
                nbf.write(nb, f)
            print(f"CREATED: {output_name} ({len(py_files)} files)")

if __name__ == "__main__":
    # Usage: python3 sub-scan.py <folder>
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    build_doctored_data(target)

