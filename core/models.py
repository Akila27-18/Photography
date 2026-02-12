from django.db import models

class LoginPageConfig(models.Model):
    welcome_text = models.CharField(max_length=255)
    admin_label = models.CharField(max_length=50)
    forgot_text = models.CharField(max_length=100)
    remember_me_enabled = models.BooleanField(default=True)

    def __str__(self):
        return "Login Page Config"
    
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache

@receiver(post_save, sender=LoginPageConfig)
def clear_login_config_cache(sender, **kwargs):
    cache.delete("login_page_config")