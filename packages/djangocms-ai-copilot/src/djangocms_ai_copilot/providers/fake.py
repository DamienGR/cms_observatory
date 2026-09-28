from .base import Completion


class FakeProvider:
    """Deterministic provider for tests and offline development.

    Queue answers in ``FakeProvider.responses``; without any, it echoes the last
    paragraph of the prompt prefixed with ``[fake]``. Every call is recorded in
    ``FakeProvider.calls``.
    """

    responses: list[str] = []
    calls: list[dict] = []

    def __init__(self, *, model="fake", **kwargs):
        self.model = "fake"

    def complete(self, *, system, prompt, images=(), max_tokens=None):
        FakeProvider.calls.append({"system": system, "prompt": prompt, "images": list(images)})
        if FakeProvider.responses:
            text = FakeProvider.responses.pop(0)
        else:
            text = "[fake] " + prompt.rsplit("\n\n", 1)[-1]
        return Completion(text=text, model=self.model, input_tokens=len(prompt) // 4, output_tokens=len(text) // 4)

    @classmethod
    def reset(cls):
        cls.responses = []
        cls.calls = []
