from urllib.request import Request, urlopen
import json


text = "What are the inspection requirements for a centrifugal pump?"


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


embedding = result["embeddings"][0]


print("Embedding created successfully!")
print("Number of values:", len(embedding))
print("First 5 values:", embedding[:5])