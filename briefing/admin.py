from django.contrib import admin
from .models import GmailConnection, BriefingCache
admin.site.register(GmailConnection)
admin.site.register(BriefingCache)
