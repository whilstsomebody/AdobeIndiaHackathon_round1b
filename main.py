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
PERSONA_JOB_FILE = os.path.join(INPUT_DIR, "persona_job.json")

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 1. Load Persona and Job-to-be-Done
    persona_data = {}
    if os.path.exists(PERSONA_JOB_FILE):
        with open(PERSONA_JOB_FILE, 'r', encoding='utf-8') as f:
            persona_input_data = json.load(f)
            persona_data = {
                "persona": persona_input_data.get("persona", {}).get("role", ""), # Extract just the role string
                "job_to_be_done": persona_input_data.get("job_to_be_done", {}).get("task", ""), # Extract just the task string
                "input_documents": [doc["filename"] for doc in persona_input_data.get("documents", [])] # Extract just filenames
            }
            print(f"Loaded Persona: {persona_data['persona']}, Job: {persona_data['job_to_be_done']}")
    else:
        print(f"Error: {PERSONA_JOB_FILE} not found. Cannot proceed without persona/job data.")
        return

    persona_description = persona_data['persona']
    job_to_be_done = persona_data['job_to_be_done']
    
    # Initialize persona analyzer and relevance scorer
    persona_analyzer = PersonaAnalyzer(persona_description, job_to_be_done)
    relevance_scorer = RelevanceScorer(persona_analyzer)

    all_extracted_sections_raw = [] # To hold sections before final ranking and formatting
    all_extracted_subsections_raw = [] # To hold subsections before final ranking and formatting

    # 2. Process each PDF in the input directory
    pdf_paths = glob.glob(os.path.join(INPUT_DIR, "*.pdf"))
    
    # Sort for consistent processing order
    pdf_paths.sort() 

    for pdf_path in pdf_paths:
        pdf_filename = os.path.basename(pdf_path)
        print(f"Processing {pdf_filename}...")

        try:
            pdf_parser = PDFParser(pdf_path)
            
            # Extract basic text content and outline (from Round 1A logic)
            # This is a critical point that needs robust implementation for heading detection.
            parsed_sections = pdf_parser.parse_document_to_sections() # This now handles both outline and content

            # 3. Score Relevance and prepare for output
            for section in parsed_sections:
                section_full_text = section.get('text', '') # Ensure 'text' key exists
                
                # Score the main section
                section_relevance_score = relevance_scorer.score_text(section_full_text)
                
                all_extracted_sections_raw.append({
                    "document": pdf_filename,
                    "section_title": section['title'],
                    "page_number": section['page'],
                    "raw_text": section_full_text, # Keep raw text for sub-section analysis
                    "relevance_score": section_relevance_score # Use a temporary score for sorting
                })

                # Process sub-sections within this main section if they exist
                for sub_section in section.get('sub_sections', []):
                    sub_section_full_text = sub_section.get('text', '')
                    sub_section_relevance_score = relevance_scorer.score_text(sub_section_full_text)

                    # Refine text for sub-sections based on persona/job-to-be-done
                    refined_text = persona_analyzer.refine_sub_section_text(
                        sub_section_full_text
                    )
                    
                    all_extracted_subsections_raw.append({
                        "document": pdf_filename,
                        "page_number": sub_section['page'],
                        "section_title": sub_section['title'],
                        "refined_text": refined_text,
                        "relevance_score": sub_section_relevance_score # Use a temporary score for sorting
                    })
        except Exception as e:
            print(f"Error processing {pdf_filename}: {e}")
            continue # Continue to next PDF if one fails

    # 4. Global Ranking for Sections and Sub-sections based on relevance_score
    all_extracted_sections_raw.sort(key=lambda x: x['relevance_score'], reverse=True)
    all_extracted_subsections_raw.sort(key=lambda x: x['relevance_score'], reverse=True)

    # Assign final importance ranks (1-N) and filter out the raw_text/relevance_score
    final_extracted_sections = []
    for i, section in enumerate(all_extracted_sections_raw):
        final_extracted_sections.append({
            "document": section["document"],
            "section_title": section["section_title"],
            "importance_rank": i + 1,
            "page_number": section["page_number"]
        })

    final_sub_section_analysis = []
    for i, subsection in enumerate(all_extracted_subsections_raw):
        # Only include top 5 subsections, as suggested by the example output
        # You might need to adjust this number based on actual challenge requirements or desired output length
        if i < 5: 
            final_sub_section_analysis.append({
                "document": subsection["document"],
                "refined_text": subsection["refined_text"],
                "page_number": subsection["page_number"]
            })

    # 5. Generate final JSON output
    output_data = OutputFormatter.format_output(
        persona_data["input_documents"],
        persona_data["persona"],
        persona_data["job_to_be_done"],
        final_extracted_sections,
        final_sub_section_analysis
    )

    output_filename = "consolidated_output.json" # As per example output
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
    print(f"Processing complete. Output saved to {output_path}")

if __name__ == "__main__":
    main()