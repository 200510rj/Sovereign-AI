import ollama

image_path = input("Enter image path: ").strip()

response = ollama.chat(
    model="glm-ocr:q8_0",
    messages=[
        {
            "role": "user",
            "content": "Extract all visible text from this image. Preserve the structure as much as possible.",
            "images": [image_path],
        }
    ],
)

print("\n================ OCR RESULT ================\n")
print(response["message"]["content"])