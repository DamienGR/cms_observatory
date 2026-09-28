from django.db import migrations

TECHNOLOGIES = [
    {"name": "Joomla", "slug": "joomla", "website": "https://www.joomla.org/",
     "registry": "github", "package": "joomla/joomla-cms"},
    {"name": "PrestaShop", "slug": "prestashop", "website": "https://www.prestashop-project.org/",
     "registry": "packagist", "package": "prestashop/prestashop"},
    {"name": "Magento", "slug": "magento", "website": "https://business.adobe.com/products/magento/open-source.html",
     "registry": "packagist", "package": "magento/community-edition"},
]


def add_technologies(apps, schema_editor):
    Technology = apps.get_model("watch", "Technology")
    for fields in TECHNOLOGIES:
        Technology.objects.get_or_create(slug=fields["slug"], defaults=fields)


def remove_technologies(apps, schema_editor):
    apps.get_model("watch", "Technology").objects.filter(slug__in=[t["slug"] for t in TECHNOLOGIES]).delete()


class Migration(migrations.Migration):
    dependencies = [("watch", "0002_technology_github_registry")]

    operations = [migrations.RunPython(add_technologies, remove_technologies)]
