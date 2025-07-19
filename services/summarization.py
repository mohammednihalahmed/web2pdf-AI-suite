import logging
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM

class TextSummarizer:
    def __init__(self, model_name="sshleifer/distilbart-cnn-12-6", max_tokens=512, min_length=60, max_length=200):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        self.summarizer = pipeline("summarization", model=self.model, tokenizer=self.tokenizer)
        self.max_tokens = max_tokens
        self.min_length = min_length
        self.max_length = max_length

    def _chunk_text_by_tokens(self, text):
        tokens = self.tokenizer.encode(text, truncation=False)
        chunks = []

        for i in range(0, len(tokens), self.max_tokens):
            chunk_tokens = tokens[i:i + self.max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
            chunks.append(chunk_text)

        logging.debug(f"Token-based chunk count: {len(chunks)}")
        return chunks

    def summarize_large_text(self, text):
        chunks = self._chunk_text_by_tokens(text)
        summaries = []

        for chunk in chunks:
            summary = self.summarizer(
                chunk,
                max_length=self.max_length,
                min_length=self.min_length,
                do_sample=False
            )[0]['summary_text']
            summaries.append(summary)

        clean_summary = self._remove_redundancy(" ".join(summaries))
        return self._format_academic_answer(clean_summary)

    def _remove_redundancy(self, text):
        sentences = list(dict.fromkeys(text.split(". ")))  # removes exact repeated sentences
        return ". ".join(sentences)

    def _format_academic_answer(self, text):
        # Break into logical sections
        parts = text.split(". ")
        total = len(parts)

        intro = ". ".join(parts[:max(1, total // 5)])
        core = ". ".join(parts[max(1, total // 5):max(3, total // 2)])
        explanation = ". ".join(parts[max(3, total // 2):-2])
        conclusion = ". ".join(parts[-2:])

        return f"""### Introduction
{intro.strip()}.

### Key Concepts
{core.strip()}.

### Explanation
{explanation.strip()}.

### Conclusion
{conclusion.strip()}."""


