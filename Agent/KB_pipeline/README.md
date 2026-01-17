# General Purpose Multimodal RAG Pipeline

## Overview

This is a **General Purpose, Multimodal RAG (Retrieval-Augmented Generation) System** designed to power Voice AI agents with specific knowledge. It is **domain-agnostic**, meaning it works equally well for:

- **Technical Engineering** (Manuals, Specs, CAD data)
- **Legal & Compliance** (Contracts, Policies, Regulations)
- **Medical & Healthcare** (Guidelines, Research Papers)
- **Finance** (Reports, Spreadsheets)
- **General Business** (Internal Wikis, FAQs)

It ingests **Documents + Structured Data + Images** and synthesizes complete, accurate answers using a Hybrid Search architecture.

---

## 🚀 Key Features

| Feature | Description |
|---------|-------------|
| **Multimodal Ingestion** | Natively handles **PDF, DOCX, XLSX, TXT, Images**. Extracts text, tables, and images. |
| **Hybrid Search** | Combines **Dense Embedding Search** (Semantic) + **BM25 Sparse Search** (Keyword) + **RRF Fusion** for best-in-class retrieval. |
| **Context Aware** | Uses **Parent-Child Chunking**: Searches small chunks for precision, but feeds large parent contexts to the LLM for reasoning. |
| **Image Intelligence** | Detects images in documents, captions them using Vision AI, and enables **Image Retrieval** to show diagrams/charts in the UI. |
| **Structured Answers** | LLM prompts are optimized to provide **complete, structured answers** with values, limits, warnings, and source attribution. |
| **Local Vector Store** | zero-dependency setup. Uses local JSON index + efficient arrays. No external vector DB required for <10k docs. |

---

## 📂 Supported Formats

| Format | Extension | Capabilities |
|--------|-----------|--------------|
| **PDF** | `.pdf` | Full text extraction, Table structure preservation, **Image extraction** (diagrams/figs) |
| **Word** | `.docx` | Headings, Text, Tables, **Embedded Images** |
| **Excel** | `.xlsx` | Sheet processing, Table conversion to Markdown, **Charts/Graphs** detection |
| **Text** | `.txt`, `.md`| Plain text, Markdown processing |
| **Images** | `.png`, `.jpg`| Vision AI analysis & captioning for searchability |

---

## 🛠️ Usage

### 1. Add Documents
Place your files in:
```
Agent/KB_pipeline/kb_data/
```
*(Subfolders are supported and recommended for organization)*

### 2. Ingest
Run the ingestion pipeline to parse and index:
```bash
python KB_pipeline/ingest.py
```

### 3. Test
Verify the system answers correctly:
```bash
python KB_pipeline/test_kb.py "Your question here"
```

---

## ⚙️ Architecture

### Pipeline Stages

1.  **Ingestion & Parsing**
    *   `ContentDetector`: Identifies file type and parses content.
    *   **PDF**: Uses PyMuPDF for reliable text/image extraction.
    *   **Office**: Uses python-docx/openpyxl.
    *   **Vision**: Sends extracted images to GPT-4o-mini for captioning.

2.  **Indexing**
    *   `HierarchicalChunker`: Splits content into **Parent Chunks** (~2000 tokens) and **Child Chunks** (~256 tokens).
    *   **Embeddings**: Generates OpenAI embeddings for Child Chunks.
    *   **BM25**: Builds keyword index for Child Chunks.

3.  **Retrieval (Query Time)**
    *   **Hybrid Search**: `Vectors` + `Keywords` → `RRF Fusion`.
    *   **Context Expansion**: Retrieves the full **Parent Chunk** for the top hits to give the LLM full context.
    *   **Image Retrieval**: Finds relevant images to display in the UI.

4.  **Synthesis**
    *   **LLM Generation**: GPT-4o-mini synthesizes the answer from the context.
    *   **Strict Prompting**: Enforces "Answer based *only* on context", "Cite sources", "Include tolerances/notes".

---

## 🔌 Agent Integration

The pipeline is pre-integrated into `agent.py`.

**Tool Definition:**
```python
@llm.function_tool
async def knowledge_lookup(query: str, show_images: bool = False) -> str:
    """Search the knowledge base. Set show_images=True if user asks to see diagrams."""
    # 1. Query KB
    result = await kb_manager.query(query, include_images=show_images)
    
    # 2. Show Image Overlay (if found)
    if show_images and result.images:
        await show_overlay(...)
        
    # 3. Return Text Answer
    return result.text
```

---

## 🔧 CLI Reference

### `ingest.py`
| Flag | Description |
|------|-------------|
| `--stats` | Show document/chunk/image counts |
| `--force` | Force re-index all documents (ignore cache) |
| `--analyze <file>` | Debug: Show text/table/image breakdown for a file |
| `--query <text>` | Run a test query |

### `test_kb.py`
*   Run without arguments for **Interactive Mode**.
*   Run with `"Query"` for single shot.

---

## 📦 Dependencies

Required packages in `requirements.txt`:
```text
llama-index==0.14.10
pymupdf>=1.24.0      # PDF
python-docx>=1.1.0   # Word
openpyxl>=3.1.0      # Excel
rank-bm25>=0.2.2     # Sparse Search
numpy>=1.26.0
python-dotenv==1.2.1
openai
```
