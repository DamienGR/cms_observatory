try:  # Django 6.0+
    from django.tasks import task
except ImportError:  # Django 5.2 with the django-tasks backport
    from django_tasks import task

__all__ = ["task"]
