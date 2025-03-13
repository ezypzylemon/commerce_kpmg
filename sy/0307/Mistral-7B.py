from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

from transformers import AutoModelForCausalLM, AutoTokenizer

# ✅ 모델 및 토크나이저 로드 (토큰 포함)
model_name = "mistralai/Mistral-7B-Instruct-v0.1"
tokenizer = AutoTokenizer.from_pretrained(model_name, token=hf_token)
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto", token=hf_token)

def map_fields_with_mistral(text):
    """OCR 결과에서 필드값을 자동 분류하는 LLM 함수"""
    prompt = f"""
    Extract and categorize the following fields from the given text:

    SEASON, PICTURE, BRAND, STYLE, BO, ITEM, 소재, 품목코드, fabric, color(original), color code, description, size, 사이즈별 수량, 통화, qty, unit price, amount.

    Input text:
    {text}

    Output JSON format:
    {{
        "SEASON": "...",
        "PICTURE": "...",
        "BRAND": "...",
        "STYLE": "...",
        "BO": "...",
        "ITEM": "...",
        "소재": "...",
        "품목코드": "...",
        "fabric": "...",
        "color(original)": "...",
        "color code": "...",
        "description": "...",
        "size": "...",
        "사이즈별 수량": "...",
        "통화": "...",
        "qty": "...",
        "unit price": "...",
        "amount": "..."
    }}
    """

    inputs = tokenizer(prompt, return_tensors="pt").to("cuda")
    outputs = model.generate(**inputs, max_length=512)
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    
    return response
