# Adobe India Hackathon - Round 1B: Persona-Driven Document Intelligence

## Project Overview

This project provides a solution for Round 1B of the Adobe India Hackathon, focusing on "Persona-Driven Document Intelligence." My system acts as an intelligent document analyst, capable of extracting and prioritizing relevant information from a collection of PDF documents based on a specific user persona and their immediate "job-to-be-done."

## Approach Explanation

### My Mission: Connecting What Matters for the User Who Matters

[cite_start]For Round 1B of the Adobe India Hackathon, my core mission is to build a system that acts as an intelligent document analyst[cite: 318]. [cite_start]I aim to extract and prioritize the most relevant sections from a collection of documents based on a specific user persona and their immediate "job-to-be-done"[cite: 318]. [cite_start]My goal is to create a generic solution that can handle diverse domains (like research papers, textbooks, or financial reports [cite: 323][cite_start]), personas (researcher, student, salesperson [cite: 324]), and job-to-be-done scenarios, ensuring it's adaptable to various document types.

### My Methodology: A Multi-Stage Intelligent Pipeline

[cite_start]My approach to this challenge involves a structured, multi-stage pipeline designed for efficiency and accuracy, while operating within the given constraints[cite: 360, 361, 362, 363, 364].

1.  **Document Parsing and Structure Extraction (Leveraging Round 1A Foundation):**
    [cite_start]I start by taking a collection of 3-10 related PDF documents as input[cite: 320]. [cite_start]For each PDF, I employ a refined document parsing strategy, building upon the principles of Round 1A's outline extraction[cite: 239, 240]. My `PDFParser` analyzes text blocks for attributes such as font size, bolding, and positional layout. [cite_start]While I understand that relying solely on font sizes can be misleading for heading level determination[cite: 303], my parser uses a heuristic combination of these features to accurately identify hierarchical headings (H1, H2, H3) and segment the document's full text into logical sections and subsections. This foundational step is crucial for understanding the content's organization.

2.  **Persona and Job-to-be-Done Understanding:**
    [cite_start]I receive a persona definition, which includes a role and specific expertise/focus areas [cite: 320][cite_start], and a concrete "job-to-be-done"[cite: 321]. To semantically interpret these, I utilize the `all-MiniLM-L6-v2` model from the `sentence-transformers` library. I combine the persona's role and the task into a concise query string, which is then encoded into a dense vector embedding. This embedding serves as the "intent" vector, representing the user's specific needs and context.

3.  **Relevance Scoring and Ranking:**
    For every extracted section and sub-section, I generate its semantic embedding using the same `all-MiniLM-L6-v2` model. I then calculate the cosine similarity between each content embedding and the persona's "intent" embedding. The resulting similarity score directly indicates the relevance of that content to the user's task. All sections and subsections are then globally ranked based on these scores, with higher scores indicating greater importance. [cite_start]This forms the basis for the `importance_rank` in my output[cite: 353].

4.  **Sub-Section Analysis and Refinement:**
    [cite_start]For the `subsection_analysis` output[cite: 354], I aim for granular insights. I refine the extracted text of each relevant sub-section by identifying and extracting the most pertinent sentences. [cite_start]This process involves further semantic comparison of individual sentences within a subsection against the persona's query, ensuring that the "refined_text" [cite: 357] directly addresses the job-to-be-done with conciseness and accuracy.

5.  **Output Generation:**
    [cite_start]Finally, I compile all the processed information—including metadata (input documents, persona, job-to-be-done, processing timestamp [cite: 344][cite_start]), the globally ranked `extracted_sections` [cite: 349][cite_start], and the refined `subsection_analysis` [cite: 354][cite_start]—into a single JSON file named `challenge1b_output.json`, strictly adhering to the specified format[cite: 342].

### Models and Libraries Used

I've carefully selected libraries and a model that comply with the hackathon's constraints:
* **PyMuPDF (fitz):** My primary tool for efficient PDF parsing and robust text extraction.
* **`sentence-transformers` (with `all-MiniLM-L6-v2`):** I use this for generating semantic embeddings, which is critical for understanding the persona's intent and scoring the relevance of document content. [cite_start]The `all-MiniLM-L6-v2` model is well under the $\le 1GB$ model size constraint[cite: 361].
* **`scikit-learn`, `numpy`, `scipy`:** These are foundational Python libraries that support the numerical operations and utilities used in my solution.

### Constraints Adhered To

I've ensured my solution strictly adheres to all specified constraints:
* [cite_start]**CPU Only:** My entire solution is designed to run exclusively on CPU, with no GPU dependencies[cite: 360].
* [cite_start]**Model Size:** The chosen `all-MiniLM-L6-v2` model is well within the $\le 1GB$ size limit[cite: 361].
* [cite_start]**Processing Time:** I've optimized my code for efficiency, targeting a processing time of $\le 60$ seconds for a document collection (3-5 documents)[cite: 362].
* [cite_start]**No Internet Access:** All model assets are self-contained within the Docker image, ensuring no internet access is allowed during execution[cite: 364].
* [cite_start]**Runtime Environment:** My solution is built to run on a system with 8 CPUs and 16 GB RAM configurations[cite: 289].

## How to Build and Run My Solution

To build and run my solution, please follow these steps from the root directory of my project (`adobe-hackathon-1b/`):

1.  **Create the `app/models` Directory:**
    I'll create the necessary directory to store the downloaded model.
    ```bash
    mkdir -p app/models
    ```

2.  **Create `requirements.txt`:**
    I'll ensure all my Python dependencies are listed in this file.
    ```bash
    echo "PyMuPDF==1.24.1" > requirements.txt
    echo "sentence-transformers==2.7.0" >> requirements.txt
    echo "scikit-learn==1.5.0" >> requirements.txt
    echo "numpy==1.26.4" >> requirements.txt
    echo "scipy==1.13.1" >> requirements.txt
    ```

3.  **Create the Model Download Script (`download_model.py`):**
    This script is crucial for fetching the necessary NLP model locally.
    ```python
    import os
    from sentence_transformers import SentenceTransformer

    model_name = 'all-MiniLM-L6-v2'
    local_model_path = os.path.join('app', 'models', model_name)

    print(f"Downloading {model_name} to {local_model_path}...")
    try:
        model = SentenceTransformer(model_name)
        model.save(local_model_path)
        print("Download complete and model saved locally.")
    except Exception as e:
        print(f"Error during model download: {e}")
        print("Please ensure you have an active internet connection for the initial download.")
    ```

4.  **Install `sentence-transformers` Locally (for running download script):**
    I need to install this library on my local machine to execute `download_model.py`.
    ```bash
    pip install sentence-transformers
    ```
    *Note: If you encounter an `externally-managed-environment` error, please create and activate a Python virtual environment first by running `python3 -m venv .venv` and then `source .venv/bin/activate` before executing this `pip install` command.*

5.  **Run the Model Download Script:**
    This step will download the `all-MiniLM-L6-v2` model into my `app/models/` directory, making it available for offline use.
    ```bash
    python download_model.py
    ```

6.  **Place Your Input Files:**
    I'll create an `input` directory in my project root and place all my sample PDFs (e.g., `South of France - Cities.pdf`, `South of France - Cuisine.pdf`, etc.) inside it. Crucially, I will also place the `challenge1b_input.json` file, containing the persona and job-to-be-done details, within this `input` directory.

7.  **Build the Docker Image:**
    From my project's root directory (`adobe-hackathon-1b/`), I will build the Docker image. I'll replace `mysolutionname:somerandomidentifier` with my chosen image name and tag.
    ```bash
    docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier .
    ```

8.  **Run the Docker Container:**
    This command will execute my solution within the Docker container. It processes the PDFs and the `challenge1b_input.json` from the mounted `input` directory and saves the consolidated `challenge1b_output.json` to the mounted `output` directory. [cite_start]I ensure no network access during execution by including `--network none`[cite: 276].
    ```bash
    docker run --rm -v "$(pwd)/input:/app/input" -v "$(pwd)/output:/app/output" --network none mysolutionname:somerandomidentifier
    ```