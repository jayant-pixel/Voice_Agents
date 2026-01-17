# Knowledge Base User Manual

This manual explains how to manage, update, and test the Knowledge Base (KB) for your Voice AI Agent.

---

## 1. Adding Files

The system supports:
- **PDFs** (`.pdf`) - Text, Tables, Images
- **Word Docs** (`.docx`) - Text, Tables, Images
- **Excel** (`.xlsx`) - Spreadsheets, Charts
- **Text** (`.txt`, `.md`)

### Steps:
1.  Open the `Agent/KB_pipeline/kb_data/` folder.
2.  **Copy/Paste** your files into this folder.
3.  You can create subfolders (e.g., `manuals/`, `specs/`) to keep things organized.

> **Tip:** Use descriptive filenames like `Machine_Manual_v2.pdf` instead of `doc1.pdf`. The AI sees the filename!

---

## 2. Ingesting (Parsing) Data

After adding files, you must "ingest" them so the AI can read them.

1.  Open a terminal in the `Agent` folder.
2.  Run the ingestion command:
    ```bash
    python KB_pipeline/ingest.py
    ```

**What happens?**
- The system reads every file.
- It extracts text, tables, and **captions images** automatically.
- It builds a search index.
- New files are added; existing files are skipped (unless changed).

**Force Re-ingest:**
If you want to re-process everything (e.g., after a software update), run:
```bash
python KB_pipeline/ingest.py --force
```

---

## 3. Verifying Content

Want to know if the AI can "see" the images or tables in your file? Use the analysis tool.

```bash
python KB_pipeline/ingest.py --analyze "your_file.pdf"
```

**Output Example:**
```
📋 Content Summary:
  Has text: ✅
  Has tables: ✅
  Has images: ✅  (106 found)
  Page count: 15
```

This confirms the system successfully extracted the content.

---

## 4. Testing Queries

You can test the AI's brain directly before trying it in the voice agent.

**Interactive Mode:**
```bash
python KB_pipeline/test_kb.py
```
Type your question and press Enter. The AI will show:
- The **Answer**
- The **Sources** (filename + page numbers)
- Any **Images** found

**Single Query:**
```bash
python KB_pipeline/test_kb.py "How do I reset the device?"
```

---

## 5. How It Handles Content

### 📄 Text
Broken into smart chunks. The AI reads full paragraphs to understand context.

### 📊 Tables
Converted into text format so the AI can read row-by-row data. 
*Example: "Row 1: Voltage = 5V, Current = 2A"*

### 🖼️ Images & Charts
The system uses Vision AI to "look" at every image during ingestion. It writes a caption like:
> *"Diagram of the wiring schematics for the control board, labeling ports A through E."*

When you search for "wiring schematic", the AI finds this image and can show it to you!

---

## 6. Troubleshooting

| Issue | Solution |
|-------|----------|
| **"No info found"** | Check if file is in `kb_data` and you ran `ingest.py`. Try rephrasing with specific keywords. |
| **Wrong Answer** | Check the source file. Is the info actually there? Use `--analyze` to see if text was extracted. |
| **Old Info** | Did you update the file? Run `ingest.py --force` to overwrite the old index. |
| **Slow Search** | First search is slow (loading AI models). Subsequent searches are fast ( < 1 sec). |

---

## 7. Best Practices

- **Keep files focused**: One topic per file is better than one giant "everything" PDF.
- **Check Page Numbers**: The AI now cites page numbers. Use them to verify the source!
- **Images**: Ensure images in PDFs are clear. Blurry scans are hard for AI to read.
