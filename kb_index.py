from pathlib import Path
from urllib.request import Request, urlopen
import json


KB_PATH = Path("data/knowledge_base")
INDEX_PATH = Path("data/kb_index.json")


def get_embedding(text: str):

    data = json.dumps({
        "model": "nomic-embed-text:latest",
        "input": text
    }).encode("utf-8")

    request = Request(
        "http://127.0.0.1:11434/api/embed",
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    with urlopen(request) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["embeddings"][0]


def load_chunks():

    chunks = []

    for file in KB_PATH.iterdir():

        if not file.is_file():
            continue

        try:
            import main
            text = main.extract_text(file)
        except Exception as err:
            print(f"Skipping {file.name}: {err}")
            continue

        if not text or not text.strip():
            continue

        # Split the document into logical sections.
        sections = [
            section.strip()
            for section in text.split("\n\n")
            if section.strip()
        ]

        current_chunk = ""

        for section in sections:

            # Keep numbered inspection requirements together.
            if (
                current_chunk
                and section[0].isdigit()
            ):
                current_chunk += "\n" + section

            elif (
                section.startswith("2.")
                or section.startswith("3.")
                or section.startswith("4.")
                or section.startswith("5.")
                or section.startswith("6.")
                or section.startswith("7.")
            ):
                current_chunk += "\n" + section

            else:

                if current_chunk:
                    chunks.append({
                        "source": file.name,
                        "text": current_chunk
                    })

                current_chunk = section

        if current_chunk:
            chunks.append({
                "source": file.name,
                "text": current_chunk
            })

    return chunks


def build_index():

    chunks = load_chunks()

    print(f"Found {len(chunks)} chunks.")

    indexed_chunks = []

    for number, chunk in enumerate(
        chunks,
        start=1
    ):

        print(
            f"Embedding chunk {number}/{len(chunks)}..."
        )

        embedding = get_embedding(
            chunk["text"]
        )

        indexed_chunks.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "embedding": embedding
        })

    INDEX_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    INDEX_PATH.write_text(
        json.dumps(
            indexed_chunks,
            indent=2
        ),
        encoding="utf-8"
    )

    print()
    print("Index created successfully!")
    print("Saved to:", INDEX_PATH)


if __name__ == "__main__":
    build_index()