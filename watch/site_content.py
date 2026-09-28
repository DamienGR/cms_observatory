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

ABOUT = {
    "fr": {
        "title": "À propos",
        "slug": "a-propos",
        "body": f"""<h1>À propos</h1>
<p>L'Observatoire des CMS rassemble en un seul endroit les nouvelles versions et les avis de sécurité
des principaux CMS open source : {CMS_LIST['fr']}.</p>
<h2>À quoi sert-il ?</h2>
<p>Maintenir un site, c'est surveiller en permanence les mises à jour de son CMS et savoir lesquelles
corrigent une faille. Ces informations sont dispersées entre registres de paquets, dépôts de code et
bases de vulnérabilités. L'observatoire les collecte pour vous et répond à trois questions :</p>
<ul>
<li>quelle est la dernière version stable de chaque CMS ?</li>
<li>quelles versions corrigent une faille de sécurité, et de quelle gravité ?</li>
<li>quel CMS a connu le plus d'alertes ces douze derniers mois ?</li>
</ul>
<p>Il s'adresse aux agences, aux développeurs freelances, aux équipes techniques et à toute personne
qui doit choisir un CMS ou garder ses sites à jour.</p>
<h2>D'où viennent les données ?</h2>
<p>Les versions proviennent des registres officiels (PyPI, Packagist) ou des publications GitHub des
projets. Les avis de sécurité proviennent des équipes de sécurité des projets quand elles les publient
(WordPress, Joomla) et de la base ouverte <a href="https://osv.dev/">OSV.dev</a>.
La collecte est automatique et a lieu plusieurs fois par jour. Chaque avis renvoie vers sa source.</p>
<h2>Limites</h2>
<p>L'observatoire ne remplace pas les annonces de sécurité officielles de chaque projet : un avis peut
y paraître avec quelques heures de décalage, et certains éditeurs publient peu dans OSV. Les résumés
sont générés automatiquement et peuvent être imprécis : vérifiez toujours l'avis d'origine avant
d'agir.</p>
<p>Un flux RSS des avis de sécurité est disponible en pied de page.</p>""",
    },
    "en": {
        "title": "About",
        "slug": "about",
        "body": f"""<h1>About</h1>
<p>The Observatoire des CMS (CMS Observatory) brings together, in one place, the new releases and security advisories of the
main open source CMSs: {CMS_LIST['en']}.</p>
<h2>What is it for?</h2>
<p>Maintaining a website means constantly watching your CMS for updates and knowing which ones fix a
vulnerability. That information is scattered across package registries, code repositories and
vulnerability databases. The observatory collects it for you and answers three questions:</p>
<ul>
<li>what is the latest stable version of each CMS?</li>
<li>which versions fix a security issue, and how severe is it?</li>
<li>which CMS has had the most alerts over the last twelve months?</li>
</ul>
<p>It is meant for agencies, freelance developers, technical teams and anyone who has to choose a CMS
or keep their sites up to date.</p>
<h2>Where does the data come from?</h2>
<p>Releases come from the official registries (PyPI, Packagist) or from the projects' GitHub releases.
Security advisories come from the projects' own security teams where they publish them (WordPress,
Joomla) and from the open <a href="https://osv.dev/">OSV.dev</a> database. Collection is
automatic and runs several times a day. Every advisory links back to its source.</p>
<h2>Limitations</h2>
<p>The observatory does not replace each project's official security announcements: an advisory may
appear here a few hours later, and some vendors publish little to OSV. Summaries are generated
automatically and may be inaccurate: always check the original advisory before acting.</p>
<p>An RSS feed of security advisories is available in the footer.</p>""",
    },
}

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
