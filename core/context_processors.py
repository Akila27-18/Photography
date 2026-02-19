from leads.models import Lead
from django.utils import timezone

def notifications(request):
    if request.user.is_authenticated:
        today = timezone.localdate()  # current date

        # Example notifications:
        # 1. New leads created today
        new_leads = Lead.objects.filter(status=Lead.STATUS_NEW, created_at__date=today)

        # 2. Leads needing follow-up today
        followup_leads = Lead.objects.filter(status=Lead.STATUS_FOLLOW, followup_date=today)

        notifications_list = []

        for lead in new_leads:
            notifications_list.append({
                "title": "New Lead Added",
                "details": f"{lead.name} ({lead.project_code})"
            })

        for lead in followup_leads:
            notifications_list.append({
                "title": "Lead Follow-Up",
                "details": f"{lead.name} ({lead.project_code})"
            })

    else:
        notifications_list = []

    return {
        "notifications": notifications_list
    }
