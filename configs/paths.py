import os

# Base project directory (root of your project)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Important paths
MODELS_DIR = os.path.join(BASE_DIR, 'models')
SERVICES_DIR = os.path.join(BASE_DIR, 'services')
UPLOADS_DIR = os.path.join(SERVICES_DIR, 'uploads')
INDEXES_DIR = os.path.join(SERVICES_DIR, 'indexes')

# Specific model paths
MISTRAL_MODEL_PATH = os.path.join(MODELS_DIR, 'mistral', 'mistral-7b-instruct-v0.1.Q4_K_M.gguf')

TEXT_STORAGE_PATH = os.path.join(SERVICES_DIR, 'text_chunks.pkl')

