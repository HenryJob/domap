from django.conf import settings
from django.utils import timezone

from .constants import PAGE_LABELS, BOT_UA_KEYWORDS
from .models import VisitorSession, PageView


def _is_bot(user_agent):
    ua = (user_agent or '').lower()
    return any(keyword in ua for keyword in BOT_UA_KEYWORDS)


class TrackingMiddleware:
    """Registra cada sesión de visitante y cada vista de página.

    El PageView se crea ANTES de renderizar la vista (con page_label vacío)
    para que el context processor pueda exponer su id a la plantilla y al
    beacon de duración en el mismo ciclo de request/response. Después de
    renderizar, si la respuesta no terminó en GET/200/HTML se elimina (no
    cuenta como vista de página); si sí calificó, se completa el page_label
    usando request.resolver_match, que recién está disponible en ese punto.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.session.session_key:
            request.session.save()

        request.visitor_session = None
        request.current_pageview = None
        pageview = None

        if not self._is_excluded(request.path):
            request.visitor_session = self._get_or_create_session(request)
            if request.method == 'GET':
                pageview = PageView.objects.create(session=request.visitor_session, path=request.path[:255])
                request.current_pageview = pageview

        response = self.get_response(request)

        if pageview is not None:
            is_html = response.get('Content-Type', '').startswith('text/html')
            if response.status_code == 200 and is_html:
                view_name = None
                if request.resolver_match:
                    view_name = f'{request.resolver_match.app_name}:{request.resolver_match.url_name}'
                pageview.page_label = PAGE_LABELS.get(view_name, '')
                pageview.save(update_fields=['page_label'])
            else:
                pageview.delete()
                request.current_pageview = None

        return response

    def _is_excluded(self, path):
        return any(path.startswith(prefix) for prefix in settings.TRACKING_EXCLUDED_PREFIXES)

    def _get_or_create_session(self, request):
        session_key = request.session.session_key
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        session, created = VisitorSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user_agent': user_agent[:255],
                'landing_path': request.path[:255],
                'referrer': request.META.get('HTTP_REFERER', '')[:255],
                'is_bot': _is_bot(user_agent),
            },
        )
        if not created:
            stale = (timezone.now() - session.last_seen).total_seconds() > 60
            if stale:
                session.save(update_fields=['last_seen'])
        return session
