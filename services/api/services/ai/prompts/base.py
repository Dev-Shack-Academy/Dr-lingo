"""
Base Prompt Classes

Provides abstract base classes for all prompt types with version control.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any


class PromptVersion(str, Enum):
    """Prompt version identifiers."""

    V1 = "v1"
    V2 = "v2"
    LATEST = "latest"


@dataclass
class PromptMetadata:
    """Metadata for a prompt."""

    version: PromptVersion
    name: str
    description: str
    author: str = "system"
    tags: list[str] | None = None


class BasePrompt(ABC):
    """
    Abstract base class for all prompts.

    Provides a consistent interface for prompt generation with:
    - Version tracking
    - Metadata
    - Template rendering
    """

    def __init__(self):
        self._metadata = self._get_metadata()

    @property
    def version(self) -> PromptVersion:
        """Get prompt version."""
        return self._metadata.version

    @property
    def name(self) -> str:
        """Get prompt name."""
        return self._metadata.name

    @property
    def metadata(self) -> PromptMetadata:
        """Get full prompt metadata."""
        return self._metadata

    @abstractmethod
    def _get_metadata(self) -> PromptMetadata:
        """Define prompt metadata. Must be implemented by subclasses."""
        pass

    @abstractmethod
    def render(self, **kwargs: Any) -> str:
        """
        Render the prompt with given parameters.

        Args:
            **kwargs: Parameters to fill in the prompt template

        Returns:
            Rendered prompt string
        """
        pass

    def __str__(self) -> str:
        return f"{self.name} ({self.version.value})"

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} version={self.version.value}>"
