from pathlib import Path


KB_PATH = Path("data/knowledge_base")


def read_knowledge_base():

    for file in KB_PATH.iterdir():

        if file.is_file():

            print("=" * 50)
            print("FILE:", file.name)
            print("=" * 50)

            text = file.read_text(
                encoding="utf-8"
            )

            print(text)


read_knowledge_base()
