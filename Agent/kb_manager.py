import logging
import os
from pathlib import Path
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.core.node_parser import SentenceSplitter

logger = logging.getLogger("kb-manager")

class KnowledgeBaseManager:
    def __init__(self, data_dir="kb_data", storage_dir="kb_store"):
        self.base_path = Path(__file__).parent
        self.data_path = self.base_path / data_dir
        self.storage_path = self.base_path / storage_dir
        self.index = None
        self.query_engine = None
        
        # Configure global settings for LlamaIndex
        # Optimize for "Long Documents" with better chunking
        Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)

    def load_or_create_index(self):
        """Loads existing index from storage or creates a new one from data directory."""
        if self.storage_path.exists() and any(self.storage_path.iterdir()):
            logger.info(f"Loading existing index from {self.storage_path}")
            storage_context = StorageContext.from_defaults(persist_dir=str(self.storage_path))
            self.index = load_index_from_storage(storage_context)
        else:
            logger.info(f"Creating new index from data at {self.data_path}")
            if not self.data_path.exists():
                self.data_path.mkdir(parents=True, exist_ok=True)
                # Create a placeholder file if empty
                with open(self.data_path / "README.txt", "w") as f:
                    f.write("Place your long documents, text, and media links here.")
            
            documents = SimpleDirectoryReader(str(self.data_path)).load_data()
            self.index = VectorStoreIndex.from_documents(documents)
            self.index.storage_context.persist(persist_dir=str(self.storage_path))
        
        self.query_engine = self.index.as_query_engine(
            similarity_top_k=3,
            # Ensure we get enough context for long doc answers
        )
        return self.index

    async def query(self, text: str) -> str:
        """Query the knowledge base and return a response."""
        if not self.query_engine:
            self.load_or_create_index()
        
        try:
            response = await self.query_engine.aquery(text)
            response_text = str(response)
            
            # Logic to handle "Multimodal Links"
            # If the response text contains patterns like [IMAGE: url] or [VIDEO: url],
            # we can extract them if the agent needs to handle them specifically.
            # For now, we return the text as is, assuming the agent will speak it.
            
            return response_text
        except Exception as e:
            logger.error(f"Query error: {e}")
            return "I encountered an error while searching my knowledge base."

# Singleton instance for easy access
kb_manager = KnowledgeBaseManager()
