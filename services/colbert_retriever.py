# services/colbert_retriever.py

import os, pickle, logging
from colbert.searcher import Searcher
from pathlib import Path

UPLOAD_FOLDER = "/home/noyo/web2pdf/services/uploads"
BASE_INDEX_PATH = "/home/noyo/web2pdf/services/experiments/default/indexes"

class ColBERTRetriever:
    def __init__(self, chunk_filename):
        if not chunk_filename:
            raise ValueError("Chunk filename is required in PDF mode")

        chunk_path = os.path.join(UPLOAD_FOLDER, chunk_filename)
        if not os.path.exists(chunk_path):
            raise FileNotFoundError(f"Chunk file not found: {chunk_path}")

        with open(chunk_path, "rb") as f:
            self.text_chunks = pickle.load(f)

        # ✅ Derive index path from chunk filename
        stem = Path(chunk_filename).stem.replace("_text_chunks", "")
        index_path = os.path.join(BASE_INDEX_PATH, f"{stem}_index")

        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Index path not found: {index_path}")

        self.searcher = Searcher(index=index_path)

    def search(self, query_text, top_k=5):
        try:
            results = self.searcher.search(query_text, k=top_k)
            logging.debug(f"ColBERT search results: {results}")

            # Extract document IDs and scores
            doc_ids, scores = results[0], results[-1]
            
            # Retrieve chunks and remove duplicates
            retrieved_chunks = []
            seen_chunks = set()
            for doc_id in doc_ids[:top_k]:
                chunk = self.text_chunks[int(doc_id)]
                if chunk not in seen_chunks:
                    seen_chunks.add(chunk)
                    retrieved_chunks.append(chunk)
            
            return retrieved_chunks
        
        except Exception as e:
            logging.error(f"Search error: {e}")
            return []

