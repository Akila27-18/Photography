from urllib import request
from django.db import transaction
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
import json
from datetime import datetime
from django.db import models
from .models import Project, ProjectTask
from accounts.models import User
from .models import PhotoSelection, ProjectPhoto
import uuid


User = get_user_model()


# ------------------------
# Admin decorator
# ------------------------
def admin_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_staff or request.user.is_superuser):
            return HttpResponseForbidden("Admins only")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ------------------------
# Helper: parse JSON safely
# ------------------------
def parse_json_request(request):
    try:
        return json.loads(request.body), None
    except json.JSONDecodeError:
        return None, JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)


# ------------------------
# Helper: task progress
# ------------------------
def task_progress_percentage(tasks, keyword):
    category_tasks = [t for t in tasks if keyword.lower() in t.title.lower()]
    if not category_tasks:
        return 0
    completed_count = sum(t.is_completed for t in category_tasks)
    return int((completed_count / len(category_tasks)) * 100)


# ------------------------
# Projects Board
# ------------------------
from django.db.models import Prefetch
from .models import PhotoSelection

def projects_board(request):
    projects = Project.objects.select_related("selection").prefetch_related("tasks").all()
    board = {
        "To Be Assigned": [],
        "Pre Production": [],
        "Selection": [],
        "Post Production": [],
        "Completed": [],
    }

    for project in projects:
        tasks = project.tasks.all()

        if project.status == "pre_production":
            project.pre_tasks = [
                ("Planning & Wedding", task_progress_percentage(tasks, "Planning")),
                ("Hard Disk", task_progress_percentage(tasks, "Hard Disk")),
                ("Pre Wedding Shoot", task_progress_percentage(tasks, "Pre Wedding")),
                ("Main Coverage", task_progress_percentage(tasks, "Main Coverage")),
            ]

        # Assign to board
        if project.status == "to_assign":
            board["To Be Assigned"].append(project)
        elif project.status == "pre_production":
            board["Pre Production"].append(project)
        elif project.status == "selection":
            board["Selection"].append(project)
        elif project.status == "post_production":
            board["Post Production"].append(project)
        elif project.status == "completed":
            board["Completed"].append(project)

    return render(request, "projects.html",
        {
            "board": board,
            "to_assign_count": len(board["To Be Assigned"]),
            "active_page": "projects",
        })




# ------------------------
# Project Sessions
# ------------------------
# ------------------------
# Project Sessions
# ------------------------
@login_required
def project_sessions(request, project_id):
    project = get_object_or_404(
        Project.objects.prefetch_related("team", "tasks"),
        id=project_id
    )

    users = User.objects.all()

    # Prepare task stages for template
    tasks_by_stage = [
        ("Pre Production", project.tasks.filter(stage="pre")),
        ("Selection", project.tasks.filter(stage="selection")),
        ("Post Production", project.tasks.filter(stage="post")),
    ]

    context = {
        "project": project,
        "users": users,
        "pre_roles": ["photographer", "videographer"],
        "post_roles": ["editor", "album_designer"],
        "tasks_by_stage": tasks_by_stage,  # Pass as list of tuples
    }

    return render(request, "project_sessions.html", context)
    



# ------------------------
# Admin AJAX Endpoints (Safe)
# ------------------------
@require_POST
@admin_required
@transaction.atomic
def toggle_project_member(request):
    data, error = parse_json_request(request)
    if error:
        return error

    project_id = data.get("project_id")
    user_id = data.get("user_id")

    if not project_id or not user_id:
        return JsonResponse({"success": False, "error": "Missing project_id or user_id"}, status=400)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"success": False, "error": "Project does not exist"}, status=404)

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return JsonResponse({"success": False, "error": "User does not exist"}, status=404)

    if user in project.team.all():
        project.team.remove(user)
    else:
        project.team.add(user)

    return JsonResponse({"success": True})


@require_POST
@admin_required
@transaction.atomic
def update_project_field(request):
    data, error = parse_json_request(request)
    if error:
        return error

    project_id = data.get("project_id")
    field = data.get("field")
    value = data.get("value")

    if not project_id or not field:
        return JsonResponse({"success": False, "error": "Missing project_id or field"}, status=400)

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({"success": False, "error": "Project does not exist"}, status=404)

    if not hasattr(project, field):
        return JsonResponse({"success": False, "error": "Invalid field"}, status=400)

    # Type conversion
    field_obj = Project._meta.get_field(field)
    try:
        if isinstance(field_obj, models.DateField):
            value = datetime.strptime(value, "%Y-%m-%d").date()
        elif isinstance(field_obj, models.TimeField):
            value = datetime.strptime(value, "%H:%M").time()
        elif isinstance(field_obj, models.IntegerField):
            value = int(value)
    except Exception:
        return JsonResponse({"success": False, "error": "Invalid value for field"}, status=400)

    setattr(project, field, value)
    project.save(update_fields=[field])

    return JsonResponse({"success": True, "field": field, "value": value})


@require_POST
@admin_required
@transaction.atomic
def toggle_task(request):
    data, error = parse_json_request(request)
    if error:
        return error

    task_id = data.get("task_id")
    completed = data.get("completed", False)

    if not task_id:
        return JsonResponse({"success": False, "error": "Missing task_id"}, status=400)

    try:
        task = ProjectTask.objects.get(id=task_id)
    except ProjectTask.DoesNotExist:
        return JsonResponse({"success": False, "error": "Task does not exist"}, status=404)

    task.is_completed = bool(completed)
    task.save()  # auto_update_status runs automatically in models

    project = task.project
    return JsonResponse({
        "success": True,
        "completed": project.completed_tasks,
        "total": project.total_tasks,
        "new_status": project.status
    })


@require_POST
@admin_required
@transaction.atomic
def update_project_status(request):
    data, error = parse_json_request(request)
    if error:
        return error

    project_id = data.get("project_id")
    new_status = data.get("new_status")

    if not project_id or not new_status:
        return JsonResponse({"success": False, "error": "Missing project_id or new_status"}, status=400)

    project = get_object_or_404(Project, id=project_id)

    if project.can_move_to(new_status):

        # ----------------- Pre-production tasks -----------------
        if new_status == "pre_production":
            project.create_preproduction_tasks()

        # ----------------- Selection path -----------------
        if new_status == "selection":
            project.create_selection_tasks()

            selection = getattr(project, "selection", None)
            if not selection:
                selection = PhotoSelection.objects.create(
                    project=project,
                    password=uuid.uuid4().hex[:8]
                )
            # Attach all project photos to this selection
            ProjectPhoto.objects.filter(project=project).update(selection=selection)

        # ----------------- Update project status -----------------
        project.status = new_status
        project.save(update_fields=["status"])

        return JsonResponse({"success": True, "new_status": new_status})

    else:
        return JsonResponse({"success": False, "error": "Invalid status transition"}, status=400)
from django.views.decorators.http import require_POST

def client_selection(request, token):
    try:
        selection = PhotoSelection.objects.get(token=token)
    except PhotoSelection.DoesNotExist:
        return JsonResponse({"success": False, "error": "Invalid token"})

    if request.method == "POST" and request.headers.get("x-requested-with") == "XMLHttpRequest":
        password = request.POST.get("password")
        if password == selection.password:
            request.session["selection_access"] = str(selection.token)
            return JsonResponse({"success": True})
        else:
            return JsonResponse({"success": False, "error": "Invalid password"})

    # GET request → normal page render
    return render(request, "client_selection.html", {
        "photos": selection.photos.all(),
        "project": selection.project
    })


@require_POST
@transaction.atomic
def save_client_selection(request, token):
    selection = get_object_or_404(PhotoSelection, token=token)

    if request.session.get("selection_access") != str(token):
        return JsonResponse({"success": False}, status=403)

    data = json.loads(request.body)
    selected_ids = [int(i) for i in data.get("selected_ids", [])]

    # 1️⃣ Reset all photos
    ProjectPhoto.objects.filter(project=selection.project).update(is_selected=False)

    # 2️⃣ Mark selected photos
    ProjectPhoto.objects.filter(id__in=selected_ids).update(is_selected=True)

    project = selection.project

    # 3️⃣ Mark selection tasks as completed
    project.tasks.filter(stage="selection").update(is_completed=True)

    # 4️⃣ Move project to post production
    project.status = "post_production"
    project.save(update_fields=["status"])

    return JsonResponse({"success": True})

def projects_list(request):
    return render(request, "projects_list.html", {
        "active_page": "projects",
    })

def projects_overview(request):
    return render(request, "projects_overview.html", {
        "active_page": "projects",
    })
