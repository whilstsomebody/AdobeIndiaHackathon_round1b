import json
from datetime import datetime

class OutputFormatter:
    @staticmethod
    def format_output(input_documents_list, persona_str, job_to_be_done_str, extracted_sections, sub_section_analysis):
        """
        Formats the processed data into the specified JSON output format.
        """
        output = {
            "metadata": {
                "input_documents": input_documents_list,
                "persona": persona_str,
                "job_to_be_done": job_to_be_done_str,
                "processing_timestamp": datetime.now().isoformat()
            },
            "extracted_sections": extracted_sections, # These are already formatted and ranked
            "subsection_analysis": sub_section_analysis # Note the 'subsection_analysis' key
        }
        return output