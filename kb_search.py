from pathlib import Path
from urllib.request import Request, urlopen
import json
import math


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


def cosine_similarity(a, b):

    dot_product = sum(
        x * y for x, y in zip(a, b)
    )

    magnitude_a = math.sqrt(
        sum(x * x for x in a)
    )

    magnitude_b = math.sqrt(
        sum(x * x for x in b)
    )

    if magnitude_a == 0 or magnitude_b == 0:
        return 0

    return dot_product / (
        magnitude_a * magnitude_b
    )


def load_index():

    if not INDEX_PATH.exists():

        raise FileNotFoundError(
            "Knowledge base index not found. "
            "Run: python kb_index.py"
        )

    return json.loads(
        INDEX_PATH.read_text(
            encoding="utf-8"
        )
    )


def search(query, top_k=3):

    chunks = load_index()

    query_embedding = get_embedding(query)

    results = []

    for chunk in chunks:

        score = cosine_similarity(
            query_embedding,
            chunk["embedding"]
        )

        results.append({
            "source": chunk["source"],
            "text": chunk["text"],
            "score": score
        })

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:top_k]


if __name__ == "__main__":

    query = input(
        "Ask your knowledge base: "
    )

    results = search(query)

    print("\nTOP RESULTS\n")

    for result in results:

        print("=" * 60)

        print(
            f"Score: {result['score']:.4f}"
        )

        print(
            f"Source: {result['source']}"
        )

        print()

        print(result["text"])