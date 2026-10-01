from django.contrib import admin
from django.urls import path
from briefing import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("api/health/", views.health, name="health"),
    path("api/overview/", views.overview, name="overview"),
    path("api/highlights/", views.highlights, name="highlights"),
    path("api/status/", views.status, name="status"),
    path("auth/gmail/start/", views.gmail_start, name="gmail_start"),
    path("auth/gmail/callback/", views.gmail_callback, name="gmail_callback"),
    path("auth/gmail/disconnect/", views.gmail_disconnect, name="gmail_disconnect"),
    path("api/briefing/refresh/", views.refresh_briefing, name="refresh_briefing"),
]
