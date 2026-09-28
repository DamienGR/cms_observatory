import base64

from .base import Completion, ProviderError


class AnthropicProvider:
    def __init__(self, *, model, api_key=None, max_tokens=1024, timeout=60):
        import anthropic

        self.model = model
        self.max_tokens = max_tokens
        credentials = {"api_key": api_key} if api_key else {}  # otherwise: ANTHROPIC_API_KEY
        self.client = anthropic.Anthropic(timeout=timeout, **credentials)
        self._errors = (anthropic.APIError,)

    def complete(self, *, system, prompt, images=(), max_tokens=None):
        content = [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": media_type, "data": base64.b64encode(data).decode()},
            }
            for data, media_type in images
        ]
        content.append({"type": "text", "text": prompt})
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": content}],
            )
        except self._errors as exc:
            raise ProviderError(str(exc)) from exc
        return Completion(
            text="".join(block.text for block in response.content if block.type == "text"),
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
