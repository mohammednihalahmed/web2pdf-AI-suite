from colbert.searcher import Searcher
searcher = Searcher(index_path="colbert_index")
results = searcher.search("What is TCP congestion control?", k=5)
print(results)







### no summary working fine until retrieval process
import os
import re
import signal
import logging
from ctransformers import AutoModelForCausalLM
from colbert_retriever import ColBERTRetriever

logging.basicConfig(level=logging.DEBUG)

MODEL_PATH = "../models/mistral/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

print("⏳ Loading Mistral 7B model...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="mistral",
        gpu_layers=15,
        context_length=4096
    )
    print("✅ Model loaded successfully on GPU!")
except Exception as e:
    print(f"⚠️ GPU ran out of memory, switching to CPU. Error: {e}")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="mistral",
        gpu_layers=0,
        context_length=2048
    )

retriever = ColBERTRetriever()

MARKS_TOKENS = {
    "10M": 768,
    "6M": 512,
    "4M": 384
}

def is_pdf_related_query(query):
    query_lower = query.lower()
    pdf_keywords = ["explain", "summary", "describe", "what is", "how does", "10m", "6m", "4m"]
    return any(keyword in query_lower for keyword in pdf_keywords)

def determine_response_type(query):
    query_lower = query.lower()

    marks_match = re.search(r"\b(10\s?marks?|10m|six\s?marks?|6m|four\s?marks?|4m)\b", query_lower)
    if marks_match:
        if "10" in marks_match.group():
            return "10M", MARKS_TOKENS["10M"]
        elif "6" in marks_match.group():
            return "6M", MARKS_TOKENS["6M"]
        else:
            return "4M", MARKS_TOKENS["4M"]

    if "explain" in query_lower or "step by step" in query_lower:
        return "explanation", MARKS_TOKENS["6M"]

    if "summary" in query_lower or "summarize" in query_lower:
        return "summary", MARKS_TOKENS["4M"]

    return "default", MARKS_TOKENS["4M"]

def timeout_handler(signum, frame):
    raise TimeoutError("Response generation took too long")

def generate_response(query):
    if is_pdf_related_query(query):
        response_type, max_response_tokens = determine_response_type(query)

        try:
            pdf_context_chunks = retriever.search(query, top_k=3)
            pdf_context = " ".join(pdf_context_chunks) if pdf_context_chunks else ""
            logging.debug(f"PDF Context: {pdf_context}")
        except Exception as e:
            logging.error(f"ColBERT retrieval failed: {e}")
            pdf_context = ""

        if pdf_context:
            prompt = f"### Instruction: Provide a {response_type} response. Use the provided context if available.\n\n### Question:\n{query}\n\n### Context:\n{pdf_context}\n\n### Response:"
        else:
            prompt = f"### Instruction: Answer concisely in about {max_response_tokens} tokens.\n\n### Question:\n{query}\n\n### Response:"
    else:
        prompt = f"### Instruction: Respond conversationally.\n\n### Query:\n{query}\n\n### Response:"

    input_tokens = model.tokenize(prompt)
    if len(input_tokens) > 1024:
        input_tokens = input_tokens[:1024]
        prompt = model.detokenize(input_tokens)

    max_allowed_tokens = 2048 - len(input_tokens)
    final_max_tokens = min(max_response_tokens, max_allowed_tokens) if is_pdf_related_query(query) else 512

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(60)

    try:
        response = model(
            prompt,
            max_new_tokens=final_max_tokens,
            temperature=0.7,
            top_p=0.9
        )
        signal.alarm(0)
    except TimeoutError:
        return "⚠️ Response took too long. Try a shorter query."

    return response

if __name__ == "__main__":
    print("Chatbot Ready! Type 'exit' to quit.")
    while True:
        user_input = input("\nAsk anything (or type 'exit'): ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = generate_response(user_input)
        print("\nAI:", response)





### summarizer added:  but way too small summary and context/meaning is lost : working without any errors:)
import os
import re
import signal
import logging
from ctransformers import AutoModelForCausalLM
from colbert_retriever import ColBERTRetriever

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer



logging.basicConfig(level=logging.DEBUG)

MODEL_PATH = "../models/mistral/mistral-7b-instruct-v0.1.Q4_K_M.gguf"

print("⏳ Loading Mistral 7B model...")
try:
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="mistral",
        gpu_layers=15,
        context_length=4096
    )
    print("✅ Model loaded successfully on GPU!")
except Exception as e:
    print(f"⚠️ GPU ran out of memory, switching to CPU. Error: {e}")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH,
        model_type="mistral",
        gpu_layers=0,
        context_length=2048
    )

retriever = ColBERTRetriever()

MARKS_TOKENS = {
    "10M": 768,
    "6M": 512,
    "4M": 384
}

def is_pdf_related_query(query):
    query_lower = query.lower()
    pdf_keywords = ["explain", "summary", "describe", "what is", "how does", "10m", "6m", "4m"]
    return any(keyword in query_lower for keyword in pdf_keywords)

def determine_response_type(query):
    query_lower = query.lower()

    marks_match = re.search(r"\b(10\s?marks?|10m|six\s?marks?|6m|four\s?marks?|4m)\b", query_lower)
    if marks_match:
        if "10" in marks_match.group():
            return "10M", MARKS_TOKENS["10M"]
        elif "6" in marks_match.group():
            return "6M", MARKS_TOKENS["6M"]
        else:
            return "4M", MARKS_TOKENS["4M"]

    if "explain" in query_lower or "step by step" in query_lower:
        return "explanation", MARKS_TOKENS["6M"]

    if "summary" in query_lower or "summarize" in query_lower:
        return "summary", MARKS_TOKENS["4M"]

    return "default", MARKS_TOKENS["4M"]

def timeout_handler(signum, frame):
    raise TimeoutError("Response generation took too long")


def summarize_text(text, num_sentences=3):
    parser = PlaintextParser.from_string(text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, num_sentences)
    return " ".join(str(sentence) for sentence in summary)

def generate_response(query):
    if is_pdf_related_query(query):
        response_type, max_response_tokens = determine_response_type(query)

        try:
            pdf_context_chunks = retriever.search(query, top_k=3)  # ✅ Keep 3 chunks
            pdf_context = " ".join(pdf_context_chunks)
            pdf_context = summarize_text(pdf_context, num_sentences=6)  # ✅ Summarize context
            logging.debug(f"Summarized PDF Context: {pdf_context}")
        except Exception as e:
            logging.error(f"ColBERT retrieval failed: {e}")
            pdf_context = ""

        if pdf_context:
            prompt = f"### Instruction: Provide a {response_type} response. Use the provided context if available.\n\n### Question:\n{query}\n\n### Context:\n{pdf_context}\n\n### Response:"
        else:
            prompt = f"### Instruction: Answer concisely in about {max_response_tokens} tokens.\n\n### Question:\n{query}\n\n### Response:"
    else:
        prompt = f"### Instruction: Respond conversationally.\n\n### Query:\n{query}\n\n### Response:"

    input_tokens = model.tokenize(prompt)
    if len(input_tokens) > 1024:
        input_tokens = input_tokens[:1024]  # ✅ Trim prompt to 1024 tokens
        prompt = model.detokenize(input_tokens)

    max_allowed_tokens = 2048 - len(input_tokens)
    final_max_tokens = min(max_response_tokens, max_allowed_tokens) if is_pdf_related_query(query) else 256  # ✅ Reduce to 256 for non-PDF

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # ✅ Reduce timeout to 30s

    try:
        response = model(
            prompt,
            max_new_tokens=final_max_tokens,
            temperature=0.7,
            top_p=0.9
        )
        signal.alarm(0)
    except TimeoutError:
        return "⚠️ Response took too long. Try a shorter query."

    return response


if __name__ == "__main__":
    print("Chatbot Ready! Type 'exit' to quit.")
    while True:
        user_input = input("\nAsk anything (or type 'exit'): ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = generate_response(user_input)
        print("\nAI:", response)




# working and top priority summarizer 
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
        summaries = []

        chunks = self._chunk_text_by_tokens(text)
        for chunk in chunks:
            summary = self.summarizer(
                chunk,
                max_length=self.max_length,
                min_length=self.min_length,
                do_sample=False
            )[0]['summary_text']
            summaries.append(summary)

        final_summary = self._remove_redundancy(" ".join(summaries))
        return final_summary

    def _remove_redundancy(self, text):
        sentences = list(dict.fromkeys(text.split(". ")))  # removes exact sentence repetitions
        return ". ".join(sentences)


# summarizer that gives academic styled answers , perfect 
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


