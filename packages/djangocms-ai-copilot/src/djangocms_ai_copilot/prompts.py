"""System prompts. The user content always comes last, after a blank line."""

SUMMARY_FIELD = (
    "You write the '{field}' field of a web page for a content management system. "
    "Write in {language}. Use at most {max_length} characters. Be factual and specific, "
    "no clickbait, no quotes, no Markdown. Return only the text of the field."
)

REWRITE_HTML = (
    "You are an editor for a website. Rewrite the HTML fragment following the instruction. "
    "Keep the language of the original. Keep the HTML structure: tags, links and every "
    "<cms-plugin> element must stay exactly as they are. Return only the HTML, without code fences."
)

TRANSLATE_HTML = (
    "Translate the HTML fragment from {source} to {target}. Translate only the visible text. "
    "Keep every tag and attribute, including <cms-plugin> elements, exactly as they are. "
    "Return only the translated HTML, without code fences or comments."
)

TRANSLATE_TEXT = (
    "Translate the text from {source} to {target}. Return only the translation, "
    "without quotes or comments."
)

ALT_TEXT = (
    "Write the alternative text (alt attribute) of this image for a website, in {language}. "
    "Describe what matters for a visually impaired reader in at most 125 characters. "
    "Do not start with 'Image of'. Return only the text."
)

REWRITE_PRESETS = {
    "simplify": "Make it simpler and easier to read, for a general audience.",
    "shorten": "Make it about 30 % shorter without losing information.",
    "formal": "Use a more formal, professional tone.",
    "seo": "Improve it for search engines: clear headings and explicit key terms, no keyword stuffing.",
}
