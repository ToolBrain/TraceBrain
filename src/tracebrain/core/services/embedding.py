"""
Embedding service providers for TraceBrain.

Provides a model-agnostic interface with a local-first default.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
import logging

from tracebrain.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(ABC):
    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        raise NotImplementedError


class LocalEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self) -> None:
        self._model = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
        except Exception as exc:
            logger.warning("Failed to load local embedding model: %s", exc)
            self._model = None

    def get_embedding(self, text: str) -> List[float]:
        if not self._model:
            return []
        try:
            embedding = self._model.encode([text], normalize_embeddings=True)
            return embedding[0].tolist()
        except Exception as exc:
            logger.warning("Embedding generation failed: %s", exc)
            return []


class CloudEmbeddingProvider(BaseEmbeddingProvider):
    def __init__(self, provider: str) -> None:
        self.provider = provider.lower()

    def _resolve_model(self) -> str:
        if self.provider == "openai":
            if settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2":
                return "text-embedding-3-small"
        if self.provider == "gemini":
            if settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2":
                return "text-embedding-004"
        return settings.EMBEDDING_MODEL

    def _openai_embedding(self, text: str) -> List[float]:
        if not settings.EMBEDDING_API_KEY:
            logger.warning("Missing EMBEDDING_API_KEY for OpenAI embeddings")
            return []
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.EMBEDDING_API_KEY, base_url=settings.EMBEDDING_BASE_URL)
            response = client.embeddings.create(
                model=self._resolve_model(),
                input=text,
            )
            return response.data[0].embedding
        except Exception as exc:
            logger.warning("OpenAI embedding failed: %s", exc)
            return []

    def _gemini_embedding(self, text: str) -> List[float]:
        if not settings.EMBEDDING_API_KEY:
            logger.warning("Missing EMBEDDING_API_KEY for Gemini embeddings")
            return []
        try:
            import google.generativeai as genai

            genai.configure(api_key=settings.EMBEDDING_API_KEY)
            response = genai.embed_content(
                model=self._resolve_model(),
                content=text,
                task_type="retrieval_query",
            )
            return response.get("embedding", [])
        except Exception as exc:
            logger.warning("Gemini embedding failed: %s", exc)
            return []

    def get_embedding(self, text: str) -> List[float]:
        if self.provider == "openai":
            return self._openai_embedding(text)
        if self.provider == "gemini":
            return self._gemini_embedding(text)
        logger.warning("Unknown embedding provider '%s'", self.provider)
        return []


class NoopEmbeddingProvider(BaseEmbeddingProvider):
    def get_embedding(self, text: str) -> List[float]:
        return []


class EmbeddingFactory:
    @staticmethod
    def create() -> BaseEmbeddingProvider:
        provider = (settings.EMBEDDING_PROVIDER or "local").lower()
        if provider == "local":
            return LocalEmbeddingProvider()
        if provider in {"openai", "gemini"}:
            return CloudEmbeddingProvider(provider)
        if provider == "cloud":
            return CloudEmbeddingProvider("openai")
        return NoopEmbeddingProvider()
