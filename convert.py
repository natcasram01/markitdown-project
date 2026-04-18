from markitdown import MarkItDown
import os

md = MarkItDown()

INPUT_DIR = "input"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filename in os.listdir(INPUT_DIR):
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename + ".md")

    print(f"Convirtiendo: {filename}...")
    result = md.convert(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result.text_content)

    print(f"✅ Guardado en: {output_path}")