"""Contenu initial des pages créées par `setup_site`, par langue.

Les éditeurs le reprennent ensuite dans le CMS : modifier ce fichier ne change pas
les pages déjà créées.
"""

CMS_LIST = {
    "fr": "Drupal, WordPress, Joomla, PrestaShop, Magento, django CMS et Wagtail",
    "en": "Drupal, WordPress, Joomla, PrestaShop, Magento, django CMS and Wagtail",
}

HOME = {
    "fr": {
        "title": "Accueil",
        "hero_title": "Les versions et failles des CMS, suivies pour vous",
        "hero_subtitle": f"{CMS_LIST['fr']} : dernières releases et avis de "
        "sécurité, collectés automatiquement plusieurs fois par jour.",
        "sidebar_title": "<h2>Correctifs de sécurité</h2>",
        "text": "<p>L'observatoire interroge PyPI, Packagist, GitHub et OSV.dev, puis résume chaque avis "
        "de sécurité pour que vous sachiez en un coup d'œil s'il faut mettre à jour.</p><h2>Dernières releases</h2>",
    },
    "en": {
        "title": "Home",
        "hero_title": "CMS releases and vulnerabilities, tracked for you",
        "hero_subtitle": f"{CMS_LIST['en']}: latest releases and security "
        "advisories, collected automatically several times a day.",
        "sidebar_title": "<h2>Security fixes</h2>",
        "text": "<p>The observatory queries PyPI, Packagist, GitHub and OSV.dev, then summarises each "
        "security advisory so you know at a glance whether to upgrade.</p><h2>Latest releases</h2>",
    },
}

WATCH = {"fr": ("Observatoire", "observatoire"), "en": ("Observatory", "observatory")}

LEGAL = {
    "fr": {
        "title": "Mentions légales",
        "slug": "mentions-legales",
        "body": """<h1>Mentions légales</h1>
<h2>Éditeur du site</h2>
<p>Damien GROS, entrepreneur individuel<br>
SIREN : 510 717 523<br>
Contact : <a href="mailto:contact@dg-tech.dev">contact@dg-tech.dev</a><br>
Service fourni par <a href="https://dg-tech.dev/">dg-tech.dev</a></p>
<p>Directeur de la publication : Damien GROS.</p>
<h2>Hébergement</h2>
<p>OVH SAS<br>
2 rue Kellermann, 59100 Roubaix, France<br>
Téléphone : +33 9 72 10 10 07<br>
<a href="https://www.ovhcloud.com/">www.ovhcloud.com</a></p>
<h2>Données personnelles et cookies</h2>
<p>Le site ne propose pas de compte visiteur, ne dépose aucun cookie publicitaire ni de mesure
d'audience et ne collecte aucune donnée personnelle à des fins commerciales. Un cookie technique
mémorise la langue choisie ; il est exempté de consentement. Les journaux techniques du serveur
(adresse IP, pages demandées) sont conservés pour la sécurité du service, puis supprimés.</p>
<p>Conformément au RGPD, vous pouvez exercer vos droits d'accès, de rectification et d'effacement en
écrivant à <a href="mailto:contact@dg-tech.dev">contact@dg-tech.dev</a>, et saisir la CNIL en cas de
litige.</p>
<h2>Contenus et responsabilité</h2>
<p>Les versions et avis de sécurité proviennent de sources publiques (PyPI, Packagist, GitHub,
OSV.dev) et restent soumis à leurs conditions d'utilisation. Ils sont fournis à titre informatif,
sans garantie d'exhaustivité ni d'exactitude : l'éditeur ne saurait être tenu responsable des
décisions prises sur leur seule base. Les noms et marques cités appartiennent à leurs propriétaires
respectifs.</p>""",
    },
    "en": {
        "title": "Legal notice",
        "slug": "legal-notice",
        "body": """<h1>Legal notice</h1>
<h2>Publisher</h2>
<p>Damien GROS, sole proprietor (entrepreneur individuel)<br>
SIREN: 510 717 523<br>
Contact: <a href="mailto:contact@dg-tech.dev">contact@dg-tech.dev</a><br>
Service provided by <a href="https://dg-tech.dev/">dg-tech.dev</a></p>
<p>Publication director: Damien GROS.</p>
<h2>Hosting</h2>
<p>OVH SAS<br>
2 rue Kellermann, 59100 Roubaix, France<br>
Phone: +33 9 72 10 10 07<br>
<a href="https://www.ovhcloud.com/">www.ovhcloud.com</a></p>
<h2>Personal data and cookies</h2>
<p>The site has no visitor accounts, sets no advertising or analytics cookies and collects no personal
data for commercial purposes. A technical cookie remembers the chosen language; it is exempt from
consent. Server logs (IP address, requested pages) are kept for security purposes, then deleted.</p>
<p>Under the GDPR, you may exercise your rights of access, rectification and erasure by writing to
<a href="mailto:contact@dg-tech.dev">contact@dg-tech.dev</a>, and lodge a complaint with the CNIL.</p>
<h2>Content and liability</h2>
<p>Releases and security advisories come from public sources (PyPI, Packagist, GitHub, OSV.dev) and
remain subject to their terms of use. They are provided for information only, with no guarantee of
completeness or accuracy: the publisher cannot be held liable for decisions based solely on them.
Names and trademarks mentioned belong to their respective owners.</p>""",
    },
}
