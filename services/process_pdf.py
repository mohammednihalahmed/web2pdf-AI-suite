# services/process_pdf.py

import os, pickle, fitz, torch, asyncio
from pathlib import Path

from colbert.modeling.checkpoint import Checkpoint
from colbert.infra.config import ColBERTConfig
from colbert.indexer import Indexer

UPLOAD_FOLDER = "/home/noyo/web2pdf/services/uploads"
CHECKPOINT_PATH = "/home/noyo/web2pdf/models/colbertv2.0"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

colbert_config = ColBERTConfig(
    nbits=2, doc_maxlen=140, kmeans_niters=4, nway=2, gpus=1
)
checkpoint = Checkpoint(CHECKPOINT_PATH, colbert_config=colbert_config)

class PDFProcessor:
    def __init__(self, chunk_size=512, chunk_overlap=50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    async def extract_text(self, pdf_path):
        doc = await asyncio.to_thread(fitz.open, pdf_path)
        texts = [page.get_text("text").replace("\n", " ").strip() for page in doc]
        return " ".join(texts)

    def chunk_text(self, text):
        words = text.split(" ")
        chunks = []
        i = 0
        while i < len(words):
            chunks.append(" ".join(words[i:i + self.chunk_size]))
            i += self.chunk_size - self.chunk_overlap
        return chunks

    async def process_and_store(self, pdf_path):
        text = await self.extract_text(pdf_path)
        chunks = self.chunk_text(text)

        pdf_filename = Path(pdf_path).stem
        chunk_filename = f"{pdf_filename}_text_chunks.pkl"
        chunk_path = os.path.join(UPLOAD_FOLDER, chunk_filename)

        with open(chunk_path, "wb") as f:
            pickle.dump(chunks, f)

        # ✅ Create per-PDF index folder
        index_path = f"/home/noyo/web2pdf/services/experiments/default/indexes/{pdf_filename}_index"
        os.makedirs(index_path, exist_ok=True)

        indexer = Indexer(checkpoint=CHECKPOINT_PATH)
        await asyncio.to_thread(
            indexer.index,
            name=index_path,
            collection=chunks,
            overwrite=True
        )

        return chunk_filename  # ✅ So you can send this to frontend
