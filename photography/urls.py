import django
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path('admin/', admin.site.urls),

    # include your custom accounts app
    path('accounts/', include('accounts.urls')),

    # include Django's built-in auth views (login, logout, password reset, etc.)
    path('accounts/', include('django.contrib.auth.urls')),

    path('leads/', include('leads.urls')),
    path('projects/', include('projects.urls')),

    # redirect root to login
    path('', lambda request: redirect('/accounts/login/')),

    # path('invoices/', include('invoices.urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)