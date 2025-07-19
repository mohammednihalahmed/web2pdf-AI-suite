import numpy as np
import torch
from colbert import Searcher

print(f"NumPy: {np.__version__}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA: {torch.cuda.is_available()}")

try:
    # Use your actual index path here
    searcher = Searcher(index="/home/noyo/web2pdf/chatbot/experiments/default/indexes/colbert_index")
    print("✅ ColBERT loaded successfully!")
    
    # Test search
    results = searcher.search("test query")
    print(f"Search results: {results}")
except Exception as e:
    print(f"❌ Error: {str(e)}")