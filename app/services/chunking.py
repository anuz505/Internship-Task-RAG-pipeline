"""
Hey, i have only utilized two chunking strategies.
we could use either of those we have Fixed length chunking and Semantic Chunking.
Both common and Easy methods.
"""

from abc import ABC, abstractmethod
from app.models.schemas import Semantic_Chunk_Config, Fixed_length_Chunk_Config
from app.logger import logger
from typing import Protocol, List
import re


class ChunkerProtocal(Protocol):
    def chunk(self, text: str) -> List[str]: ...


class BaseChunker(ABC):
    @abstractmethod
    def chunk(self, text: str) -> List[str]:
        pass


class Fixed_Length_Chunker(BaseChunker):
    def __init__(self, config: Fixed_length_Chunk_Config):
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start += self.chunk_size - self.chunk_overlap
            if self.chunk_overlap >= self.chunk_size:
                break

        logger.info(f"Fixed length chunking done | Created {len(chunks)}")
        return chunks


class Semantic_Chunker(BaseChunker):
    def __init__(self, config: Semantic_Chunk_Config):
        self.split_by = config.split_by
        self.max_chunk_size = config.max_chunk_size

    def chunk(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []

        if self.split_by == "sentence":
            return self._chunk_by_sentence(text)
        if self.split_by == "paragraph":
            return self._chunk_by_paragraph(text)

        return []

    def _chunk_by_sentence(self, text: str) -> List[str]:

        sentences = re.split(r"(?<=[.!?])\s+", text)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            if (
                current_chunk
                and len(current_chunk) + len(sentence) + 1 > self.max_chunk_size
            ):
                chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk = f"{current_chunk} {sentence}".strip()

        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"Semantic sentence chunking created {len(chunks)} chunks")
        return chunks

    def _chunk_by_paragraph(self, text: str) -> List[str]:
        """
        Chunk text by paragraphs, respecting max chunk size.

        Args:
            text: Input text

        Returns:
            List of paragraph-based chunks
        """
        paragraphs = re.split(r"\n\s*\n", text)

        chunks = []
        current_chunk = ""

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            if len(paragraph) > self.max_chunk_size:
                sentence_chunks = self._chunk_by_sentence(paragraph)

                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = ""

                chunks.extend(sentence_chunks)
            else:
                if (
                    current_chunk
                    and len(current_chunk) + len(paragraph) + 2 > self.max_chunk_size
                ):
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    current_chunk = (
                        f"{current_chunk}\n\n{paragraph}".strip()
                        if current_chunk
                        else paragraph
                    )

        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.info(f"Semantic paragraph chunking created {len(chunks)} chunks")
        return chunks


def get_chunker(
    config: Fixed_length_Chunk_Config | Semantic_Chunk_Config,
) -> BaseChunker:
    if isinstance(config, Fixed_length_Chunk_Config):
        return Fixed_Length_Chunker(config)
    elif isinstance(config, Semantic_Chunk_Config):
        return Semantic_Chunker(config)
    else:
        raise ValueError(f"Unknown chunking config type: {type(config)}")
