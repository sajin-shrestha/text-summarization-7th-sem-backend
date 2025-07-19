from transformers import BartTokenizer, BartForConditionalGeneration

def summarize_text(input_text):
    model_name = "facebook/bart-base"
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)
    
    inputs = tokenizer(input_text, max_length=1024, return_tensors="pt", truncation=True)
    summary_ids = model.generate(
        inputs['input_ids'],
        max_length=120,
        min_length=30,
        length_penalty=2.5,
        num_beams=4,
        early_stopping=True
    )
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary