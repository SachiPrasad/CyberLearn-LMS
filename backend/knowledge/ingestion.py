import json
import os
import re
import math
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class DocumentMetadata(BaseModel):
    document_id: str
    course_id: str
    course_name: str
    module_id: str
    module_name: str
    document_type: str
    title: str
    content: str
    keywords: List[str] = Field(default_factory=list)
    source: str
    version: str = "1.0"
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class IngestionPipeline:
    def __init__(self, data_file: Optional[str] = None):
        if data_file is None:
            base_dir = os.path.dirname(__file__)
            data_file = os.path.join(base_dir, "documents.json")
        self.data_file = data_file
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.idf: Dict[str, float] = {}
        self.doc_vectors: List[Dict[str, float]] = []
        self.load_and_index()

    def tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = re.findall(r'[a-z0-9_\-\.\/]+', text)
        return tokens

    def load_and_index(self):
        """Loads documents from JSON, validates schema, and computes index."""
        if not os.path.exists(self.data_file):
            logger.warning(f"Knowledge data file not found: {self.data_file}")
            return

        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
            validated_docs = []
            for item in raw_data:
                try:
                    doc = DocumentMetadata(**item)
                    validated_docs.append(doc.model_dump())
                except Exception as ve:
                    logger.error(f"Validation error for document {item.get('document_id', 'unknown')}: {ve}")

            self.documents = validated_docs
            self._build_index()
            logger.info(f"Ingestion Pipeline: Loaded and indexed {len(self.documents)} verified CyberLearn documents.")
        except Exception as e:
            logger.error(f"Failed to load documents: {e}", exc_info=True)

    def _build_index(self):
        """Computes vocabulary, inverse document frequencies (IDF), and document TF-IDF vectors."""
        n_docs = len(self.documents)
        if n_docs == 0:
            return

        doc_frequencies: Dict[str, int] = {}
        tokenized_docs = []

        for doc in self.documents:
            # Combine title, keywords, and content for rich indexing
            full_text = f"{doc['title']} {' '.join(doc['keywords'])} {doc['content']} {doc['course_name']} {doc['module_name']}"
            tokens = self.tokenize(full_text)
            tokenized_docs.append(tokens)
            
            unique_terms = set(tokens)
            for term in unique_terms:
                doc_frequencies[term] = doc_frequencies.get(term, 0) + 1

        self.idf = {
            term: math.log((n_docs + 1) / (df + 1)) + 1.0
            for term, df in doc_frequencies.items()
        }

        # Build sparse unit-normalized TF-IDF vector for each document
        self.doc_vectors = []
        for tokens in tokenized_docs:
            tf: Dict[str, float] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1.0
            
            vec: Dict[str, float] = {}
            norm_sq = 0.0
            for term, count in tf.items():
                tfidf_val = count * self.idf.get(term, 1.0)
                vec[term] = tfidf_val
                norm_sq += tfidf_val ** 2
            
            norm = math.sqrt(norm_sq) if norm_sq > 0 else 1.0
            unit_vec = {k: v / norm for k, v in vec.items()}
            self.doc_vectors.append(unit_vec)

    def get_all_documents(self) -> List[Dict[str, Any]]:
        return self.documents

    def add_document(self, doc_data: Dict[str, Any]):
        """Dynamically add new document, validate schema, and rebuild index."""
        doc = DocumentMetadata(**doc_data)
        self.documents.append(doc.model_dump())
        self._build_index()
        # Persist to JSON
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.documents, f, indent=2)

# Global singleton
kb_pipeline = IngestionPipeline()
