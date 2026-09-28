from cms.wizards.wizard_base import Wizard
from django import forms
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .models import Technology, TechnologyContent


class TechnologyWizardForm(forms.ModelForm):
    tagline = forms.CharField(label=_("Accroche"), max_length=200)

    class Meta:
        model = Technology
        fields = ["name", "slug", "registry", "package", "website"]

    @transaction.atomic
    def save(self, commit=True):
        technology = super().save()
        # with_user() : djangocms-versioning crée la version brouillon au nom de l'éditeur.
        # On renvoie le contenu : l'assistant redirige alors vers son mode édition.
        return TechnologyContent.objects.with_user(self._request.user).create(
            technology=technology,
            language=self.language_code,
            tagline=self.cleaned_data["tagline"],
        )


class TechnologyWizard(Wizard):
    def user_has_add_permission(self, user, **kwargs):
        return user.has_perm("watch.add_technology")


technology_wizard = TechnologyWizard(
    title=_("Nouvelle fiche technologie"),
    weight=150,
    form=TechnologyWizardForm,
    model=Technology,
    description=_("Suivre un nouveau CMS ou framework et rédiger sa fiche."),
)
