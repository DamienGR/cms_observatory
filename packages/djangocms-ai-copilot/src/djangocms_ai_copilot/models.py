from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _


class CopilotLog(models.Model):
    """Audit trail: who asked what, on which object, for how many tokens."""

    class Action(models.TextChoices):
        SUMMARY = "summary", _("Summary field")
        REWRITE = "rewrite", _("Rewrite")
        TRANSLATE = "translate", _("Translation")
        ALT_TEXT = "alt_text", _("Alt text")
        SUMMARIZE = "summarize", _("Summarize")
        CUSTOM = "custom", _("Custom")

    class Status(models.TextChoices):
        OK = "ok", _("Success")
        ERROR = "error", _("Error")

    created_at = models.DateTimeField(_("created"), auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, verbose_name=_("user")
    )
    action = models.CharField(_("action"), max_length=20, choices=Action.choices)
    status = models.CharField(_("status"), max_length=10, choices=Status.choices, default=Status.OK)
    content_type = models.ForeignKey(ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveBigIntegerField(null=True, blank=True)
    target = GenericForeignKey("content_type", "object_id")
    model = models.CharField(_("model"), max_length=100)
    prompt = models.TextField(_("prompt"))
    result = models.TextField(_("result"), blank=True)
    error = models.TextField(_("error"), blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = _("copilot log entry")
        verbose_name_plural = _("copilot log")
        permissions = [("use_copilot", _("Can use the AI copilot"))]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.get_action_display()} — {self.created_at:%Y-%m-%d %H:%M}"
