from cms.models import PageContent
from django.http import Http404
from django.shortcuts import render
from django.utils.translation import get_language
from django.views.generic import ListView, TemplateView

from .board import build_board
from .models import Advisory, PageTechnologyExtension, Release, Technology, TechnologyContent


class DashboardView(TemplateView):
    # get_root_template() de l'apphook lit cet attribut : les {% placeholder %}
    # de ce gabarit apparaissent dans le mode structure (django CMS 5.1).
    template_name = "watch/dashboard.html"

    def get(self, request, *args, **kwargs):
        content = request.toolbar.get_object()
        if request.toolbar.edit_mode_active and isinstance(content, PageContent):
            # En mode édition, django CMS ne crée pas les placeholders manquants du
            # brouillon : « intro » n'existerait pas si l'apphook a été ajouté après coup.
            content.rescan_placeholders()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        technologies = Technology.objects.filter(is_tracked=True)
        return super().get_context_data(
            technologies=technologies,
            board=build_board(technologies),
            releases=Release.objects.filter(is_prerelease=False).select_related("technology")[:15],
            advisories=Advisory.objects.select_related("technology")[:8],
            **kwargs,
        )


class AdvisoryListView(ListView):
    template_name = "watch/advisory_list.html"
    paginate_by = 25

    def get_queryset(self):
        queryset = Advisory.objects.select_related("technology")
        if technology := self.request.GET.get("technologie"):
            queryset = queryset.filter(technology__slug=technology)
        if severity := self.request.GET.get("severite"):
            queryset = queryset.filter(severity=severity)
        return queryset

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            technologies=Technology.objects.all(), severities=Advisory.Severity.choices, **kwargs
        )


def render_technology_content(request, content):
    """Rendu partagé par la vue publique et par les endpoints d'aperçu et d'édition du CMS."""
    technology = content.technology
    related_pages = [
        (extension.extended_object, url)
        for extension in PageTechnologyExtension.objects.filter(technology=technology).select_related(
            "extended_object"
        )
        # django CMS 5.1 : get_absolute_url() renvoie None si la page n'est pas publiée.
        if (url := extension.extended_object.get_absolute_url(content.language))
    ]
    return render(
        request,
        content.get_template(),
        {
            "object": content,
            "technology": technology,
            "row": build_board([technology])[0],
            "releases": technology.releases.filter(is_prerelease=False)[:10],
            "advisories": technology.advisories.all()[:10],
            "related_pages": related_pages,
        },
    )


def technology_detail(request, slug):
    content = (
        TechnologyContent.objects.filter(technology__slug=slug, language=get_language())
        .select_related("technology")
        .first()
    )
    if content is None:
        raise Http404
    request.toolbar.set_object(content)  # boutons « Modifier » et « Aperçu » dans la toolbar
    return render_technology_content(request, content)
