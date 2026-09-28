from django import forms
from django.utils.translation import gettext_lazy as _

from .prompts import REWRITE_PRESETS


class RewriteForm(forms.Form):
    preset = forms.ChoiceField(
        label=_("Goal"),
        choices=[
            ("simplify", _("Simplify")),
            ("shorten", _("Shorten")),
            ("formal", _("More formal")),
            ("seo", _("Search engine friendly")),
            ("custom", _("Custom instruction")),
        ],
    )
    instruction = forms.CharField(label=_("Custom instruction"), required=False, widget=forms.Textarea(attrs={"rows": 2}))
    proposal = forms.CharField(required=False, widget=forms.HiddenInput)

    def clean(self):
        data = super().clean()
        if data.get("preset") == "custom" and not data.get("instruction"):
            self.add_error("instruction", _("Please describe what you want."))
        return data

    def get_instruction(self):
        preset = self.cleaned_data["preset"]
        return self.cleaned_data["instruction"] if preset == "custom" else REWRITE_PRESETS[preset]


class TranslateForm(forms.Form):
    target_language = forms.ChoiceField(label=_("Translate to"))

    def __init__(self, *args, languages, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_language"].choices = languages
