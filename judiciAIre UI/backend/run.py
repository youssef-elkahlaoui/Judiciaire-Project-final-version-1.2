import torch
from unsloth import FastLanguageModel
from transformers import AutoTokenizer

model_name = "ANASEEE/JudicIAreLLAMA"

try:
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name = model_name,
        max_seq_length = 2048,
        dtype = torch.float16,
        load_in_4bit = True,
    )

    FastLanguageModel.for_inference(model)  # Required for Unsloth models
    print("✅ Model and tokenizer loaded successfully")

except Exception as e:
    print(f"❌ Failed to load model or tokenizer: {str(e)}")
    exit(1)

    
prompt = """### Instruction :
أنت مساعد قانوني متخصص في القانون المغربي.
الجواب خاصو يكون واضح، قصير، وبالدارجة المغربية، ومرتكز فقط على القانون.

### Question :
شنو هي عقوبة السرقة فالقانون المغربي؟

### Réponse :
"""

inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    temperature=0.7,
    top_p=0.9,
    do_sample=True,
    eos_token_id=tokenizer.eos_token_id,
)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print("📤 Response:\n", response)
