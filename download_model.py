import os
from sentence_transformers import SentenceTransformer

# Define the local path where you want to save the model
model_name = 'all-MiniLM-L6-v2'
local_model_path = os.path.join('app', 'models', model_name)

print(f"Downloading {model_name} to {local_model_path}...")
try:
    model = SentenceTransformer(model_name)
    model.save(local_model_path)
    print("Download complete and model saved locally.")
except Exception as e:
    print(f"Error during model download: {e}")