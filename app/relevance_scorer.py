from sentence_transformers import util

class RelevanceScorer:
    def __init__(self, persona_analyzer):
        self.persona_analyzer = persona_analyzer
        self.query_embedding = self.persona_analyzer.query_embedding

    def score_text(self, text_content):
        """
        Calculates a relevance score for a given text content (section or subsection).
        Uses cosine similarity with the combined persona/job embedding.
        """
        if self.query_embedding is None or not self.persona_analyzer.model or not text_content:
            return 0.0

        try:
            text_embedding = self.persona_analyzer.model.encode(text_content, convert_to_tensor=False)
            similarity = util.cos_sim(self.query_embedding, text_embedding).item()
            return max(0.0, similarity)
        except Exception as e:
            print(f"Error scoring text: {e}")
            return 0.0