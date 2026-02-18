from django.db import models
from django.utils import timezone


class Lead(models.Model):
    project_code = models.CharField(max_length=10, unique=True, null=True, blank=True)

    # Status choices
    STATUS_NEW = 'NEW'
    STATUS_FOLLOW = 'FOLLOW'
    STATUS_ACCEPTED = 'ACCEPTED'
    STATUS_LOST = 'LOST'

    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_FOLLOW, 'Follow'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_LOST, 'Lost'),
    ]

    # Session choices
    SESSION_MORNING = 'MOR'
    SESSION_EVENING = 'EVE'

    SESSION_CHOICES = [
        (SESSION_MORNING, 'Morning'),
        (SESSION_EVENING, 'Evening'),
    ]

    # Lead details
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    event_place = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.CharField(max_length=100, blank=True, null=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Event dates and sessions
    followup_date = models.DateField(blank=True, null=True)
    event_start_date = models.DateField(blank=True, null=True)
    event_start_session = models.CharField(max_length=3, choices=SESSION_CHOICES, default=SESSION_MORNING)
    event_end_date = models.DateField(blank=True, null=True)
    event_end_session = models.CharField(max_length=3, choices=SESSION_CHOICES, default=SESSION_EVENING)

    # Status and timestamps
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.project_code:
            last_code = (
                Lead.objects
                .exclude(project_code__isnull=True)
                .order_by('-project_code')
                .values_list('project_code', flat=True)
                .first()
            )

            if last_code and last_code.startswith("AK"):
                last_number = int(last_code[2:])
                new_number = last_number + 1
            else:
                new_number = 1

            self.project_code = f"AK{new_number:03d}"

        super().save(*args, **kwargs)

