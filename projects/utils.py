from django.db.models import Q

def filter_projects(request, queryset):
    search = request.GET.get("search")
    status = request.GET.get("status")
    member = request.GET.get("member")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")
    task_type = request.GET.get("task_type")

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

    if task_type:
        queryset = queryset.filter(tasks__title__icontains=task_type)

    return queryset.distinct()
