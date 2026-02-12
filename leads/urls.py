from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('', views.leads_dashboard, name='leads'),
    path('list/', views.leads_list, name='leads_list'),
    path('add/', views.add_lead, name='add_lead'),
    path('edit/', views.edit_lead, name='edit_lead'),
    path('delete/', views.delete_lead, name='delete_lead'),
    path('update-status/<int:lead_id>/', views.update_lead_status, name='update_status'),
    path('amounts/', views.lead_amounts, name='lead_amounts'),
    path('check-conflict/', views.check_conflict, name='check_conflict'),
    # path("search/", views.search_leads, name="search_leads"),



]
