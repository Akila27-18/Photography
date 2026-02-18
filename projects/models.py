import uuid
from django.db import models
from django.utils import timezone
from accounts.models import User


class Project(models.Model):
    STATUS_CHOICES = (
        ('to_assign', 'To Be Assigned'),
        ('pre_production', 'Pre Production'),
        ('selection', 'Selection'),
        ('post_production', 'Post Production'),
        ('completed', 'Completed'),
    )

    lead = models.OneToOneField(
        'leads.Lead',
        on_delete=models.CASCADE,
        related_name='project'
    )
    code = models.CharField(max_length=20, unique=True)
    client_name = models.CharField(max_length=120)
    event_type = models.CharField(max_length=50)

    # Additional fields
    venue = models.CharField(max_length=255, blank=True, null=True)
    time = models.TimeField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    due_date = models.DateField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='to_assign'
    )
    team = models.ManyToManyField(
        User,
        related_name="projects",
        blank=True
    )

    completed_tasks = models.IntegerField(default=0)
    total_tasks = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.client_name} – {self.event_type}"
    @property
    def total_invoiced(self):
        return sum(inv.total for inv in self.invoices.all())

    @property
    def total_paid(self):
        return sum(inv.paid_amount for inv in self.invoices.all())

    @property
    def remaining_amount(self):
        return self.lead.amount - self.total_paid

    # ---------- UI HELPERS ----------
    def status_color(self):
        return {
            'to_assign': '#E9D5FF',
            'pre_production': '#E0E7FF',
            'selection': '#FEF9C3',
            'post_production': '#FEE2E2',
            'completed': '#DCFCE7',
        }.get(self.status, '#FFFFFF')

    def header_color(self):
        return {
            'to_assign': '#C084FC',
            'pre_production': '#6366F1',
            'selection': '#FACC15',
            'post_production': '#EF4444',
            'completed': '#22C55E',
        }.get(self.status, '#000000')

    # ---------- TASK PROGRESS ----------
    def update_task_progress(self):
        self.completed_tasks = self.tasks.filter(is_completed=True).count()
        self.total_tasks = self.tasks.count()
        self.save(update_fields=['completed_tasks', 'total_tasks'])

    def task_progress(self, keyword):
        qs = self.tasks.filter(title__icontains=keyword)
        return qs.filter(is_completed=True).count(), qs.count()

    def stage_progress(self, stage):
        qs = self.tasks.filter(stage=stage)
        return qs.filter(is_completed=True).count(), qs.count()

    # ---------- AUTOMATION LOGIC ----------
    def auto_update_status(self):
        """
        Handles automatic status progression, including selection path creation.
        """
        stage_order = [
            ('pre_production', 'pre'),
            ('selection', 'selection'),
            ('post_production', 'post')
        ]

        for status_name, stage_name in stage_order:
            # Check if all tasks in current stage are completed
            if self.status == status_name and not self.tasks.filter(stage=stage_name, is_completed=False).exists():
                # Move to next status
                next_index = stage_order.index((status_name, stage_name)) + 1
                if next_index < len(stage_order):
                    self.status = stage_order[next_index][0]
                else:
                    self.status = 'completed'
                self.save(update_fields=['status'])

                # ---------------- FIX: CREATE PHOTO SELECTION ----------------
                if self.status == 'selection' and not hasattr(self, 'selection'):
                    PhotoSelection.objects.create(
                        project=self,
                        password=uuid.uuid4().hex[:8]
                    )
                # -------------------------------------------------------------

                break

    # ---------- DRAG RULE ENFORCEMENT ----------
    def can_move_to(self, new_status):
        allowed = {
            'to_assign': ['pre_production'],
            'pre_production': ['selection'],
            'selection': ['post_production'],
            'post_production': ['completed'],
            'completed': [],
        }
        return new_status in allowed.get(self.status, [])

    # ---------- TASK CREATION ----------
    def create_preproduction_tasks(self):
        defaults = [
            "Planning & Wedding",
            "Hard Disk",
            "Pre Wedding Shoot",
            "Main Coverage",
            "Equipment Check",
            "Team Assignment",
            "Venue Recce",
        ]
        for title in defaults:
            self.tasks.get_or_create(
                title=title,
                stage="pre",
                defaults={"is_completed": False}
            )
    def create_selection_tasks(self):
        defaults = [
            "Initial Culling",
            "Final Culling",
            "Color Correction",
            "Preview Gallery Creation"
        ]
        for title in defaults:
            self.tasks.get_or_create(
                title=title,
                stage="selection",
                defaults={"is_completed": False}
            )


# ---------- PROJECT TASK ----------
class ProjectTask(models.Model):
    STAGE_CHOICES = (
        ('pre', 'Pre Production'),
        ('selection', 'Selection'),
        ('post', 'Post Production'),
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks"
    )
    title = models.CharField(max_length=120)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.project.client_name} - {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.project.update_task_progress()
        self.project.auto_update_status()


# ---------- PHOTO SELECTION ----------
class PhotoSelection(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="selection")
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_valid(self):
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

class ProjectPhoto(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="project_photos/")
    is_selected = models.BooleanField(default=False)
    selection = models.ForeignKey(PhotoSelection, on_delete=models.CASCADE, related_name="photos", null=True, blank=True)

