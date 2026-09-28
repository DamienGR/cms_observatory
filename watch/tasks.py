from django.tasks import task
from django.utils.html import strip_tags

from djangocms_ai_copilot.services import ask
from menus.menu_pool import menu_pool

from .models import Advisory, Technology
from .services import collect_technology

ADVISORY_SYSTEM_PROMPT = (
    "Tu es un expert en sécurité web. Résume l'avis de sécurité fourni en français, "
    "en 3 phrases maximum : ce qui est touché, le risque concret, l'action à mener "
    "(versions correctives incluses). Pas de mise en forme Markdown."
)


@task()
def collect_technology_task(technology_id: int) -> dict:
    technology = Technology.objects.get(pk=technology_id)
    report = collect_technology(technology)
    for advisory_id in report.new_advisory_ids:
        summarize_advisory_task.enqueue(advisory_id)
    if report.new_advisory_ids:
        # Les badges « failles récentes » du menu dépendent de ces données.
        menu_pool.clear(all=True)
    return report.as_dict()


@task(queue_name="llm", priority=-10)
def summarize_advisory_task(advisory_id: int) -> str:
    advisory = Advisory.objects.select_related("technology").get(pk=advisory_id)
    prompt = (
        f"Technologie : {advisory.technology.name}\n"
        f"Identifiant : {advisory.identifier} ({', '.join(advisory.aliases)})\n"
        f"Sévérité : {advisory.get_severity_display()}\n"
        f"Versions correctives : {', '.join(advisory.fixed_versions) or 'non précisées'}\n\n"
        f"{advisory.title}\n\n{strip_tags(advisory.details)[:6000]}"
    )
    advisory.summary = ask(ADVISORY_SYSTEM_PROMPT, prompt, action="summarize", target=advisory)
    advisory.save(update_fields=["summary"])
    return advisory.summary
