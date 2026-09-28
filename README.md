# Observatoire des CMS

Site django CMS 5.1 qui suit les releases et les avis de sécurité de Drupal, WordPress,
Joomla, PrestaShop, Magento, django CMS et Wagtail, et package `djangocms-ai-copilot` (copilote IA pour l'éditeur).
Le tutoriel complet détaille chaque fichier.

## Démarrer

```bash
uv venv -p 3.13 && source .venv/bin/activate
uv pip install pip -r requirements-dev.txt
python manage.py migrate
python manage.py loaddata technologies
python manage.py createsuperuser
python manage.py setup_site  # pages Accueil, Observatoire, À propos, Mentions légales (FR/EN)
export COPILOT_PROVIDER=djangocms_ai_copilot.providers.fake.FakeProvider  # sans clé API
python manage.py runserver
```

`setup_site` crée la page « Accueil » (gabarit Accueil, page d'accueil) et la page
« Observatoire » (application « Observatoire », espace de noms `watch`) sur un site vide,
puis les pages « À propos » (`reverse_id` `about`) et « Mentions légales » (`legal-notice`,
liée depuis le pied de page) si elles manquent, et les publie. Relancée, elle ne fait rien.
Lancez la collecte depuis le menu « Observatoire » de la toolbar ou avec
`python manage.py collect_watch`.

Les releases viennent de PyPI, de Packagist ou des publications GitHub (Joomla, absent de
Packagist) ; les avis de sécurité, d'OSV.dev. Joomla, PrestaShop et Magento sont ajoutés
par la migration `watch.0003`.

Une technologie peut combiner plusieurs sources d'avis (champ « sources des avis » dans
l'admin), dédoublonnées par CVE. WordPress lit les avis GitHub de `WordPress/wordpress-develop`
puis OSV/Bitnami ; Joomla lit le flux du Joomla! Security Centre puis OSV/Packagist.

## Interface

Thème maison par-dessus Bootstrap 5.3 (conservé pour les plugins djangocms-frontend),
servi par le site sans CDN : `observatoire/static/` (thème, police Instrument Sans sous
licence OFL, logo). Les pages par défaut de django CMS et de Django sont remplacées :
accueil d'un site vide (`templates/cms/welcome.html`), erreurs 400/403/404/500, `robots.txt`.

## Tests

```bash
python -m pytest                                      # site
cd packages/djangocms-ai-copilot && python -m pytest  # package
```

Testé avec Python 3.13.7, Django 6.1.1 et django CMS 5.1.3.
