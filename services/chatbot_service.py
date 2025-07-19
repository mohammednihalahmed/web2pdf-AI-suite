from ctransformers import AutoModelForCausalLM
from .colbert_retriever import ColBERTRetriever
from .summarization import TextSummarizer
import logging
import re
import signal
from configs.paths import MISTRAL_MODEL_PATH

logging.basicConfig(level=logging.DEBUG)

_model = None  # Global model reference

def start_model():
    global _model
    if _model is not None:
        print("ℹ️ Mistral model already running.")
        return
    print("⏳ Loading Mistral model...")
    try:
        _model = AutoModelForCausalLM.from_pretrained(
            MISTRAL_MODEL_PATH,
            model_type="mistral",
            gpu_layers=15,
            context_length=4096
        )
        print("✅ Mistral model loaded successfully on GPU!")
    except Exception as e:
        print(f"⚠️ GPU loading failed: {e}\nFalling back to CPU...")
        _model = AutoModelForCausalLM.from_pretrained(
            MISTRAL_MODEL_PATH,
            model_type="mistral",
            gpu_layers=0,
            context_length=2048
        )
        print("✅ Mistral model loaded on CPU.")

def stop_model():
    global _model
    if _model is not None:
        print("🛑 Stopping Mistral model...")
        _model = None
        print("🧹 Model resources released.")
    else:
        print("ℹ️ Model is already stopped.")

def get_model():
    return _model

# Initialize model on startup
start_model()

summarizer = TextSummarizer()

MARKS_TOKENS = {
    "10M": 600,
    "6M": 512,
    "4M": 384
}

def is_pdf_related_query(query):
    query_lower = query.lower()
    pdf_keywords = ["explain", "summary", "describe", "what", "how does", "10m", "6m", "4m"]
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

def generate_response(query, mode, chunk_filename=None):
    if mode == "pdf":
        response_type, max_response_tokens = determine_response_type(query)

        try:
            retriever = ColBERTRetriever(chunk_filename)
            pdf_context_chunks = retriever.search(query, top_k=3)
            pdf_context = " ".join(pdf_context_chunks)
            
            if pdf_context.strip():
                summarized_context = summarizer.summarize_large_text(pdf_context)
                logging.debug(f"Summarized PDF Context: {summarized_context}")
                return summarized_context
            else:
                return "⚠️ No relevant PDF content found for your query."
        except Exception as e:
            logging.error(f"ColBERT retrieval failed: {e}")
            return "⚠️ Error retrieving PDF content."

    elif mode == "general":
        model = get_model()
        if model is None:
            return "⚠️ Model is currently paused for processing. Please wait and try again."

        prompt = f"### Instruction: Answer conversationally.\n\n### Query:\n{query}\n\n### Response:"
        input_tokens = model.tokenize(prompt)
        if len(input_tokens) > 1024:
            input_tokens = input_tokens[:1024]
            prompt = model.detokenize(input_tokens)

        max_allowed_tokens = 2048 - len(input_tokens)
        final_max_tokens = min(512, max_allowed_tokens)

        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(40)

        try:
            response = model(
                prompt,
                max_new_tokens=final_max_tokens,
                temperature=0.7,
                top_p=0.9
            )
            signal.alarm(0)
            return response
        except TimeoutError:
            return "⚠️ Response took too long. Try a shorter query."
        except Exception as e:
            signal.alarm(0)
            return f"⚠️ Generation failed: {str(e)}"

    else:
        return "⚠️ Invalid mode. Use 'pdf' or 'general'."

