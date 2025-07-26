import os
from sentence_transformers import SentenceTransformer, util
import re

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
            return sub_section_text

        sentences = re.split(r'(?<=[.!?])\s+', sub_section_text)
        sentences = [s.strip() for s in sentences if s.strip()]

        if not sentences:
            return ""

        sentence_embeddings = self.model.encode(sentences, convert_to_tensor=False)
        similarities = util.cos_sim(self.query_embedding, sentence_embeddings)[0].tolist()
        sentence_scores = sorted([(sim, idx, sent) for idx, (sim, sent) in enumerate(zip(similarities, sentences))], reverse=True)
        num_sentences_to_extract = min(3, len(sentences))

        selected_sentence_indices = sorted([item[1] for item in sentence_scores[:num_sentences_to_extract]])
        refined_sentences = [sentences[i] for i in selected_sentence_indices]

        if not refined_sentences and sentences:
            return sentences[0]
        return " ".join(refined_sentences)