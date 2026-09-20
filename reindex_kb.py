import json
from pathlib import Path
import re
import sys

# Ensure local directory is in path
sys.path.insert(0, str(Path(__file__).parent))

import main

def fix_filenames_and_index():
    kb_dir = Path("data/knowledge_base")
    if not kb_dir.exists():
        print("Knowledge base directory missing.")
        return

    # 1. Clean up trailing space in filenames
    for file in list(kb_dir.iterdir()):
        if file.is_file():
            cleaned_name = file.name.strip()
            # Remove spaces right before extension like "Het_Patel_Resume .pdf"
            cleaned_name = re.sub(r'\s+(\.[a-zA-Z0-9]+)$', r'\1', cleaned_name)
            if cleaned_name != file.name:
                new_path = kb_dir / cleaned_name
                file.rename(new_path)
                print(f"Renamed '{file.name}' -> '{cleaned_name}'")

    print("\n--- Indexing Knowledge Base Files ---")
    indexed_count = 0
    for file in kb_dir.iterdir():
        if file.is_file():
            print(f"Processing: {file.name}")
            try:
                text = main.extract_text(file)
                if text and text.strip():
                    chunks_created = main.index_document(file.name, text)
                    print(f"  Successfully indexed {file.name}: {chunks_created} chunks.")
                    indexed_count += 1
                else:
                    print(f"  Warning: No text extracted from {file.name}")
            except Exception as e:
                print(f"  Error processing {file.name}: {e}")

    print(f"\nCompleted re-indexing {indexed_count} files into data/kb_index.json.")

if __name__ == "__main__":
    fix_filenames_and_index()
