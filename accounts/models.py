# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

PHOTOGRAPHY_ROLES = (
    ('photographer', 'Photographer'),
    ('videographer', 'Videographer'),
    ('editor', 'Editor'),
    ('album_designer', 'Album Designer'),
)

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('team', 'Team Member'),
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='team'
    )

    photography_role = models.CharField(
        max_length=20,
        choices=PHOTOGRAPHY_ROLES,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.username

class PasswordResetRequest(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    token = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reset request for {self.user}"
