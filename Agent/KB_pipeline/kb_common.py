import logging
import json
import numpy as np
import openai
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from rank_bm25 import BM25Okapi
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("kb-common")

# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ContentElement:
    """Represents a detected content element from a document."""
    element_type: str  # "text", "table", "image", "chart", "formula"
    content: str       # Text content or image caption
    page: Optional[int] = None
    base64_data: Optional[str] = None  # For images
    metadata: Dict = field(default_factory=dict)


@dataclass
class DocumentChunk:
    """A chunk of document content with embedding."""
    chunk_id: str
    doc_id: str
    filename: str
    text: str
    embedding: List[float] = field(default_factory=list)
    is_parent: bool = True
    parent_id: Optional[str] = None
    page_numbers: List[int] = field(default_factory=list)
    has_images: bool = False
    image_ids: List[str] = field(default_factory=list)


@dataclass
class ImageData:
    """Extracted image with caption and embedding."""
    image_id: str
    doc_id: str
    filename: str
    caption: str
    embedding: List[float] = field(default_factory=list)
    page: Optional[int] = None
    local_path: Optional[str] = None
    is_chart: bool = False


@dataclass
class DocumentMeta:
    """Document-level metadata."""
    doc_id: str
    filename: str
    summary: str
    has_text: bool = False
    has_tables: bool = False
    has_images: bool = False
    has_charts: bool = False
    chunk_ids: List[str] = field(default_factory=list)
    image_ids: List[str] = field(default_factory=list)
    cross_refs: List[str] = field(default_factory=list)
    processed_at: str = ""


@dataclass
class QueryResult:
    """Result from a knowledge base query."""
    text: str
    sources: List[str]
    images: List[str] = field(default_factory=list)
    confidence: float = 0.0


# ============================================================
# CHUNKER
# ============================================================

class HierarchicalChunker:
    """
    Creates parent-child chunk hierarchy.
    - Parents: Large chunks (~2000 tokens) for context
    - Children: Small chunks (~256 tokens) for search
    """
    
    def __init__(self, parent_size: int = 2000, child_size: int = 256, overlap: int = 50):
        self.parent_size = parent_size
        self.child_size = child_size
        self.overlap = overlap
    
    def create_chunks(
        self, 
        elements: List[ContentElement], 
        doc_id: str, 
        filename: str
    ) -> List[DocumentChunk]:
        """Create hierarchical chunks from content elements."""
        
        # Combine text elements into full text
        text_parts = []
        current_pages = []
        
        for el in elements:
            if el.element_type in ["text", "table", "formula"]:
                text_parts.append(el.content)
                if el.page:
                    current_pages.append(el.page)
        
        full_text = "\n\n".join(text_parts)
        
        # Create parent chunks
        parent_chunks = self._split_text(full_text, self.parent_size, self.overlap)
        
        chunks = []
        for i, parent_text in enumerate(parent_chunks):
            parent_id = f"{doc_id}_p{i:03d}"
            
            # Create parent chunk
            parent_chunk = DocumentChunk(
                chunk_id=parent_id,
                doc_id=doc_id,
                filename=filename,
                text=parent_text,
                is_parent=True,
                page_numbers=list(set(current_pages)) if current_pages else []
            )
            chunks.append(parent_chunk)
            
            # Create child chunks (for search indexing)
            child_texts = self._split_text(parent_text, self.child_size, self.overlap // 2)
            for j, child_text in enumerate(child_texts):
                child_chunk = DocumentChunk(
                    chunk_id=f"{parent_id}_c{j:03d}",
                    doc_id=doc_id,
                    filename=filename,
                    text=child_text,
                    is_parent=False,
                    parent_id=parent_id
                )
                chunks.append(child_chunk)
        
        return chunks
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Split text into chunks with overlap."""
        if not text:
            return []
        
        # Approximate tokens as words * 1.3
        words = text.split()
        target_words = int(chunk_size / 1.3)
        overlap_words = int(overlap / 1.3)
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = min(start + target_words, len(words))
            chunk = ' '.join(words[start:end])
            chunks.append(chunk)
            start = end - overlap_words
            if start >= len(words) - overlap_words:
                break
        
        return chunks


# ============================================================
# EMBEDDINGS & SEARCH ENGINE
# ============================================================

class HybridSearchEngine:
    """
    Hybrid search with dense (OpenAI) + sparse (BM25) + RRF fusion.
    """
    
    def __init__(self):
        self.openai_client = openai.OpenAI()
        self.bm25_index = None
        self.corpus_tokens = []
        self.chunk_lookup = {}
    
    def embed_text(self, text: str) -> List[float]:
        """Generate OpenAI embedding for text."""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:8000]  # Truncate to max length
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return [0.0] * 1536
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple texts."""
        embeddings = []
        batch_size = 20
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",
                    input=[t[:8000] for t in batch]
                )
                embeddings.extend([d.embedding for d in response.data])
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                embeddings.extend([[0.0] * 1536] * len(batch))
        
        return embeddings
    
    def build_bm25_index(self, chunks: List[DocumentChunk]):
        """Build BM25 sparse index."""
        self.corpus_tokens = []
        self.chunk_lookup = {}
        
        for chunk in chunks:
            tokens = chunk.text.lower().split()
            self.corpus_tokens.append(tokens)
            self.chunk_lookup[len(self.corpus_tokens) - 1] = chunk.chunk_id
        
        if self.corpus_tokens:
            self.bm25_index = BM25Okapi(self.corpus_tokens)
    
    def search_dense(
        self, 
        query_embedding: List[float], 
        all_embeddings: Dict[str, List[float]], 
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """Dense cosine similarity search."""
        query_vec = np.array(query_embedding)
        scores = []
        
        for chunk_id, embedding in all_embeddings.items():
            emb_vec = np.array(embedding)
            # Cosine similarity
            similarity = np.dot(query_vec, emb_vec) / (
                np.linalg.norm(query_vec) * np.linalg.norm(emb_vec) + 1e-8
            )
            scores.append((chunk_id, float(similarity)))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def search_sparse(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """BM25 sparse keyword search."""
        if not self.bm25_index:
            return []
        
        query_tokens = query.lower().split()
        scores = self.bm25_index.get_scores(query_tokens)
        
        results = []
        for idx, score in enumerate(scores):
            if idx in self.chunk_lookup:
                results.append((self.chunk_lookup[idx], float(score)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def rrf_fusion(
        self, 
        dense_results: List[Tuple[str, float]], 
        sparse_results: List[Tuple[str, float]], 
        k: int = 60
    ) -> List[Tuple[str, float]]:
        """Reciprocal Rank Fusion to combine dense and sparse results."""
        rrf_scores = {}
        
        # Add dense scores
        for rank, (chunk_id, _) in enumerate(dense_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        
        # Add sparse scores
        for rank, (chunk_id, _) in enumerate(sparse_results):
            rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + 1 / (k + rank + 1)
        
        # Sort by combined score
        results = [(chunk_id, score) for chunk_id, score in rrf_scores.items()]
        results.sort(key=lambda x: x[1], reverse=True)
        
        return results
