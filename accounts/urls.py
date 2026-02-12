from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path('', views.root_redirect),                    # redirects /accounts/ → login
    path('login/', views.admin_login, name='login'), # admin login
    path('team-login/', views.team_login, name='team_login'), # team login
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('approve-reset/<str:token>/', views.approve_reset, name='approve_reset'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('team-dashboard/', views.team_dashboard, name='team_dashboard'),
    path('api/login-config/', views.login_config_api, name='login_config_api'),
    # accounts/urls.py
    path('team-members/', views.team_members_list, name='team_members'),
    path('team-members/add/', views.add_team_member, name='add_team_member'),
    path('team-members/edit/<int:user_id>/', views.edit_team_member, name='edit_team_member'),
    path('team-members/delete/<int:user_id>/', views.delete_team_member, name='delete_team_member'),
    path('team-members/reset-password/<int:user_id>/', views.admin_reset_team_password, name='admin_reset_team_password'),


]