from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Lead

@receiver(post_save, sender=Lead)
def create_project_when_lead_accepted(sender, instance, **kwargs):
    """
    Auto-create a Project when a Lead is marked as ACCEPTED
    """
    if instance.status == Lead.STATUS_ACCEPTED:
        # Lazy import to avoid circular import
        from projects.models import Project

        Project.objects.get_or_create(
            lead=instance,
            code=f'PRJ-{instance.id}',  # now must specify code for uniqueness
            defaults={
                'client_name': instance.name,
                'event_type': instance.event_type or 'General',
                'start_date': instance.event_start_date,
                'end_date': instance.event_end_date,
                'status': 'to_assign',
                    }
        )

