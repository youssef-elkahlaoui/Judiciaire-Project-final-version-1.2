import google.generativeai as genai
import json
import os
import time
import re
from PyPDF2 import PdfReader
import logging
import sys

# Setup logging
log_filename = "processing.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, mode='w', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)  # Optional: to also print to console
    ]
)

# Redirect all prints to logging
print = lambda *args, **kwargs: logging.info(' '.join(map(str, args)))

# --- CONFIGURATION ---
API_KEYS = [
    "AIzaSyCZOEjTahVmjnPUY9BacgC_DHZFWT08-Bs",
    "AIzaSyAZZGIahdxiL8TcyqC27DDWiWm4MxzyFqY",
    "AIzaSyDG64AcEIaWkTgTJfdd1mL_5y1d-TzaYTw",
    "AIzaSyC_Fb2AvDz-OS7CZj-UpOYWtWhI4rAZGow",
    # Add more keys as needed
]
PDF_DIR = "code"          # Parent directory containing subdirectories with PDF files
OUTPUT_DIR = "outputs_ar"     # Directory to save JSONL output files
MODEL_NAME = "models/gemini-2.0-flash"
PAIRS_PER_CHUNK = 3
CHUNKS_PER_CALL = 3
SLEEP_AFTER = 10
SLEEP_SECONDS = 60

# --- Initialize Gemini ---
current_key_index = 0

def configure_gemini():
    genai.configure(api_key=API_KEYS[current_key_index])

configure_gemini()
model = genai.GenerativeModel(MODEL_NAME)

# --- PDF Text Extraction ---
def extract_text_chunks_from_pdf(file_path):
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            full_text = "\n".join(page.extract_text() or '' for page in reader.pages)
            chunks = re.split(r'(Article\s+\d+[\s\S]*?)(?=Article\s+\d+|$)', full_text)
            return [chunk.strip() for chunk in chunks if chunk.strip()]
    except Exception as e:
        print(f"[Error] PDF extraction failed: {e}")
        return []

# --- Detect source title from content ---
def detect_source_name(text_chunk):
    try:
        prompt = f"""
Lis ce texte juridique marocain et donne uniquement le nom exact du document juridique ou code auquel il appartient.
Par exemple : "Code de la Famille (Moudwana), ETAT CIVIL ...".

Texte :
{text_chunk}
"""
        response = model.generate_content(prompt)
        return response.text.strip().strip('"')
    except Exception as e:
        print(f"[Error] Failed to detect source name: {e}")
        return "Source juridique"

# --- Generate QA pairs using Gemini ---
# def generate_qa_pairs(text, num_pairs, source):
#     prompt = f"""
# Tu es un assistant juridique expert en droit marocain.
# Lis le texte suivant, et génère {num_pairs} paires question-réponse pertinentes.
# ✅ Chaque réponse doit être claire, utile, pédagogique et suffisamment longue avec détails et exemples si possible.
# ✅ Tu peux mentionner le numéro d'article et le nom exact de la loi si c’est utile.
# ✅ N’hésite pas à proposer des interprétations, exemples, suggestions concrètes ou cas d’usage.

# Termine chaque réponse par : "Source : {source}"

# Format attendu :
# Q: ...
# A: ...
# Q: ...
# A: ...

# Texte :
# {text}
# """
#     response = model.generate_content(prompt)
#     return parse_qa_pairs(response.text.strip(), source)


# def generate_qa_pairs(text, num_pairs, source):
#     prompt = f"""
# Tu es un assistant juridique expert en droit marocain.

# Lis attentivement le texte suivant et génère {num_pairs} paires question-réponse de haute qualité.

# 🎯 Chaque **question** doit être formulée comme une **situation problématique concrète**, par exemple :
# - "Une femme a deux enfants, quels sont ses droits en cas de divorce ?"
# - "Un salarié licencié sans préavis, que peut-il faire ?"
# - "Comment hérite un enfant naturel selon le Code de la Famille ?"

# 🧠 Chaque **réponse** doit être :
# - Longue, claire et pédagogique
# - Bien structurée avec des explications détaillées
# - Peut mentionner le numéro d'article et le nom exact de la loi
# - Peut proposer des cas pratiques, suggestions ou recommandations

# Chaque réponse doit se terminer par :  
# "Source : {source}"

# Format attendu :
# Q: ...
# A: ...
# Q: ...
# A: ...

# Texte :
# {text}
# """
#     response = model.generate_content(prompt)
#     return parse_qa_pairs(response.text.strip(), source)

def generate_qa_pairs(text, num_pairs, source):
    prompt = f"""
Tu es un assistant juridique spécialisé en droit marocain.

Lis attentivement le texte juridique suivant (en français), puis génère {num_pairs} paires question-réponse de haute qualité rédigées en **arabe classique**.

🎯 Chaque **question** (سؤال) doit être formulée comme une **situation réelle et problématique**, par exemple :
- "امرأة لديها طفلان، ما هي حقوقها في حالة الطلاق؟"
- "عامل تم طرده دون إشعار مسبق، ما هي الإجراءات التي يمكنه اتخاذها؟"
- "كيف يتم توزيع الإرث في حالة وجود أبناء من زواج غير موثق؟"

🧠 Chaque **réponse** (جواب) doit :
- être longue, claire, pédagogique
- inclure des explications détaillées, des exemples si nécessaire
- mentionner les articles de loi et les noms des textes légaux si pertinents
- inclure des suggestions ou recommandations utiles

📌 Chaque réponse doit se terminer par :
"المصدر: {source}"

🗂 Format strictement attendu :
س: ...
ج: ...
س: ...
ج: ...

Voici le texte à analyser :
{text}
"""
    response = model.generate_content(prompt)
    return parse_qa_pairs(response.text.strip(), source)

# --- Retry wrapper with key rotation ---
def safe_generate_qa_pairs(text, num_pairs, source):
    global current_key_index, model
    retries = 5
    delay = 60
    for _ in range(retries):
        try:
            return generate_qa_pairs(text, num_pairs, source)
        except Exception as e:
            err_str = str(e).lower()
            if "quota" in err_str or "resourceexhausted" in err_str:
                print(f"Quota exceeded for key index {current_key_index}, switching API key...")
                current_key_index += 1
                if current_key_index >= len(API_KEYS):
                    print(f"All API keys exhausted. Waiting {delay}s before retrying...")
                    time.sleep(delay)
                    delay *= 2
                    current_key_index = 0
                configure_gemini()
                model = genai.GenerativeModel(MODEL_NAME)
            else:
                print(f"Error: {e}")
                break
    return []

# --- Parse QA pairs ---
def parse_qa_pairs(text, source):
    qa_pairs = []
    lines = text.split("\n")
    current_q = None
    for line in lines:
        if line.startswith("Q:"):
            current_q = line.replace("Q:", "").strip()
        elif line.startswith("A:") and current_q:
            answer = line.replace("A:", "").strip()
            if not answer.endswith(f"Source: {source}"):
                answer += f"\n\nSource: {source}"
            qa_pairs.append({"input": current_q, "output": answer})
            current_q = None
    return qa_pairs

# --- Append to JSONL ---
def append_to_jsonl(file_path, data):
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')
    except Exception as e:
        print(f"[Error] JSONL write failed: {e}")

# --- Merge all JSONL files ---
def merge_all_jsonl_outputs(output_dir, merged_filename="qa_pairs.jsonl"):
    merged_path = os.path.join(output_dir, merged_filename)
    with open(merged_path, 'w', encoding='utf-8') as _:
        pass
    total_entries = 0
    for root, _, files in os.walk(output_dir):
        for file in files:
            if file.endswith(".jsonl") and file != merged_filename:
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f_in, open(merged_path, 'a', encoding='utf-8') as f_out:
                    lines = f_in.readlines()
                    f_out.writelines(lines)
                    total_entries += len(lines)
                print(f"📎 Merged {len(lines)} entries from {file}")
    print(f"\n📦 All Q&A pairs merged into '{merged_path}' ({total_entries} total entries).")

# --- Main function ---
def main():
    if not API_KEYS:
        print("[Error] No API keys configured.")
        return
    if not os.path.exists(PDF_DIR):
        print(f"[Error] PDF directory '{PDF_DIR}' not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    grand_total_pairs = 0
    for subdir, _, files in os.walk(PDF_DIR):
        sub_total_pairs = 0
        for file in files:
            if not file.lower().endswith('.pdf'):
                continue
            pdf_path = os.path.join(subdir, file)
            print(f"\n🚀 Starting processing file: {file}")

            chunks = extract_text_chunks_from_pdf(pdf_path)
            print(f"📦 Total chunks: {len(chunks)}")
            if not chunks:
                print(f"[Warning] No valid text chunks in {file}. Skipping.")
                continue

            source = detect_source_name(chunks[0])
            print(f"📌 Source: {source}")

            output_file = os.path.join(OUTPUT_DIR, f"{os.path.splitext(file)[0]}.jsonl")
            open(output_file, 'w', encoding='utf-8').close()

            total_pairs = 0
            for i in range(0, len(chunks), CHUNKS_PER_CALL):
                batch = chunks[i:i + CHUNKS_PER_CALL]
                combined_text = "\n\n".join(batch)
                num_pairs = PAIRS_PER_CHUNK * len(batch)

                print(f"📄 Processing chunks {i + 1} to {i + len(batch)}...")
                qa_pairs = safe_generate_qa_pairs(combined_text, num_pairs, source)
                append_to_jsonl(output_file, qa_pairs)
                total_pairs += len(qa_pairs)

                if (i // CHUNKS_PER_CALL + 1) % SLEEP_AFTER == 0:
                    print(f"⏳ Sleeping {SLEEP_SECONDS}s to avoid rate limits...")
                    time.sleep(SLEEP_SECONDS)

            print(f"✅ Done: {total_pairs} Q&A pairs written for {file}")
            sub_total_pairs += total_pairs

        print(f"📁 Finished directory '{subdir}': {sub_total_pairs} Q&A pairs")
        grand_total_pairs += sub_total_pairs

    print(f"\n🎯 Total Q&A pairs across all directories: {grand_total_pairs}")
    merge_all_jsonl_outputs(OUTPUT_DIR)

if __name__ == "__main__":
    main()