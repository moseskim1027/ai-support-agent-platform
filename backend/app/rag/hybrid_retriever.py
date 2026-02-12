"""Hybrid search retriever combining dense and sparse search"""

import logging
from typing import Dict, List, Optional, Tuple

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Hybrid retriever combining dense (vector) and sparse (BM25) search

    Uses Reciprocal Rank Fusion (RRF) to combine results from both methods.
    """

    def __init__(
        self,
        qdrant_client: QdrantClient,
        collection_name: str,
        embeddings: GoogleGenerativeAIEmbeddings,
    ):
        """
        Initialize hybrid retriever

        Args:
            qdrant_client: Qdrant client instance
            collection_name: Name of Qdrant collection
            embeddings: Google Gemini embeddings instance
        """
        self.qdrant = qdrant_client
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.bm25_index: Optional[BM25Okapi] = None
        self.documents: List[Dict] = []

    def build_bm25_index(self, documents: List[Dict]):
        """
        Build BM25 index from documents

        Args:
            documents: List of document dictionaries with 'text' field
        """
        self.documents = documents

        # Tokenize documents for BM25
        tokenized_corpus = [self._tokenize(doc.get("text", "")) for doc in documents]

        # Build BM25 index
        self.bm25_index = BM25Okapi(tokenized_corpus)
        logger.info(f"Built BM25 index with {len(documents)} documents")

    def _tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for BM25

        Args:
            text: Text to tokenize

        Returns:
            List of tokens (lowercase words)
        """
        # Simple word tokenization (can be enhanced with better tokenizers)
        return text.lower().split()

    async def dense_search(
        self, query: str, top_k: int = 10, score_threshold: float = 0.7
    ) -> List[Tuple[Dict, float]]:
        """
        Perform dense vector search

        Args:
            query: Search query
            top_k: Number of results to return
            score_threshold: Minimum similarity score

        Returns:
            List of (document, score) tuples
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query)

            # Search in Qdrant
            results = self.qdrant.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
            )

            # Filter by score and format results
            documents = [
                (hit.payload, hit.score) for hit in results if hit.score >= score_threshold
            ]

            logger.debug(f"Dense search returned {len(documents)} results")
            return documents

        except Exception as e:
            logger.error(f"Error in dense search: {e}", exc_info=True)
            return []

    def sparse_search(self, query: str, top_k: int = 10) -> List[Tuple[Dict, float]]:
        """
        Perform sparse BM25 search

        Args:
            query: Search query
            top_k: Number of results to return

        Returns:
            List of (document, score) tuples
        """
        if not self.bm25_index:
            logger.warning("BM25 index not built, skipping sparse search")
            return []

        try:
            # Tokenize query
            tokenized_query = self._tokenize(query)

            # Get BM25 scores
            scores = self.bm25_index.get_scores(tokenized_query)

            # Get top-k indices
            top_indices = scores.argsort()[-top_k:][::-1]

            # Format results with normalized scores
            max_score = scores[top_indices[0]] if len(top_indices) > 0 else 1.0
            documents = [
                (
                    self.documents[idx],
                    float(scores[idx] / max_score) if max_score > 0 else 0.0,
                )
                for idx in top_indices
                if scores[idx] > 0
            ]

            logger.debug(f"Sparse search returned {len(documents)} results")
            return documents

        except Exception as e:
            logger.error(f"Error in sparse search: {e}", exc_info=True)
            return []

    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        rrf_k: int = 60,
    ) -> List[Tuple[Dict, float]]:
        """
        Perform hybrid search using Reciprocal Rank Fusion (RRF)

        Args:
            query: Search query
            top_k: Number of final results to return
            dense_weight: Weight for dense search (0-1)
            sparse_weight: Weight for sparse search (0-1)
            rrf_k: RRF constant (typically 60)

        Returns:
            List of (document, score) tuples sorted by fused score
        """
        # Get results from both methods
        dense_results = await self.dense_search(query, top_k=top_k * 2)
        sparse_results = self.sparse_search(query, top_k=top_k * 2)

        # If one method returns no results, fall back to the other
        if not dense_results and not sparse_results:
            logger.warning("No results from either search method")
            return []
        if not dense_results:
            logger.info("Using only sparse search results")
            return sparse_results[:top_k]
        if not sparse_results:
            logger.info("Using only dense search results")
            return dense_results[:top_k]

        # Reciprocal Rank Fusion (RRF)
        # Score = sum(weight_i / (k + rank_i)) for each method
        doc_scores: Dict[str, float] = {}
        doc_objects: Dict[str, Dict] = {}

        # Process dense results
        for rank, (doc, score) in enumerate(dense_results, start=1):
            doc_id = doc.get("text", "")[:50]  # Use first 50 chars as ID
            doc_scores[doc_id] = dense_weight / (rrf_k + rank)
            doc_objects[doc_id] = doc

        # Process sparse results
        for rank, (doc, score) in enumerate(sparse_results, start=1):
            doc_id = doc.get("text", "")[:50]
            if doc_id in doc_scores:
                # Document found in both methods - add scores
                doc_scores[doc_id] += sparse_weight / (rrf_k + rank)
            else:
                doc_scores[doc_id] = sparse_weight / (rrf_k + rank)
                doc_objects[doc_id] = doc

        # Sort by fused score
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)

        # Return top-k results
        results = [(doc_objects[doc_id], score) for doc_id, score in sorted_docs[:top_k]]

        logger.info(
            f"Hybrid search returned {len(results)} results "
            f"(dense: {len(dense_results)}, sparse: {len(sparse_results)})"
        )

        return results

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_hybrid: bool = True,
    ) -> List[str]:
        """
        Main retrieval method

        Args:
            query: Search query
            top_k: Number of results to return
            use_hybrid: Whether to use hybrid search (True) or just dense (False)

        Returns:
            List of document texts
        """
        if use_hybrid:
            results = await self.hybrid_search(query, top_k=top_k)
        else:
            results = await self.dense_search(query, top_k=top_k)

        return [doc.get("text", "") for doc, score in results]
