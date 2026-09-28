from django.contrib import admin

from .models import CopilotLog


@admin.register(CopilotLog)
class CopilotLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "status", "user", "content_type", "object_id", "model", "input_tokens", "output_tokens")
    list_filter = ("action", "status", "model")
    date_hierarchy = "created_at"
    search_fields = ("prompt", "result")
    list_select_related = ("user", "content_type")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False  # read-only audit trail
