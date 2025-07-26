import os
import json
import glob
from app.pdf_parser import PDFParser
from app.persona_analyzer import PersonaAnalyzer
from app.relevance_scorer import RelevanceScorer
from app.output_formatter import OutputFormatter
from datetime import datetime

INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"
PERSONA_JOB_INPUT_FILE = os.path.join(INPUT_DIR, "challenge1b_input.json") 
OUTPUT_JSON_FILENAME = "challenge1b_output.json"

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    persona_data = {}
    if os.path.exists(PERSONA_JOB_INPUT_FILE):
        with open(PERSONA_JOB_INPUT_FILE, 'r', encoding='utf-8') as f:
            persona_input_data = json.load(f)
            persona_data = {
                "persona": persona_input_data.get("persona", {}).get("role", ""),
                "job_to_be_done": persona_input_data.get("job_to_be_done", {}).get("task", ""),
                "input_documents": [doc["filename"] for doc in persona_input_data.get("documents", [])]
            }
            print(f"Loaded Persona: {persona_data['persona']}, Job: {persona_data['job_to_be_done']}")
    else:
        print(f"Error: {PERSONA_JOB_INPUT_FILE} not found. Cannot proceed without persona/job data.")
        return

    persona_description = persona_data['persona']
    job_to_be_done = persona_data['job_to_be_done']

    persona_analyzer = PersonaAnalyzer(persona_description, job_to_be_done)
    relevance_scorer = RelevanceScorer(persona_analyzer)

    all_extracted_sections_raw = [] 
    all_extracted_subsections_raw = [] 

    pdf_filenames_to_process = persona_data['input_documents']
    
    for pdf_filename in pdf_filenames_to_process:
        pdf_path = os.path.join(INPUT_DIR, pdf_filename)
        if not os.path.exists(pdf_path):
            print(f"Warning: PDF file '{pdf_filename}' not found at '{pdf_path}'. Skipping.")
            continue

        print(f"Processing {pdf_filename}...")

        try:
            pdf_parser = PDFParser(pdf_path)
            parsed_sections = pdf_parser.parse_document_to_sections()

            for section in parsed_sections:
                section_full_text = section.get('text', '')
                section_relevance_score = relevance_scorer.score_text(section_full_text)
                
                all_extracted_sections_raw.append({
                    "document": pdf_filename,
                    "section_title": section['title'],
                    "page_number": section['page'],
                    "raw_text": section_full_text,
                    "relevance_score": section_relevance_score
                })

                for sub_section in section.get('sub_sections', []):
                    sub_section_full_text = sub_section.get('text', '')
                    sub_section_relevance_score = relevance_scorer.score_text(sub_section_full_text)

                    refined_text = persona_analyzer.refine_sub_section_text(
                        sub_section_full_text
                    )
                    
                    all_extracted_subsections_raw.append({
                        "document": pdf_filename,
                        "page_number": sub_section['page'],
                        "section_title": sub_section['title'],
                        "refined_text": refined_text,
                        "relevance_score": sub_section_relevance_score
                    })
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")
            continue 

    all_extracted_sections_raw.sort(key=lambda x: x['relevance_score'], reverse=True)
    all_extracted_subsections_raw.sort(key=lambda x: x['relevance_score'], reverse=True)

    final_extracted_sections = []
    for i, section in enumerate(all_extracted_sections_raw[:5]): 
        final_extracted_sections.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": i + 1,
            "page_number": section["page_number"]
        })

    final_sub_section_analysis = []
    for i, subsection in enumerate(all_extracted_subsections_raw[:5]): 
        final_sub_section_analysis.append({
            "document": subsection["document"],
            "refined_text": subsection["refined_text"],
            "page_number": subsection["page_number"]
        })

    output_data = OutputFormatter.format_output(
        persona_data["input_documents"],
        persona_data["persona"],
        persona_data["job_to_be_done"],
        final_extracted_sections,
        final_sub_section_analysis
    )

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_JSON_FILENAME)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"Processing complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()