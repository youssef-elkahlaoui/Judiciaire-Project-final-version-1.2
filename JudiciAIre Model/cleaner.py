import json

input_file = "C:\\Users\\jozef\\OneDrive\\Desktop\\JudiciAIre\\JudiciAIre Model\\all_qa.jsonl"
output_file = "C:\\Users\\jozef\\OneDrive\\Desktop\\JudiciAIre\\JudiciAIre Model\\fichier_sans_source.jsonl"

with open(input_file, "r", encoding="utf-8") as infile, open(output_file, "w", encoding="utf-8") as outfile:
    for line in infile:
        data = json.loads(line)
        # Supprimer le texte à partir de "\n\nSource: CODE DE LA FAMILLE" dans le champ "output"
        if "output" in data:
            data["output"] = data["output"].replace("\n\nSource: CODE DE LA FAMILLE", "")
        outfile.write(json.dumps(data, ensure_ascii=False) + "\n")
