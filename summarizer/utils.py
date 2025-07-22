from transformers import BartTokenizer, BartForConditionalGeneration
import re

def summarize_text(input_text):
    model_name = "facebook/bart-large-cnn"
    tokenizer = BartTokenizer.from_pretrained(model_name)
    model = BartForConditionalGeneration.from_pretrained(model_name)

    def split_into_chunks(text, max_words=900):
        # Basic sentence splitting by punctuation
        sentences = re.split(r'(?<=[.!?]) +', text)
        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            words = sentence.split()
            if current_length + len(words) > max_words:
                chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = len(words)
            else:
                current_chunk.append(sentence)
                current_length += len(words)

        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return chunks

    def generate_summary(text):
        inputs = tokenizer(text, max_length=1024, return_tensors="pt", truncation=True)
        summary_ids = model.generate(
            inputs["input_ids"],
            max_length=240,
            min_length=50,
            length_penalty=2.0,
            num_beams=4,
            early_stopping=True,
            no_repeat_ngram_size=3
        )
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        if not summary.endswith('.'):
            last_period = summary.rfind('.')
            if last_period != -1:
                summary = summary[:last_period + 1]
        return summary.strip()

    # If input is short, summarize directly
    word_count = len(input_text.split())
    if word_count <= 900:
        return generate_summary(input_text)

    # Otherwise, chunk and summarize
    chunks = split_into_chunks(input_text)
    partial_summaries = [generate_summary(chunk) for chunk in chunks]
    combined_summary = " ".join(partial_summaries)
    final_summary = generate_summary(combined_summary)

    return final_summary
