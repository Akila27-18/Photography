from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Sum
from datetime import date
import json

from .models import Lead


# ================== DASHBOARD ==================
@login_required
def leads_dashboard(request):
    today = date.today()

    # AUTO MOVE FOLLOW / NEW → LOST if event is over
    Lead.objects.filter(
        status__in=[Lead.STATUS_NEW, Lead.STATUS_FOLLOW],
        event_end_date__lt=today
    ).update(status=Lead.STATUS_LOST)

    return render(request, 'leads.html', {
        'total_leads': Lead.objects.count(),
        'total_amount': float(Lead.objects.aggregate(total=Sum('amount'))['total'] or 0),
        'accepted_amount': float(
            Lead.objects.filter(status=Lead.STATUS_ACCEPTED).aggregate(total=Sum('amount'))['total'] or 0
        ),
        'lost_amount': float(
            Lead.objects.filter(status=Lead.STATUS_LOST).aggregate(total=Sum('amount'))['total'] or 0
        ),
        'active_page': 'leads',
        'status_choices': Lead.STATUS_CHOICES,
    })


# ================== LIST ==================
@login_required
def leads_list(request):
    query = request.GET.get("q", "").strip()

    leads = Lead.objects.all().order_by("-id")

    if query:
        leads = leads.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(event_type__icontains=query) |
            Q(event_place__icontains=query) |
            Q(status__icontains=query)
        )

    data = {key: [] for key, _ in Lead.STATUS_CHOICES}

    for lead in leads:
        data[lead.status].append({
            "id": lead.id,
            "name": lead.name,
            "phone": lead.phone or "",
            "email": lead.email or "",
            "event_place": lead.event_place or "",
            "event_type": lead.event_type or "",
            "amount": float(lead.amount),
            "advance_amount": float(lead.advance_amount or 0),
            "remaining_amount": float(lead.amount - (lead.advance_amount or 0)),
            "followup_date": lead.followup_date.isoformat() if lead.followup_date else "",
            "event_start_date": lead.event_start_date.isoformat() if lead.event_start_date else "",
            "event_start_session": lead.event_start_session,
            "event_end_date": lead.event_end_date.isoformat() if lead.event_end_date else "",
            "event_end_session": lead.event_end_session,
            "status": lead.status,
        })

    return JsonResponse(data)




# ================== ADD ==================
@login_required
@require_POST
def add_lead(request):
    try:
        start_date = date.fromisoformat(request.POST.get('event_start_date')) if request.POST.get('event_start_date') else None
        end_date = date.fromisoformat(request.POST.get('event_end_date')) if request.POST.get('event_end_date') else None
        followup_date = date.fromisoformat(request.POST.get('followup_date')) if request.POST.get('followup_date') else None

        lead = Lead.objects.create(
            name=request.POST.get('name'),
            phone=request.POST.get('phone', ''),
            email=request.POST.get('email', ''),
            event_type=request.POST.get('event_type', ''),
            amount=float(request.POST.get('amount') or 0),
            advance_amount=float(request.POST.get('advance_amount') or 0),
            event_start_date=start_date,
            event_start_session=request.POST.get('event_start_session', Lead.SESSION_MORNING),
            event_end_date=end_date,
            event_end_session=request.POST.get('event_end_session', Lead.SESSION_EVENING),
            followup_date=followup_date,
            status=Lead.STATUS_NEW
        )

        lead.full_clean()
        lead.save()

        return JsonResponse({'success': True, 'id': lead.id})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ================== EDIT ==================
@login_required
@require_POST
def edit_lead(request):
    try:
        lead = get_object_or_404(Lead, id=request.POST.get('id'))

        lead.name = request.POST.get('name')
        lead.phone = request.POST.get('phone', '')
        lead.email = request.POST.get('email', '')
        lead.event_type = request.POST.get('event_type', '')
        lead.amount = float(request.POST.get('amount') or 0)
        lead.advance_amount = float(request.POST.get('advance_amount') or 0)

        for field in ['followup_date', 'event_start_date', 'event_end_date']:
            val = request.POST.get(field)
            setattr(lead, field, date.fromisoformat(val) if val else None)

        lead.event_start_session = request.POST.get('event_start_session', Lead.SESSION_MORNING)
        lead.event_end_session = request.POST.get('event_end_session', Lead.SESSION_EVENING)

        lead.full_clean()
        lead.save()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ================== DELETE ==================
@login_required
@require_POST
def delete_lead(request):
    try:
        lead = get_object_or_404(Lead, id=request.POST.get('id'))
        lead.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


# ================== UPDATE STATUS ==================
@login_required
@require_POST
def update_lead_status(request, lead_id):
    try:
        data = json.loads(request.body)
        new_status = data.get('status')
        override = data.get('override') or data.get('force', False)

        lead = get_object_or_404(Lead, id=lead_id)

        if new_status == Lead.STATUS_ACCEPTED and lead.event_start_date and not override:
            conflicts = Lead.objects.filter(
                status=Lead.STATUS_ACCEPTED,
                event_start_date=lead.event_start_date,
                event_start_session=lead.event_start_session
            ).exclude(id=lead.id)

            if conflicts.exists():
                return JsonResponse({
                    'success': False,
                    'conflict': True,
                    'conflicts': list(conflicts.values('id', 'name'))
                }, status=409)

        lead.status = new_status
        lead.save(update_fields=["status"])

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

    
# ================== AMOUNTS ==================
@login_required
def lead_amounts(request):
    return JsonResponse({
        'total_leads': Lead.objects.count(),
        'total_amount': float(Lead.objects.aggregate(total=Sum('amount'))['total'] or 0),
        'accepted': float(Lead.objects.filter(status=Lead.STATUS_ACCEPTED).aggregate(total=Sum('amount'))['total'] or 0),
        'lost': float(Lead.objects.filter(status=Lead.STATUS_LOST).aggregate(total=Sum('amount'))['total'] or 0),
    })


# ================== CHECK CONFLICT ==================
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def check_conflict(request):
    event_date = request.GET.get("date")
    session = request.GET.get("session")
    lead_id = request.GET.get("lead_id")   # 👈 ADD THIS LINE

    if not event_date or not session:
        return JsonResponse({"success": False, "conflicts": []})

    conflicts = Lead.objects.filter(
        status=Lead.STATUS_ACCEPTED,
        event_start_date=event_date,
        event_start_session=session
    )

    # 👇 ADD THIS BLOCK
    if lead_id:
        conflicts = conflicts.exclude(id=lead_id)

    return JsonResponse({
        "success": True,
        "conflicts": list(
            conflicts.values("id", "name")
        )
    })



# ================== SEARCH LEADS ==================
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from .models import Lead


@require_GET
def search_leads(request):
    query = request.GET.get("q", "").strip()

    leads = Lead.objects.all()

    if query:
        leads = leads.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query) |
            Q(event_type__icontains=query) |
            Q(event_place__icontains=query) |
            Q(status__icontains=query)
        )

    data = [{
        "id": l.id,
        "name": l.name,
        "phone": l.phone,
        "email": l.email,
        "event_type": l.event_type,
        "event_place": l.event_place,
        "status": l.status,
        "amount": float(l.amount),
        "event_start_date": l.event_start_date,
        "event_end_date": l.event_end_date,
        "event_start_session": l.event_start_session,
        "event_end_session": l.event_end_session,
    } for l in leads]

    return JsonResponse({"leads": data})
