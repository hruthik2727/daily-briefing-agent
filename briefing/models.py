from django.db import models

class GmailConnection(models.Model):
    # Local single-user MVP. OAuth token JSON is encrypted before being stored.
    provider = models.CharField(max_length=30, default="gmail", unique=True)
    encrypted_token = models.TextField()
    connected_email = models.EmailField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider}: {self.connected_email or 'connected'}"

class BriefingCache(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)
