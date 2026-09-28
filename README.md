# Observatoire des CMS

Site django CMS 5.1 qui suit les releases et les avis de sécurité de Drupal, WordPress,
django CMS et Wagtail, et package `djangocms-ai-copilot` (copilote IA pour l'éditeur).
Le tutoriel complet détaille chaque fichier.

## Démarrer

```bash
uv venv -p 3.13 && source .venv/bin/activate
uv pip install pip -r requirements-dev.txt
python manage.py migrate
python manage.py loaddata technologies
python manage.py createsuperuser
python manage.py setup_site  # pages Accueil et Observatoire (FR/EN), publiées
export COPILOT_PROVIDER=djangocms_ai_copilot.providers.fake.FakeProvider  # sans clé API
python manage.py runserver
```

`setup_site` crée la page « Accueil » (gabarit Accueil, page d'accueil) et la page
« Observatoire » (application « Observatoire », espace de noms `watch`), puis les publie.
Elle ne fait rien si le site a déjà des pages.
Lancez la collecte depuis le menu « Observatoire » de la toolbar ou avec
`python manage.py collect_watch`.

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
