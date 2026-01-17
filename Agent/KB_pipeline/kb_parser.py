"""
KB Parser
=========
Heavy Knowledge Base Parser & Ingester.
Handles document loading, parsing (unstructured, pymupdf), chunking, and indexing.
Not used at pure runtime/search.
"""

import logging
import json
import base64
import hashlib
import openai
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import common components
try:
    from .kb_common import ContentElement, DocumentChunk, DocumentMeta, HierarchicalChunker, HybridSearchEngine
except ImportError:
    from kb_common import ContentElement, DocumentChunk, DocumentMeta, HierarchicalChunker, HybridSearchEngine

logger = logging.getLogger("kb-parser")


class ContentDetector:
    """
    Detects and classifies content inside documents.
    """
    
    def __init__(self, use_vision_for_charts: bool = True):
        self.use_vision_for_charts = use_vision_for_charts
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Verify required libraries are available."""
        try:
            from unstructured.partition.auto import partition
            self.unstructured_available = True
        except ImportError:
            logger.warning("Install unstructured: pip install unstructured[all-docs]")
            self.unstructured_available = False
    
    def detect_content(self, file_path: Path) -> Tuple[List[ContentElement], Dict]:
        """Parse document and detect content."""
        if not self.unstructured_available:
            return self._fallback_parse(file_path)
        
        from unstructured.partition.auto import partition
        
        try:
            elements = partition(
                filename=str(file_path),
                strategy="hi_res",
                extract_images_in_pdf=True,
                infer_table_structure=True,
            )
        except Exception as e:
            logger.warning(f"Hi-res parsing failed, trying fast mode: {e}")
            try:
                elements = partition(filename=str(file_path), strategy="fast")
            except Exception as e2:
                logger.warning(f"Fast parsing also failed: {e2}")
                elements = []
        
        if not elements:
            return self._fallback_parse(file_path)
        
        content_elements = []
        summary = {
            "has_text": False, "has_tables": False, 
            "has_images": False, "has_charts": False, 
            "has_formulas": False, "page_count": 0, "element_counts": {}
        }
        
        last_caption = None
        
        for element in elements:
            el_type = type(element).__name__
            page_num = getattr(element.metadata, 'page_number', None)
            
            if page_num and page_num > summary["page_count"]:
                summary["page_count"] = page_num
            
            summary["element_counts"][el_type] = summary["element_counts"].get(el_type, 0) + 1
            
            if el_type in ["NarrativeText", "Text", "Title", "ListItem"]:
                content_elements.append(ContentElement(
                    element_type="text", content=element.text, page=page_num
                ))
                summary["has_text"] = True
                
            elif el_type == "FigureCaption":
                last_caption = element.text
                
            elif el_type == "Table":
                table_html = getattr(element.metadata, 'text_as_html', None)
                content_elements.append(ContentElement(
                    element_type="table",
                    content=self._table_to_markdown(element.text, table_html),
                    page=page_num, metadata={"html": table_html}
                ))
                summary["has_tables"] = True
                
            elif el_type == "Image":
                img_b64 = getattr(element.metadata, 'image_base64', None)
                is_chart = False
                caption = last_caption or ""
                
                if caption and any(w in caption.lower() for w in ["chart", "graph", "figure", "plot"]):
                    is_chart = True
                elif img_b64 and self.use_vision_for_charts:
                    is_chart = self._classify_image(img_b64)
                
                content_elements.append(ContentElement(
                    element_type="chart" if is_chart else "image",
                    content=caption, page=page_num,
                    base64_data=img_b64, metadata={"is_chart": is_chart}
                ))
                summary["has_images"] = True
                if is_chart: summary["has_charts"] = True
                last_caption = None
                
            elif el_type == "Formula":
                content_elements.append(ContentElement(
                    element_type="formula", content=element.text, page=page_num
                ))
                summary["has_formulas"] = True
        
        return content_elements, summary

    def _table_to_markdown(self, text: str, html: Optional[str]) -> str:
        """Convert table to markdown."""
        if not text: return ""
        lines = text.strip().split('\n')
        if len(lines) < 2: return f"[TABLE]\n{text}\n[/TABLE]"
        md_lines = [lines[0]]
        md_lines.append('|'.join(['---'] * len(lines[0].split('|'))))
        md_lines.extend(lines[1:])
        return f"[TABLE]\n{chr(10).join(md_lines)}\n[/TABLE]"
    
    def _classify_image(self, img_b64: str) -> bool:
        """Use Vision AI to classify image."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Is this a chart, graph, diagram? Reply YES or NO"},
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64[:1000]}..."}}
                    ]
                }],
                max_tokens=10,
            )
            return "YES" in response.choices[0].message.content.upper()
        except:
            return False

    def _fallback_parse(self, file_path: Path) -> Tuple[List[ContentElement], Dict]:
        """Simple fallback parser."""
        ext = file_path.suffix.lower()
        elements = []
        summary = {"has_text": False, "has_tables": False, "has_images": False, "has_charts": False, "page_count": 0, "element_counts": {}}
        
        # Implement minimal fallback for PDF/PyMuPDF usage if Unstructured fails
        if ext == '.pdf':
            try:
                import fitz
                doc = fitz.open(str(file_path))
                summary["page_count"] = len(doc)
                for i, page in enumerate(doc):
                    text = page.get_text()
                    if text.strip():
                        elements.append(ContentElement("text", text, page=i+1))
                        summary["has_text"] = True
                    # Basic image extraction
                    for img in page.get_images():
                        try:
                            xref = img[0]
                            base = doc.extract_image(xref)
                            b64 = base64.b64encode(base["image"]).decode('utf-8')
                            elements.append(ContentElement("image", "Extracted Image", page=i+1, base64_data=b64))
                            summary["has_images"] = True
                        except: pass
                doc.close()
                return elements, summary
            except: pass
        
        # Fallback text
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if content.strip():
                elements.append(ContentElement("text", content))
                summary["has_text"] = True
        except: pass
        return elements, summary


class KnowledgeBaseParser:
    """
    Manages Ingestion and Indexing (Heavy).
    """
    
    def __init__(self, data_dir: str = "kb_data", store_dir: str = "kb_store"):
        self.base_path = Path(__file__).parent
        self.data_path = self.base_path / data_dir
        self.store_path = self.base_path / store_dir
        self.parents_path = self.store_path / "parents"
        self.images_path = self.store_path / "images"
        
        for path in [self.data_path, self.store_path, self.parents_path, self.images_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        self.detector = ContentDetector()
        self.chunker = HierarchicalChunker()
        self.search_engine = HybridSearchEngine()
        
        self.index = {"documents": {}, "chunks": {}, "images": {}, "embeddings": {}}
        self._load_index()
    
    def _load_index(self):
        path = self.store_path / "index.json"
        if path.exists():
            try:
                with open(path, 'r') as f: self.index = json.load(f)
                chunks = [DocumentChunk(**c) for c in self.index.get("chunks", {}).values()]
                self.search_engine.build_bm25_index(chunks)
            except Exception as e: logger.error(f"Load failed: {e}")
            
    def _save_index(self):
        with open(self.store_path / "index.json", 'w') as f:
            json.dump(self.index, f, indent=2)

    def _generate_doc_id(self, file_path: Path) -> str:
        content = f"{file_path.name}_{file_path.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
        
    def ingest_all(self, force: bool = False) -> int:
        processed = 0
        for file_path in self.data_path.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith('.'):
                try:
                    self.ingest_document(file_path, force)
                    processed += 1
                except Exception as e: logger.error(f"Failed {file_path.name}: {e}")
        
        chunks = [DocumentChunk(**c) for c in self.index.get("chunks", {}).values()]
        self.search_engine.build_bm25_index(chunks)
        self._save_index()
        return processed

    def ingest_document(self, file_path: Path, force: bool = False):
        doc_id = self._generate_doc_id(file_path)
        if not force and doc_id in self.index.get("documents", {}):
            return
            
        logger.info(f"Ingesting: {file_path.name}")
        elements, summary = self.detector.detect_content(file_path)
        chunks = self.chunker.create_chunks(elements, doc_id, file_path.name)
        
        # Embed children
        child_chunks = [c for c in chunks if not c.is_parent]
        if child_chunks:
            embeddings = self.search_engine.embed_batch([c.text for c in child_chunks])
            for c, emb in zip(child_chunks, embeddings):
                c.embedding = emb
                self.index["embeddings"][c.chunk_id] = emb
        
        # Store chunks
        for c in chunks:
            self.index["chunks"][c.chunk_id] = c.__dict__
            if c.is_parent:
                (self.parents_path / f"{c.chunk_id}.txt").write_text(c.text, encoding='utf-8')
        
        # Store Doc Meta
        doc_meta = DocumentMeta(
            doc_id=doc_id, filename=file_path.name, summary=f"Parsed {len(elements)} elements",
            has_text=summary["has_text"], has_images=summary["has_images"],
            chunk_ids=[c.chunk_id for c in chunks]
        )
        self.index["documents"][doc_id] = doc_meta.__dict__
        
        # Save images
        for el in elements:
            if (el.element_type in ["image", "chart"]) and el.base64_data:
                img_id = f"{doc_id}_img_{hash(el.content or 'img')}"  # Simple hash
                # Decode and save to file
                try:
                    img_bytes = base64.b64decode(el.base64_data)
                    local_path = self.images_path / f"{img_id}.png"
                    with open(local_path, "wb") as f:
                        f.write(img_bytes)
                    
                    # Embed caption if exists
                    emb = []
                    if el.content:
                        emb = self.search_engine.embed_text(el.content)

                    self.index["images"][img_id] = {
                        "image_id": img_id, "doc_id": doc_id,
                        "filename": file_path.name, "caption": el.content,
                        "embedding": emb, "local_path": str(local_path),
                        "is_chart": el.metadata.get("is_chart", False)
                    }
                except Exception as e:
                    logger.warning(f"Failed to save image: {e}")

# Instantiate singleton
kb_parser = KnowledgeBaseParser()
