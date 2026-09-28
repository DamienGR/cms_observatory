from django.db import migrations

# roots/wordpress date presque toutes ses releases du même jour ; roots/wordpress-no-content
# porte les vraies dates et le même nommage que wordpress.org (7.1 et non 7.1.0).
OLD, NEW = "roots/wordpress", "roots/wordpress-no-content"


def switch_package(apps, old, new):
    Technology = apps.get_model("watch", "Technology")
    Release = apps.get_model("watch", "Release")
    technologies = Technology.objects.filter(registry="packagist", package=old)
    # Les releases aux dates erronées seront recollectées depuis le nouveau paquet.
    Release.objects.filter(technology__in=technologies).delete()
    technologies.update(package=new)


def forwards(apps, schema_editor):
    switch_package(apps, OLD, NEW)


def backwards(apps, schema_editor):
    switch_package(apps, NEW, OLD)


class Migration(migrations.Migration):
    dependencies = [("watch", "0003_add_joomla_prestashop_magento")]

    operations = [migrations.RunPython(forwards, backwards)]
