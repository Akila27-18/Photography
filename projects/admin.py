from django.contrib import admin
from .models import Project, ProjectPhoto, PhotoSelection


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("id", "client_name", "status")


@admin.register(ProjectPhoto)
class ProjectPhotoAdmin(admin.ModelAdmin):
    list_display = ("id", "project", "selection", "is_selected")
    list_filter = ("project", "selection")


@admin.register(PhotoSelection)
class PhotoSelectionAdmin(admin.ModelAdmin):
    list_display = ("project", "token", "password")
    readonly_fields = ("token",)
