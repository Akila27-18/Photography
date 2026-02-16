from django.urls import path
from . import views

app_name = "projects"

urlpatterns = [
    path("board/", views.projects_board, name="board"),
    path("<int:project_id>/sessions/", views.project_sessions, name="project_sessions"),
    path("list/", views.projects_list, name="list"),
    path("overview/", views.projects_overview, name="overview"),

    # AJAX mutations
    path("toggle-member/", views.toggle_project_member, name="toggle_project_member"),
    path("update-field/", views.update_project_field, name="update_project_field"),
    path("update-status/", views.update_project_status, name="update_project_status"),
    path("toggle-task/", views.toggle_task, name="toggle_task"),
    path("projects/filter/", views.projects_filtered_partial, name="projects_filter"),


    # Client selection (only token version)
    path("selection/<uuid:token>/", views.client_selection, name="client_selection"),
    path("selection/<uuid:token>/save/", views.save_client_selection, name="save_client_selection"),

    # Session management
    path("sessions/", views.sessions_view, name="sessions"),

]
