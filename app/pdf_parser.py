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
            if b['type'] == 0:
                for l_idx, l in enumerate(b['lines']):
                    for s_idx, s in enumerate(l['spans']):
                        text = s['text'].strip()
                        if not text:
                            continue
                        is_bold = 'bold' in s['font'].lower() or re.search(r'[B][oO][lL][dD]', s['font'])
                        
                        parsed_blocks.append({
                            'text': text,
                            'size': s['size'],
                            'font': s['font'],
                            'bbox': s['bbox'],
                            'is_bold': is_bold,
                            'origin': s['origin'],
                            'line_num': l_idx,
                            'span_num': s_idx
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

        all_font_sizes = []
        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            for block in self._get_text_blocks_with_properties(page):
                all_font_sizes.append(block['size'])
        
        if not all_font_sizes:
            return []

        unique_sizes = sorted(list(set(all_font_sizes)), reverse=True)
        title_size_threshold = unique_sizes[0] if len(unique_sizes) > 0 else 0
        h1_size_threshold = unique_sizes[1] if len(unique_sizes) > 1 else 0
        h2_size_threshold = unique_sizes[2] if len(unique_sizes) > 2 else 0
        h3_size_threshold = unique_sizes[3] if len(unique_sizes) > 3 else 0

        title_size_threshold = 20
        h1_size_threshold = 16.0
        h2_size_threshold = 12.0
        h3_size_threshold = 10.0

        def _add_current_section():
            nonlocal current_section_title, current_section_text_buffer, current_section_page
            if current_section_title and current_section_text_buffer:
                document_sections.append({
                    'title': current_section_title,
                    'level': current_section_level,
                    'page': current_section_page,
                    'text': "\n".join(current_section_text_buffer).strip(),
                    'sub_sections': []
                })
            current_section_title = None
            current_section_text_buffer = []
            current_section_page = None

        for page_num in range(self.doc.page_count):
            page = self.doc.load_page(page_num)
            blocks = self._get_text_blocks_with_properties(page)

            for block in blocks:
                text = block['text']
                size = block['size']
                is_bold = block['is_bold']
                if page_num == 0 and size >= title_size_threshold and not document_sections:
                    if not document_sections and "Comprehensive Guide to" in text:
                        pass 
                    continue

                if size >= h1_size_threshold and is_bold and (block['bbox'][0] < 50):
                    _add_current_section()
                    current_section_title = text
                    current_section_level = "H1"
                    current_section_page = page_num + 1
                    current_section_text_buffer = []

                if size >= h2_size_threshold and is_bold and (block['bbox'][0] < 100):
                    _add_current_section()
                    current_section_title = text
                    current_section_level = "H2"
                    current_section_page = page_num + 1
                    current_section_text_buffer = []
                    continue

                if current_section_title:
                    current_section_text_buffer.append(text)
                
        _add_current_section()

        final_structured_sections = []
        for section in document_sections:
            temp_sub_sections = []
            section_text_lines = section['text'].split('\n')
            
            current_subsection_title = None
            current_subsection_text_buffer = []
            current_subsection_page = None

            for line in section_text_lines:
                is_h3_candidate = False
                if line.startswith("• ") or (line.strip() and line.strip().endswith(":")):
                    if current_subsection_title and current_subsection_text_buffer:
                        temp_sub_sections.append({
                            'title': current_subsection_title,
                            'text': "\n".join(current_subsection_text_buffer).strip(),
                            'page': current_subsection_page if current_subsection_page else section['page']
                        })
                    
                    current_subsection_title = line.split(':', 1)[0].replace('•', '').strip() if ':' in line else line.replace('•', '').strip()
                    current_subsection_text_buffer = [line]
                    current_subsection_page = section['page']
                    is_h3_candidate = True
                
                if not is_h3_candidate and current_subsection_text_buffer:
                    current_subsection_text_buffer.append(line)
                elif not current_subsection_title:
                     pass

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