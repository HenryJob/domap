from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST

from .models import PageView
from .reports import build_dashboard_context
from .services import log_whatsapp_click as _log_whatsapp_click
from .services import log_instagram_click as _log_instagram_click


@require_POST
def record_duration(request):
    pageview_id = request.POST.get('pageview_id')
    duration = request.POST.get('duration')
    if not pageview_id or not duration:
        return HttpResponse(status=204)

    try:
        pageview = PageView.objects.select_related('session').get(id=pageview_id)
    except (PageView.DoesNotExist, ValueError):
        return HttpResponse(status=204)

    # Solo la sesión dueña del pageview puede reportar su duración.
    if pageview.session.session_key != request.session.session_key:
        return HttpResponse(status=204)

    try:
        seconds = max(0, int(float(duration)))
    except ValueError:
        return HttpResponse(status=204)

    pageview.duration_seconds = seconds
    pageview.is_duration_final = True
    pageview.save(update_fields=['duration_seconds', 'is_duration_final'])
    return HttpResponse(status=204)


@require_POST
def log_whatsapp_click(request):
    _log_whatsapp_click(request)
    return HttpResponse(status=204)


@require_POST
def log_instagram_click(request):
    _log_instagram_click(request)
    return HttpResponse(status=204)


@staff_member_required
def dashboard(request):
    today = timezone.localdate()
    end = parse_date(request.GET.get('end', '')) or today
    start = parse_date(request.GET.get('start', '')) or (end - timedelta(days=30))
    if start > end:
        start, end = end, start

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()), tz)
    end_dt = timezone.make_aware(datetime.combine(end, datetime.max.time()), tz)

    # Rangos rápidos para el filtro. `active` marca cuál coincide con el rango actual.
    presets = []
    for label, days in [('Hoy', 0), ('7 días', 6), ('30 días', 29), ('90 días', 89)]:
        p_start = today - timedelta(days=days)
        presets.append({
            'label': label,
            'start': p_start.isoformat(),
            'end': today.isoformat(),
            'active': start == p_start and end == today,
        })

    context = build_dashboard_context(start_dt, end_dt)
    context.update({'start': start, 'end': end, 'presets': presets, 'range_days': (end - start).days + 1})
    return render(request, 'analytics/dashboard.html', context)
