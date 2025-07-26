import os
from sentence_transformers import SentenceTransformer, util
import re

# Ensure model is downloaded or available locally.
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'all-MiniLM-L6-v2')

class PersonaAnalyzer:
    def __init__(self, persona_description, job_to_be_done):
        self.persona_description = persona_description
        self.job_to_be_done = job_to_be_done
        try:
            self.model = SentenceTransformer(MODEL_PATH)
            print(f"SentenceTransformer model loaded from {MODEL_PATH}")
        except Exception as e:
            print(f"Error loading SentenceTransformer model from {MODEL_PATH}: {e}")
            print("Ensure the model 'all-MiniLM-L6-v2' is downloaded and placed in the 'app/models' directory.")
            self.model = None

        # Combine persona and job into a single query for relevance
        self.query_text = f"Persona: {self.persona_description}. Task: {self.job_to_be_done}."
        self.query_embedding = self._get_embedding(self.query_text)
        
        if self.query_embedding is None:
            print("Warning: Could not create query embedding. Relevance scoring may be impaired.")

    def _get_embedding(self, text):
        if self.model and text:
            return self.model.encode(text, convert_to_tensor=False)
        return None

    def refine_sub_section_text(self, sub_section_text):
        """
        Refines the sub-section text to highlight relevant parts based on persona/job.
        This uses sentence similarity to extract the most relevant sentences.
        """
        if not self.model or not sub_section_text or self.query_embedding is None:
            return sub_section_text # Return original if model not loaded or no text

        # Split text into sentences for fine-grained analysis
        sentences = re.split(r'(?<=[.!?])\s+', sub_section_text)
        sentences = [s.strip() for s in sentences if s.strip()] # Clean empty sentences

        if not sentences:
            return ""

        sentence_embeddings = self.model.encode(sentences, convert_to_tensor=False)

        # Calculate cosine similarity between query and each sentence
        similarities = util.cos_sim(self.query_embedding, sentence_embeddings)[0].tolist()

        # Get top N most similar sentences based on relevance to the query
        # For a "group of 10 college friends" and "4 days", focus on activities, food, budget, fun.
        # Prioritize sentences that mention these themes.
        
        # Sort sentences by similarity and retrieve them in their original document order for coherence
        sentence_scores = sorted([(sim, idx, sent) for idx, (sim, sent) in enumerate(zip(similarities, sentences))], reverse=True)
        
        # Aim for a few key sentences, but not too many.
        # Adjust num_sentences_to_extract based on desired output verbosity.
        num_sentences_to_extract = min(3, len(sentences)) # Get up to 3 most relevant sentences

        selected_sentence_indices = sorted([item[1] for item in sentence_scores[:num_sentences_to_extract]])
        refined_sentences = [sentences[i] for i in selected_sentence_indices]
        
        # If no sentences are highly relevant, fallback to a short snippet or the original.
        if not refined_sentences and sentences:
            return sentences[0] # Just take the first sentence if no good matches
            
        return " ".join(refined_sentences)