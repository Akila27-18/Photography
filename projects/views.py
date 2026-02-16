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
from django.db.models import Q
from collections import defaultdict
from django.shortcuts import render
from django.utils.timezone import now
from django.http import JsonResponse
from django.template.loader import render_to_string
from .models import Project


def apply_project_filters(request, queryset):
    search = request.GET.get("search")
    status = request.GET.get("status")
    member = request.GET.get("member")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if search:
        queryset = queryset.filter(
            Q(code__icontains=search) |
            Q(client_name__icontains=search) |
            Q(event_type__icontains=search)
        )

    if status:
        queryset = queryset.filter(status=status)

    if member:
        queryset = queryset.filter(team__id=member)

    if start_date:
        queryset = queryset.filter(start_date__gte=start_date)

    if end_date:
        queryset = queryset.filter(end_date__lte=end_date)

    return queryset.distinct()


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
    projects = Project.objects.select_related("selection").prefetch_related("tasks", "team")
    projects = apply_project_filters(request, projects)
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

    return render(request, "projects.html", {
    "board": board,
    "to_assign_count": len(board["To Be Assigned"]),
    "team_members": User.objects.all(),
    "filters": request.GET,
    "active_page": "projects",
})

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

from collections import OrderedDict

def projects_list(request):
    projects = Project.objects.prefetch_related("tasks", "team")
    projects = apply_project_filters(request, projects)

    grouped = OrderedDict([
        ("pre_production", []),
        ("selection", []),
        ("post_production", []),
    ])

    for project in projects:
        tasks = project.tasks.all()

        # PRE PRODUCTION
        if project.status == "pre_production":
            project.stage_tasks = [
                ("Planning & Wedding", *project.task_progress("Planning")),
                ("Hard Disk", *project.task_progress("Hard Disk")),
                ("Pre Wedding Shoot", *project.task_progress("Pre Wedding")),
                ("Main Coverage", *project.task_progress("Main Coverage")),
            ]

        # SELECTION
        elif project.status == "selection":
            project.stage_tasks = [
                (task.title, 1 if task.is_completed else 0, 1)
                for task in tasks.filter(stage="selection")
            ]

        # POST PRODUCTION
        elif project.status == "post_production":
            project.stage_tasks = [
                (task.title, 1 if task.is_completed else 0, 1)
                for task in tasks.filter(stage="post")
            ]

        if project.status in grouped:
            grouped[project.status].append(project)

    return render(request, "projects_list.html", {
    "grouped_projects": grouped,
    "team_members": User.objects.all(),
    "filters": request.GET,
    "active_page": "projects",
})



def projects_overview(request):
    projects = Project.objects.prefetch_related("tasks", "team")
    projects = apply_project_filters(request, projects)

    pending_internal = []
    awaiting_client = []

    for project in projects:
        pending_tasks = project.tasks.filter(is_completed=False)

        # Example logic:
        # If selection stage → awaiting client
        if project.status == "selection":
            awaiting_client.append(project)
        else:
            if pending_tasks.exists():
                pending_internal.append(project)

        project.pending_tasks = pending_tasks

    return render(request, "projects_overview.html", {
        "pending_internal": pending_internal,
        "awaiting_client": awaiting_client,
        "team_members": User.objects.all(),
        "filters": request.GET,
        "active_page": "projects",
    })

from django.template.loader import render_to_string

def projects_filtered_partial(request):
    projects = Project.objects.prefetch_related("tasks", "team")
    projects = apply_project_filters(request, projects)

    view_type = request.GET.get("view")

    if view_type == "board":
        # rebuild board structure
        board = {
            "To Be Assigned": [],
            "Pre Production": [],
            "Selection": [],
            "Post Production": [],
            "Completed": [],
        }

        for project in projects:
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

        html = render_to_string("partials/board_content.html", {
            "board": board
        }, request=request)

    elif view_type == "list":
        grouped = {
            "pre_production": [],
            "selection": [],
            "post_production": [],
        }

        for project in projects:
            if project.status in grouped:
                grouped[project.status].append(project)

        html = render_to_string("partials/list_content.html", {
            "grouped_projects": grouped
        }, request=request)

    else:  # overview
        pending_internal = []
        awaiting_client = []

        for project in projects:
            pending_tasks = project.tasks.filter(is_completed=False)
            project.pending_tasks = pending_tasks

            if project.status == "selection":
                awaiting_client.append(project)
            elif pending_tasks.exists():
                pending_internal.append(project)

        html = render_to_string("partials/overview_content.html", {
            "pending_internal": pending_internal,
            "awaiting_client": awaiting_client,
        }, request=request)

    return JsonResponse({"html": html})

from collections import defaultdict
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.utils.timezone import now
from django.db.models import Q
from projects.models import Project


def sessions_view(request):
    filter_type = request.GET.get("type", "upcoming")
    search_query = request.GET.get("search", "").strip()

    today = now().date()

    # Show all active session projects
    projects = Project.objects.filter(
        status__in=["pre_production", "selection", "post_production"]
    ).prefetch_related("team")

    # -------- FILTER BY TYPE --------
    if filter_type == "past":
        projects = projects.filter(start_date__isnull=False, start_date__lt=today)

    elif filter_type == "decided":
        projects = projects.filter(start_date__isnull=True)

    else:  # upcoming
        projects = projects.filter(start_date__isnull=False, start_date__gte=today)

    # -------- SEARCH --------
    if search_query:
        projects = projects.filter(
            Q(client_name__icontains=search_query) |
            Q(event_type__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    projects = projects.order_by("start_date")

    # -------- GROUP BY MONTH --------
    grouped_sessions = defaultdict(list)

    for project in projects:
        if project.start_date:
            month = project.start_date.strftime("%B %Y")
        else:
            month = "To Be Decided"

        grouped_sessions[month].append(project)

    context = {
        "grouped_sessions": dict(grouped_sessions),
        "active_tab": filter_type,
    }

    # -------- AJAX --------
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        html = render_to_string(
            "partials/sessions_list.html",
            context,
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "sessions.html", {
        **context,
        "active_page": "sessions"
    })

