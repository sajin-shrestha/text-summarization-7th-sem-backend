from transformers import BartTokenizer, BartForConditionalGeneration
import re
import torch
import unicodedata
from collections import Counter

# def summarize_text(input_text: str, model_path: str = "/Users/sajinshrestha/Developer/college/text_summarizer/custom-trained-modal-final"):
#     """
#     Summarizes text using a fine-tuned BART model.
#     - If text <= threshold → summarize directly.
#     - If longer → split into chunks, summarize each, then combine all summaries.
#     """
#         # Clean input to remove unwanted symbols / control characters
#     def clean_text(text: str) -> str:
#         # Normalize unicode (NFKC) to unify characters
#         text = unicodedata.normalize("NFKC", text)
#         # Remove non-printable/control characters
#         text = ''.join(ch for ch in text if ch.isprintable())
#         # Keep letters, numbers, common punctuation and whitespace; remove other unusual symbols
#         text = re.sub(r'[^0-9A-Za-z\u00C0-\u017F\s\.,;:!\?\(\)\[\]\'"%-—–\/&]+', '', text)
#         # Collapse multiple whitespace/newlines into single space
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text

#     # Clean the input before any processing
#     input_text = clean_text(input_text)

#     # Load model and tokenizer
#     tokenizer = BartTokenizer.from_pretrained(model_path)
#     model = BartForConditionalGeneration.from_pretrained(model_path)
#     model.eval()

#     device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
#     model.to(device)

#     def split_into_chunks(text: str, max_words: int = 300, overlap: int = 50):
#         """Split text into roughly max_words chunks with an overlap to preserve context."""
#         sentences = re.split(r'(?<=[.!?])\s+', text)
#         chunks, current_chunk, word_count = [], [], 0

#         for sentence in sentences:
#             words = sentence.split()
#             if word_count + len(words) > max_words:
#                 chunks.append(" ".join(current_chunk))
#                 # start new chunk with overlap
#                 overlap_slice = " ".join(current_chunk[-overlap:]) if overlap and len(current_chunk) >= overlap else ""
#                 current_chunk = [overlap_slice, sentence] if overlap_slice else [sentence]
#                 # recompute word_count for current_chunk
#                 word_count = sum(len(s.split()) for s in current_chunk)
#             else:
#                 current_chunk.append(sentence)
#                 word_count += len(words)

#         if current_chunk:
#             chunks.append(" ".join([s for s in current_chunk if s]))
#         return [c.strip() for c in chunks if c.strip()]
    
#     def extractive_key_sentences(text: str, top_n: int = 3):
#         """Simple frequency-based extractive selection to keep important facts."""
#         sentences = re.split(r'(?<=[.!?])\s+', text)
#         words = re.findall(r'\w+', text.lower())
#         # small stopword list to ignore common words
#         stopwords = {"the","and","is","in","to","of","a","for","on","with","that","this","it","as","are"}
#         freqs = Counter(w for w in words if w not in stopwords)
#         sentence_scores = []
#         for s in sentences:
#             s_words = re.findall(r'\w+', s.lower())
#             score = sum(freqs.get(w,0) for w in s_words)
#             sentence_scores.append((score, s))
#         top = [s for _, s in sorted(sentence_scores, reverse=True)[:max(1, min(top_n, len(sentences)))]]
#         return top

#     def generate_summary(texts, max_len: int = 240, min_len: int = 50, prompt_prefix: str = ""):
#         """
#         Accepts either a single string or a list of strings.
#         Uses batching when a list is provided and runs generation on device.
#         """
#         single = False
#         if isinstance(texts, str):
#             texts = [texts]
#             single = True

#         # optionally add a short prefix to give instruction context
#         inputs = tokenizer([prompt_prefix + t for t in texts], max_length=1024, truncation=True, padding=True, return_tensors="pt")
#         input_ids = inputs["input_ids"].to(device)
#         attention_mask = inputs.get("attention_mask").to(device)

#         with torch.no_grad():
#             summary_ids = model.generate(
#                 input_ids=input_ids,
#                 attention_mask=attention_mask,
#                 max_length=max_len,
#                 min_length=min_len,
#                 length_penalty=1.0,
#                 num_beams=6,
#                 early_stopping=True,
#                 no_repeat_ngram_size=3,
#             )

#         summaries = [tokenizer.decode(g, skip_special_tokens=True).strip() for g in summary_ids]
#         return summaries[0] if single else summaries

#     # Count total words
#     total_words = len(input_text.split())

#     # Direct summarization for short text
#     if total_words <= 300:
#         # add a soft instruction prefix (helps some finetuned models)
#         return generate_summary(input_text, max_len=280, min_len=60, prompt_prefix="Summarize: ")

#     # Chunk-based summarization for long text
#     chunks = split_into_chunks(input_text, max_words=300, overlap=50)
#     # batch generate summaries for chunks
#     chunk_summaries = generate_summary(chunks, max_len=220, min_len=50, prompt_prefix="Summarize: ")

#     # Combine all summaries
#     combined_summary = " ".join(chunk_summaries)

#     # Keep some extractive key sentences from original to preserve facts
#     keys = extractive_key_sentences(input_text, top_n=4)
#     combined_with_keys = combined_summary + " " + " ".join(keys)

#     # Final refinement pass: re-summarize combined text to improve coherence
#     refined = generate_summary(combined_with_keys, max_len=320, min_len=80, prompt_prefix="Summarize concisely: ")

#     return refined.strip()

def summarize_text(input_text: str, model_path: str = "/Users/sajinshrestha/Developer/college/text_summarizer/custom-trained-modal-final"):
    """
    Summarizes text using a fine-tuned BART model.
    - If text <= 420 chars → summarize directly.
    - If longer → split into chunks, summarize each, then combine summaries.
    """
    def clean_text(text: str) -> str:
        text = unicodedata.normalize("NFKC", text)
        text = ''.join(ch for ch in text if ch.isprintable())
        text = re.sub(r'[^0-9A-Za-z\u00C0-\u017F\s\.,;:!\?\(\)\[\]\'"%-—–\/&]+', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    input_text = clean_text(input_text)
    tokenizer = BartTokenizer.from_pretrained(model_path)
    model = BartForConditionalGeneration.from_pretrained(model_path)
    model.eval()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    def split_into_chunks(text: str, max_chars: int = 420, overlap_chars: int = 25):
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks, current_chunk, char_count = [], [], 0
        for sentence in sentences:
            sent_chars = len(sentence)
            if char_count + sent_chars > max_chars:
                joined_chunk = " ".join(current_chunk)
                chunks.append(joined_chunk)
                overlap_slice = joined_chunk[-overlap_chars:] if len(joined_chunk) >= overlap_chars else joined_chunk
                current_chunk = [overlap_slice + " " + sentence] if overlap_slice else [sentence]
                char_count = len(" ".join(current_chunk))
            else:
                current_chunk.append(sentence)
                char_count += sent_chars + 1 if current_chunk else sent_chars
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        return [c.strip() for c in chunks if c.strip()]

    def generate_summary(texts, max_len: int = 120, min_len: int = 25, prompt_prefix: str = ""):
        single = False
        if isinstance(texts, str):
            texts = [texts]
            single = True
        inputs = tokenizer([prompt_prefix + t for t in texts], max_length=420, truncation=True, padding=True, return_tensors="pt")
        input_ids = inputs["input_ids"].to(device)
        attention_mask = inputs.get("attention_mask").to(device)
        with torch.no_grad():
            summary_ids = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_length=max_len,
                min_length=min_len,
                length_penalty=1.0,
                num_beams=6,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
        summaries = [tokenizer.decode(g, skip_special_tokens=True).strip() for g in summary_ids]
        return summaries[0] if single else summaries

    total_chars = len(input_text)
    if total_chars <= 420:
        return generate_summary(input_text, max_len=120, min_len=25, prompt_prefix="Summarize: ")

    chunks = split_into_chunks(input_text, max_chars=420, overlap_chars=25)
    chunk_summaries = generate_summary(chunks, max_len=120, min_len=25, prompt_prefix="Summarize: ")
    combined_summary = " ".join(chunk_summaries)
    return combined_summary.strip()
