"""
KB Searcher
===========
Lightweight Knowledge Base Searcher.
Does NOT include parsing dependencies (unstructured, pymupdf).
"""

import logging
import json
import openai
from pathlib import Path
from typing import List, Dict, Optional

# Import common components
try:
    from .kb_common import HybridSearchEngine, DocumentChunk, QueryResult
except ImportError:
    from kb_common import HybridSearchEngine, DocumentChunk, QueryResult

logger = logging.getLogger("kb-searcher")

class KnowledgeBaseSearcher:
    """
    Manages Knowledge Base Retrieval (Search Only).
    """
    
    def __init__(
        self,
        data_dir: str = "kb_data",
        store_dir: str = "kb_store",
    ):
        self.base_path = Path(__file__).parent
        self.data_path = self.base_path / data_dir
        self.store_path = self.base_path / store_dir
        self.parents_path = self.store_path / "parents"
        self.images_path = self.store_path / "images"
        
        # Initialize Engine
        self.search_engine = HybridSearchEngine()
        
        # Index data
        self.index = {
            "documents": {},
            "chunks": {},
            "images": {},
            "embeddings": {},
        }
        
        # Load existing index
        self._load_index()
    
    def _load_index(self):
        """Load index from disk."""
        index_path = self.store_path / "index.json"
        if index_path.exists():
            try:
                with open(index_path, 'r') as f:
                    self.index = json.load(f)
                logger.info(f"Loaded index with {len(self.index.get('documents', []))} documents")
                
                # Rebuild BM25 index
                chunks = [DocumentChunk(**c) for c in self.index.get("chunks", {}).values()]
                self.search_engine.build_bm25_index(chunks)
                
            except Exception as e:
                logger.error(f"Failed to load index: {e}")
        else:
            logger.warning(f"Index not found at {index_path}")
    
    def get_stats(self) -> Dict:
        """Get knowledge base statistics."""
        return {
            "documents": len(self.index.get("documents", {})),
            "chunks": len(self.index.get("chunks", {})),
            "images": len(self.index.get("images", {})),
        }

    async def _expand_query(self, query: str) -> List[str]:
        """Generate variations of the query to improve search recall."""
        try:
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a query expansion assistant. Generate 3 short, keyword-focused variations of the user's query to help find relevant information in a document database. Return only the 3 variations separated by newlines."},
                    {"role": "user", "content": query}
                ],
                max_tokens=60,
                temperature=0.5,
            )
            variations = response.choices[0].message.content.strip().split('\n')
            return [v.strip() for v in variations if v.strip()]
        except Exception as e:
            logger.warning(f"Query expansion failed: {e}")
            return []

    async def query(self, text: str, top_k: int = 3, include_images: bool = True) -> QueryResult:
        """Alias for retrieve()."""
        return await self.retrieve(text, top_k, include_images)

    async def retrieve(self, text: str, top_k: int = 3, include_images: bool = True) -> QueryResult:
        """
        Retrieves relevant context (chunks + images) using Hybrid Search.
        """
        # 1. Expand Query
        variations = await self._expand_query(text)
        search_queries = [text] + variations
        logger.info(f"Expanded query '{text}' to: {variations}")
        
        all_fused = []
        
        # 2. Hybrid Search...
        for q in search_queries:
            q_embedding = self.search_engine.embed_text(q)
            dense_results = self.search_engine.search_dense(q_embedding, self.index.get("embeddings", {}), top_k * 2)
            sparse_results = self.search_engine.search_sparse(q, top_k * 2)
            fused = self.search_engine.rrf_fusion(dense_results, sparse_results)[:top_k]
            all_fused.extend(fused)
        
        # Deduplicate
        chunk_scores = {}
        for chunk_id, score in all_fused:
            chunk_scores[chunk_id] = max(chunk_scores.get(chunk_id, 0), score)
        
        final_results = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)[:top_k+2]
            
        if not final_results:
            return QueryResult(
                text="No relevant information found in the knowledge base.",
                sources=[]
            )
        
        # 3. Build Context
        context_parts = []
        sources = set()
        
        for chunk_id, score in final_results:
            chunk_data = self.index["chunks"].get(chunk_id, {})
            parent_id = chunk_data.get("parent_id") or chunk_id
            parent_file = self.parents_path / f"{parent_id}.txt"
            
            if parent_file.exists():
                parent_text = parent_file.read_text(encoding='utf-8')
            else:
                parent_text = chunk_data.get("text", "")
            
            doc_id = chunk_data.get("doc_id")
            doc_meta = self.index.get("documents", {}).get(doc_id, {})
            summary = doc_meta.get("summary", "")
            filename = doc_meta.get("filename", "Unknown")
            page_nums = chunk_data.get("page_numbers", [])
            page_info = f" (Pages: {', '.join(map(str, page_nums))})" if page_nums else ""
            
            # Format: [Filename (Pages: 1)] \n Content...
            context = f"[{filename}{page_info}]\n"
            if summary:
                context += f"Summary: {summary}\n\n"
            context += parent_text
            
            context_parts.append(context)
            
            if page_nums:
                sources.add(f"{filename} (p.{','.join(map(str, page_nums))})")
            else:
                sources.add(filename)
        
        # 4. Get Images
        image_paths = []
        if include_images:
            q_emb = self.search_engine.embed_text(text)
            image_results = self.search_engine.search_dense(
                q_emb,
                {img["image_id"]: img["embedding"] for img in self.index.get("images", {}).values() if img.get("embedding")},
                top_k=2
            )
            for img_id, _ in image_results:
                img_data = self.index.get("images", {}).get(img_id, {})
                if img_data.get("local_path"):
                    image_paths.append(img_data["local_path"])
        
        # Return RAW CONTEXT
        final_context_text = "\n\n---\n\n".join(context_parts)
        
        return QueryResult(
            text=final_context_text,
            sources=list(sources),
            images=image_paths,
            confidence=all_fused[0][1] if all_fused else 0.0
        )

# Instantiate singleton
kb_searcher = KnowledgeBaseSearcher()
