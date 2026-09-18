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


def search(query, top_k=5):

    chunks = json.loads(
        INDEX_PATH.read_text(
            encoding="utf-8"
        )
    )

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


def ask_qwen(question, context):

    prompt = f"""
You are a local enterprise AI assistant.

Answer the user's question using ONLY the provided
knowledge-base context.

If the context does not contain enough information,
say that the information is not available in the
knowledge base.

Do not invent procedures, measurements, requirements,
or facts.

KNOWLEDGE BASE CONTEXT:
{context}

USER QUESTION:
{question}

Give a concise answer and mention the source file.
"""

    data = json.dumps({
        "model": "qwen3.5:4b",
        "prompt": prompt,
        "stream": False,
        "think": False,
        "options": {
            "num_predict": 256
        }
    }).encode("utf-8")

    request = Request(
        "http://127.0.0.1:11434/api/generate",
        data=data,
        headers={
            "Content-Type": "application/json"
        }
    )

    with urlopen(request) as response:
        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["response"]


if __name__ == "__main__":

    question = input(
        "Ask your knowledge base: "
    )

    results = search(question)

    context_parts = []

    for result in results:

        context_parts.append(
            f"[Source: {result['source']}]\n"
            f"{result['text']}"
        )

    context = "\n\n".join(context_parts)

    print("\nGenerating grounded answer...\n")

    answer = ask_qwen(
        question,
        context
    )

    print("=" * 60)
    print("ANSWER")
    print("=" * 60)
    print(answer)

    print("\n")
    print("RETRIEVED SOURCES")
    print("=" * 60)

    for result in results:

        print(
            f"{result['source']} "
            f"(score: {result['score']:.4f})"
        )