from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import PageView
from .reports import resolve_dashboard_context
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
    context = resolve_dashboard_context(request)
    return render(request, 'analytics/dashboard.html', context)
