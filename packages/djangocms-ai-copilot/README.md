# djangocms-ai-copilot

An AI copilot for django CMS 5.1 editors. It writes drafts, never publishes.

- **Summary fields**: writes a page's meta description (or any field an app registers) from its content.
- **Rewrite**: "Rewrite with AI…" in the context menu of text plugins, with a preview before applying.
- **Translation**: creates a new language version of a page, as a draft, with translated text plugins.
- **Alt texts**: fills missing alt texts of django-filer images (`manage.py copilot_alt_texts`).
- **Audit log**: every call is logged with user, target object and token usage.

Every write goes through django CMS permissions and, when djangocms-versioning is installed,
only to draft versions that are not locked by someone else.

## Installation

```bash
pip install djangocms-ai-copilot
```

```python
INSTALLED_APPS = [..., "djangocms_ai_copilot"]
DJANGOCMS_AI_COPILOT = {"MODEL": "claude-sonnet-5"}  # the SDK reads ANTHROPIC_API_KEY
```

Run `python manage.py migrate`, then give editors the "Can use the AI copilot" permission.
Long jobs (translations, alt texts) are Django tasks on the `llm` queue.

## Let the copilot write your own fields

```python
# myapp/cms_config.py
from cms.app_base import CMSAppConfig

class MyAppCMSConfig(CMSAppConfig):
    djangocms_ai_copilot_enabled = True
    copilot_summary_fields = {ArticleContent: "teaser"}
```

## Other providers

Set `DJANGOCMS_AI_COPILOT["PROVIDER"]` to the dotted path of a class implementing
`complete(system=..., prompt=..., images=..., max_tokens=...)` and returning a `Completion`.
`djangocms_ai_copilot.providers.fake.FakeProvider` is available for tests.

## Tests

```bash
pip install -e ".[test]" && pytest
```
