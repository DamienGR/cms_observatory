from dataclasses import dataclass
from typing import Protocol


class ProviderError(Exception):
    """Raised when the LLM provider fails (network, quota, invalid answer...)."""


@dataclass
class Completion:
    text: str
    model: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider(Protocol):
    model: str

    def complete(
        self,
        *,
        system: str,
        prompt: str,
        images: list[tuple[bytes, str]] = (),
        max_tokens: int | None = None,
    ) -> Completion:
        """Return the model's answer. ``images`` holds (raw bytes, media type) pairs."""
        ...
