import fitz  # PyMuPDF
import re

class PDFParser:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def _get_text_blocks_with_properties(self, page):
        """Extracts text blocks with font size, bold status, and position."""
        blocks = page.get_text("dict")["blocks"]
        parsed_blocks = []
        for b in blocks:
            if b['type'] == 0:  # Text block
                for l_idx, l in enumerate(b['lines']):
                    for s_idx, s in enumerate(l['spans']):
                        text = s['text'].strip()
                        if not text:
                            continue
                        # Heuristics for bold detection (can be improved)
                        is_bold = 'bold' in s['font'].lower() or re.search(r'[B][oO][lL][dD]', s['font'])
                        
                        parsed_blocks.append({
                            'text': text,
                            'size': s['size'],
                            'font': s['font'],
                            'bbox': s['bbox'],
                            'is_bold': is_bold,
                            'origin': s['origin'], # (x,y) coordinates
                            'line_num': l_idx, # Line index within the block
                            'span_num': s_idx  # Span index within the line
                        })
        return parsed_blocks

    def parse_document_to_sections(self):
        """
        Parses the entire document to identify sections (H1, H2, H3) and extract their content.
        This is a more robust heuristic-based approach.
        """
        document_sections = []
        current_section_level = 0
        current_section_title = None
        current_section_text_buffer = []
        current_section_page = None

        # Analyze font sizes across the entire document to set thresholds
        all_font_sizes = []
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            for block in self._get_text_blocks_with_properties(page):
                all_font_sizes.append(block['size'])
        
        if not all_font_sizes:
            return [] # No text found

        # Simple approach for thresholds (can be improved with clustering or more sophisticated analysis)
        unique_sizes = sorted(list(set(all_font_sizes)), reverse=True)
        
        # Example: Assume top 3-4 largest unique sizes are for Title, H1, H2, H3
        # These thresholds need careful tuning for your specific PDFs!
        title_size_threshold = unique_sizes[0] if len(unique_sizes) > 0 else 0
        h1_size_threshold = unique_sizes[1] if len(unique_sizes) > 1 else 0
        h2_size_threshold = unique_sizes[2] if len(unique_sizes) > 2 else 0
        h3_size_threshold = unique_sizes[3] if len(unique_sizes) > 3 else 0 # Adjust if you have many sizes

        # Adjust these based on observation of the "South of France" PDFs:
        # Looking at the PDFs, titles are ~22-24, H1 are ~16-18, H2 are ~12-14, H3 are ~10-12 and bold
        # Let's set some concrete thresholds that seem to work for the sample PDFs.
        title_size_threshold = 20 # For the main document title (usually on page 1)
        h1_size_threshold = 16.0 # "Restaurants", "Hotels", "Introduction" etc.
        h2_size_threshold = 12.0 # "Budget-Friendly Restaurants", "Family-Friendly Restaurants" etc.
        h3_size_threshold = 10.0 # Some lists might be H3-like, or strong points within H2

        # A more robust approach might be to collect all potential headings and then
        # infer hierarchy based on size, bold, and indentation.

        def _add_current_section():
            nonlocal current_section_title, current_section_text_buffer, current_section_page
            if current_section_title and current_section_text_buffer:
                # Basic sub-section placeholder (will refine in a later pass or recursively)
                document_sections.append({
                    'title': current_section_title,
                    'level': current_section_level,
                    'page': current_section_page,
                    'text': "\n".join(current_section_text_buffer).strip(),
                    'sub_sections': [] # This will be populated in a secondary pass or more complex logic
                })
            current_section_title = None
            current_section_text_buffer = []
            current_section_page = None

        # First pass: Identify main headings (H1, H2) and their content
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            blocks = self._get_text_blocks_with_properties(page)

            for block in blocks:
                text = block['text']
                size = block['size']
                is_bold = block['is_bold']
                
                # Simple check for the main document title on the first page
                if page_num == 0 and size >= title_size_threshold and not document_sections:
                    if not document_sections and "Comprehensive Guide to" in text: # Specific for this PDF
                         # We'll treat the main document title differently for output metadata
                        pass 
                        # Or, you can add it as a top-level section if desired:
                        # if not current_section_title: # Only if no section is open
                        #    _add_current_section()
                        #    current_section_title = text
                        #    current_section_level = "TITLE" # Custom level
                        #    current_section_page = page_num + 1
                        #    current_section_text_buffer = []
                    continue # Skip processing the main document title as a regular section for now


                # Detect H1 headings
                if size >= h1_size_threshold and is_bold and (block['bbox'][0] < 50): # Left-aligned heuristic
                    _add_current_section() # Close previous section
                    current_section_title = text
                    current_section_level = "H1"
                    current_section_page = page_num + 1
                    current_section_text_buffer = []
                    continue # Don't add heading itself to buffer yet

                # Detect H2 headings (assuming they are smaller than H1 but still prominent)
                if size >= h2_size_threshold and is_bold and (block['bbox'][0] < 100): # Left-aligned or slightly indented
                    _add_current_section() # Close previous section
                    current_section_title = text
                    current_section_level = "H2"
                    current_section_page = page_num + 1
                    current_section_text_buffer = []
                    continue

                # Add text to current section buffer
                if current_section_title:
                    current_section_text_buffer.append(text)
                
        _add_current_section() # Add the last section

        # Now, refine by identifying sub-sections (H3) within these larger sections
        # This requires a second pass or more complex recursive logic.
        # For simplicity, let's treat H3s as part of the section text but try to extract them as separate entities.
        
        # This is a VERY simplified recursive-like approach for sub-sections.
        # A full, accurate hierarchical parser is a separate project.
        final_structured_sections = []
        for section in document_sections:
            temp_sub_sections = []
            section_text_lines = section['text'].split('\n')
            
            current_subsection_title = None
            current_subsection_text_buffer = []
            current_subsection_page = None # Will try to infer from section page

            for line in section_text_lines:
                # Attempt to detect H3-like elements within section text (e.g., bullet points, bolded phrases)
                # This is extremely heuristic and will vary per document.
                # For example, "• Chez Pipo (Nice):" in the Restaurants PDF is a potential H3-level entry.
                # Looking at the PDFs, H3-like items are often bullet points or short bolded phrases.
                is_h3_candidate = False
                if line.startswith("• ") or (line.strip() and line.strip().endswith(":")):
                    # Further check if it looks like a sub-heading (e.g., shorter, starts new idea)
                    # This needs better text analysis. For now, a simple check:
                    
                    # This part is highly dependent on PDF layout.
                    # Given the sample PDFs, the bullet points under H2 are the 'sub-sections'.
                    # We'll treat the bullet point title as 'section_title' for the sub-section analysis.
                    # The content following it until the next bullet point (or end of main section) is its 'refined_text'.
                    
                    # For a simple approach: if it's a bullet, treat it as a new sub_section candidate
                    if current_subsection_title and current_subsection_text_buffer:
                        # Append the previous sub_section
                        temp_sub_sections.append({
                            'title': current_subsection_title,
                            'text': "\n".join(current_subsection_text_buffer).strip(),
                            'page': current_subsection_page if current_subsection_page else section['page'] # Infer page
                        })
                    
                    current_subsection_title = line.split(':', 1)[0].replace('•', '').strip() if ':' in line else line.replace('•', '').strip()
                    current_subsection_text_buffer = [line] # Include the bullet point line in its text
                    current_subsection_page = section['page'] # Assume same page for now
                    is_h3_candidate = True # Mark that we're starting a new subsection
                
                if not is_h3_candidate and current_subsection_text_buffer:
                    current_subsection_text_buffer.append(line)
                elif not current_subsection_title: # If no subsection started yet, just add to main section text
                     pass # We will re-assemble main section text after sub-section extraction


            # Add the last detected sub-section
            if current_subsection_title and current_subsection_text_buffer:
                 temp_sub_sections.append({
                    'title': current_subsection_title,
                    'text': "\n".join(current_subsection_text_buffer).strip(),
                    'page': current_subsection_page if current_subsection_page else section['page']
                })

            section['sub_sections'] = temp_sub_sections
            final_structured_sections.append(section)
            
        return final_structured_sections

    def extract_full_text_by_page(self):
        """Extracts full text content for each page."""
        full_text = {}
        for page_num, page in enumerate(self.doc):
            full_text[page_num + 1] = page.get_text()
        return full_text