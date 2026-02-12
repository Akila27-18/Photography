from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, PhotoSelection, ProjectPhoto
import uuid

@receiver(post_save, sender=Project)
def create_assets_on_status_change(sender, instance, created, **kwargs):
    """
    Automatically create tasks and photo selection when project status changes.
    - Pre-production: seed tasks if missing.
    - Selection: seed tasks, create PhotoSelection if missing, attach photos.
    """

    # Pre-production tasks
    if instance.status == "pre_production":
        if not instance.tasks.filter(stage="pre").exists():
            instance.create_preproduction_tasks()

    # Selection stage
    if instance.status == "selection":
        # Ensure selection tasks exist
        if not instance.tasks.filter(stage="selection").exists():
            instance.create_selection_tasks()

        # Ensure PhotoSelection exists
        selection = getattr(instance, "selection", None)
        if not selection:
            selection = PhotoSelection.objects.create(
                project=instance,
                password=uuid.uuid4().hex[:8]
            )

        # Attach all project photos to this selection
        ProjectPhoto.objects.filter(project=instance, selection__isnull=True).update(selection=selection)