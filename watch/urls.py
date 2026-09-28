from django.urls import path

from . import views
from .feeds import LatestAdvisoriesFeed

app_name = "watch"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("securite/", views.AdvisoryListView.as_view(), name="advisories"),
    path("securite/flux.xml", LatestAdvisoriesFeed(), name="advisories-feed"),
    path("<slug:slug>/", views.technology_detail, name="technology-detail"),
]
