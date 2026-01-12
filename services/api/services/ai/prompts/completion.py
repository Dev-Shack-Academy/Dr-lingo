"""
Completion Prompts

Simple prompts for text completion/generation tasks (RAG queries).
These don't need versioning - they're generic "answer using context" prompts.
"""

from typing import Any

from .base import BasePrompt, PromptMetadata, PromptVersion


class CompletionPrompt(BasePrompt):
    """Basic completion prompt - passthrough."""

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V1,
            name="completion_basic",
            description="Basic completion prompt (passthrough)",
            tags=["completion", "generation"],
        )

    def render(self, prompt: str, **kwargs: Any) -> str:
        return prompt


class CompletionWithContextPrompt(BasePrompt):
    """Completion prompt with RAG context."""

    def _get_metadata(self) -> PromptMetadata:
        return PromptMetadata(
            version=PromptVersion.V1,
            name="completion_with_context",
            description="Context-aware completion prompt for RAG",
            tags=["completion", "generation", "context", "rag"],
        )

    def render(self, prompt: str, context: str, **kwargs: Any) -> str:
        return f"""<|system|>
You are a medical knowledge assistant. Answer the question using ONLY the provided context.
If the answer is not in the context, say so. Be concise and accurate.
<|end|>

<|user|>
<context>
{context}
</context>

<question>
{prompt}
</question>
<|end|>

<|assistant|>
"""


def get_completion_prompt() -> CompletionPrompt:
    """Get the completion prompt."""
    return CompletionPrompt()


def get_completion_with_context_prompt() -> CompletionWithContextPrompt:
    """Get the context-aware completion prompt."""
    return CompletionWithContextPrompt()
