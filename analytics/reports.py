"""Agregaciones para el dashboard de analítica. Todo se calcula al vuelo
(sin Celery/cron) ya que el volumen esperado es de un negocio pequeño."""

import statistics
from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Sum, Count, Max, Avg
from django.db.models.functions import TruncDate, ExtractHour
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from django.utils.dateparse import parse_date

from catalog.models import Product
from orders.models import Order, OrderItem, ManualSale, ManualSaleItem
from .constants import PAGE_LABELS
from .models import (
    VisitorSession, PageView, CartEvent, WishlistEvent, CheckoutEvent, ProductViewEvent,
    WhatsappClickEvent, InstagramClickEvent,
)


# Vistas de PAGE_LABELS que requieren argumentos para reverse(); se muestra el
# patrón de la URL (con placeholder) en vez de una ruta histórica concreta.
_PARAMETRIZED_ROUTE_PATTERNS = {
    'orders:order_success': '/pedidos/confirmacion/<id>/',
}


def _current_route(view_name):
    """Resuelve la ruta ACTUAL (según las urls.py vigentes) para un view_name
    de PAGE_LABELS, en vez de reusar el `path` histórico guardado en PageView
    (que puede haber quedado obsoleto si la URL cambió)."""
    if view_name in _PARAMETRIZED_ROUTE_PATTERNS:
        return _PARAMETRIZED_ROUTE_PATTERNS[view_name]
    try:
        return reverse(view_name)
    except NoReverseMatch:
        return None


def _merge_series(*series_dicts):
    """series_dicts: lista de {date: float}. Devuelve fechas ordenadas + listas alineadas por serie."""
    all_dates = sorted(set().union(*[d.keys() for d in series_dicts]))
    return all_dates, [[float(d.get(date, 0)) for date in all_dates] for d in series_dicts]


def _classify_source(referrer, site_host=''):
    """Agrupa el referrer de la sesión en un canal de adquisición legible."""
    r = (referrer or '').lower()
    if not r:
        return 'Directo'
    if 'instagram' in r:
        return 'Instagram'
    if 'google' in r:
        return 'Google'
    if 'facebook' in r or 'fb.' in r or 'fb.me' in r:
        return 'Facebook'
    if 'tiktok' in r:
        return 'TikTok'
    if 'wa.me' in r or 'whatsapp' in r:
        return 'WhatsApp'
    if site_host and site_host in r:
        return 'Directo'
    return 'Otro'


def _classify_device(user_agent):
    """Deduce el tipo de dispositivo a partir del user-agent."""
    ua = (user_agent or '').lower()
    if 'ipad' in ua or ('tablet' in ua and 'mobile' not in ua):
        return 'Tablet'
    if any(k in ua for k in ('mobi', 'android', 'iphone', 'ipod')):
        return 'Móvil'
    return 'Escritorio'


def _labels_and_counts(counter, order):
    """Devuelve (labels, values) ordenados según `order`, con el resto al final."""
    labels, values = [], []
    for key in order:
        if counter.get(key):
            labels.append(key)
            values.append(counter[key])
    for key, val in sorted(counter.items(), key=lambda kv: -kv[1]):
        if key not in order and val:
            labels.append(key)
            values.append(val)
    return labels, values


def resolve_dashboard_context(request):
    """Lee el rango de fechas de la querystring, arma los presets rápidos y
    devuelve el contexto completo del dashboard. Compartido por las vistas
    de /panel/analitica/ y /analytics/panel/ para no duplicar esta lógica."""
    today = timezone.localdate()
    end = parse_date(request.GET.get('end', '')) or today
    start = parse_date(request.GET.get('start', '')) or (end - timedelta(days=30))
    if start > end:
        start, end = end, start

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, datetime.min.time()), tz)
    end_dt = timezone.make_aware(datetime.combine(end, datetime.max.time()), tz)

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
    context.update({
        'start': start,
        'end': end,
        'presets': presets,
        'range_days': (end - start).days + 1,
    })
    return context


def build_dashboard_context(start_dt, end_dt):
    sessions_qs = VisitorSession.objects.filter(is_bot=False, first_seen__range=(start_dt, end_dt))
    visits = sessions_qs.count()

    cart_events_qs = CartEvent.objects.filter(session__is_bot=False, created_at__range=(start_dt, end_dt))
    wishlist_events_qs = WishlistEvent.objects.filter(session__is_bot=False, created_at__range=(start_dt, end_dt))

    cart_add_total = cart_events_qs.filter(event_type='add').count()
    wishlist_add_total = wishlist_events_qs.filter(event_type='add').count()
    cart_adds_sessions = cart_events_qs.filter(event_type='add').values('session').distinct().count()
    checkout_started_sessions = (CheckoutEvent.objects
                                  .filter(step='started', session__is_bot=False, created_at__range=(start_dt, end_dt))
                                  .values('session').distinct().count())

    web_orders = Order.objects.filter(status__in=['confirmed', 'completed'], created_at__range=(start_dt, end_dt))
    # Order no tiene FK a VisitorSession (solo guarda session_key por valor),
    # así que para excluir bots del embudo cruzamos contra las claves no-bot conocidas.
    non_bot_session_keys = set(VisitorSession.objects.filter(is_bot=False).values_list('session_key', flat=True))
    completed_web_sessions = (web_orders.exclude(session_key='')
                               .filter(session_key__in=non_bot_session_keys)
                               .values('session_key').distinct().count())

    funnel = [
        {'label': 'Visitas', 'value': visits},
        {'label': 'Carrito', 'value': cart_adds_sessions},
        {'label': 'Checkout iniciado', 'value': checkout_started_sessions},
        {'label': 'Completado (web)', 'value': completed_web_sessions},
    ]

    # --- Abandono de carrito ---
    window_minutes = settings.ABANDONMENT_WINDOW_MINUTES
    # El corte se calcula respecto al final del rango consultado (o "ahora" si el
    # rango incluye el presente), para que un rango histórico no mida abandono
    # contra el momento actual.
    cutoff = min(timezone.now(), end_dt) - timedelta(minutes=window_minutes)
    stale_candidates = (cart_events_qs.filter(event_type='add')
                         .values('session_id').annotate(last_add=Max('created_at'))
                         .filter(last_add__lt=cutoff))
    candidate_session_ids = [c['session_id'] for c in stale_candidates]
    candidate_session_keys = list(
        VisitorSession.objects.filter(id__in=candidate_session_ids).values_list('session_key', flat=True))

    converted_web_keys = set(
        Order.objects.filter(session_key__in=candidate_session_keys).values_list('session_key', flat=True))
    manual_sale_codes = set(
        ManualSale.objects.exclude(session_reference='').values_list('session_reference', flat=True))

    abandoned_keys = [
        key for key in candidate_session_keys
        if key not in converted_web_keys and key[:8].upper() not in manual_sale_codes
    ]
    abandonment_rate = (len(abandoned_keys) / len(candidate_session_keys) * 100) if candidate_session_keys else 0

    # --- KPI de ventas combinadas (web + WhatsApp + Instagram, ambas registradas manualmente) ---
    manual_sales = ManualSale.objects.filter(sale_date__range=(start_dt, end_dt))
    whatsapp_sales = manual_sales.filter(channel='whatsapp')
    instagram_sales = manual_sales.filter(channel='instagram')
    web_revenue = web_orders.aggregate(s=Sum('total'))['s'] or 0
    whatsapp_revenue = whatsapp_sales.aggregate(s=Sum('total_amount'))['s'] or 0
    instagram_revenue = instagram_sales.aggregate(s=Sum('total_amount'))['s'] or 0
    combined_revenue = web_revenue + whatsapp_revenue + instagram_revenue
    web_sales_count = web_orders.count()
    whatsapp_sales_count = whatsapp_sales.count()
    instagram_sales_count = instagram_sales.count()
    combined_sales_count = web_sales_count + whatsapp_sales_count + instagram_sales_count
    conversion_rate = (combined_sales_count / visits * 100) if visits else 0

    # --- Ventas en el tiempo ---
    web_by_day = {
        row['day'].isoformat(): float(row['total'])
        for row in web_orders.annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum('total'))
    }
    whatsapp_by_day = {
        row['day'].isoformat(): float(row['total'])
        for row in whatsapp_sales.annotate(day=TruncDate('sale_date')).values('day').annotate(total=Sum('total_amount'))
    }
    instagram_by_day = {
        row['day'].isoformat(): float(row['total'])
        for row in instagram_sales.annotate(day=TruncDate('sale_date')).values('day').annotate(total=Sum('total_amount'))
    }
    sales_dates, (web_series, whatsapp_series, instagram_series) = _merge_series(
        web_by_day, whatsapp_by_day, instagram_by_day)
    combined_series = [w + wa + ig for w, wa, ig in zip(web_series, whatsapp_series, instagram_series)]

    # --- Visitas en el tiempo ---
    visits_by_day = {
        row['day'].isoformat(): row['count']
        for row in sessions_qs.annotate(day=TruncDate('first_seen')).values('day').annotate(count=Count('id'))
    }
    visit_dates = sorted(visits_by_day.keys())
    visit_counts = [visits_by_day[d] for d in visit_dates]

    # --- Tiempo en página ---
    durations = list(
        PageView.objects.filter(duration_seconds__isnull=False, entered_at__range=(start_dt, end_dt),
                                 session__is_bot=False)
        .values_list('duration_seconds', flat=True))
    avg_duration = round(sum(durations) / len(durations), 1) if durations else 0
    median_duration = round(statistics.median(durations), 1) if durations else 0

    # --- Productos: vistas / agregados al carrito / vendidos ---
    views_by_product = {r['product__name']: r['views'] for r in (
        ProductViewEvent.objects.filter(created_at__range=(start_dt, end_dt), session__is_bot=False)
        .values('product__name').annotate(views=Count('id')))}
    adds_by_product = {r['product__name']: r['adds'] for r in (
        cart_events_qs.filter(event_type='add').values('product__name').annotate(adds=Count('id')))}
    web_sales_by_product = {r['product__name']: r['qty'] for r in (
        OrderItem.objects.filter(order__in=web_orders).values('product__name').annotate(qty=Sum('quantity')))}
    whatsapp_sales_by_product = {r['product__name']: r['qty'] for r in (
        ManualSaleItem.objects.filter(sale__in=whatsapp_sales, product__isnull=False)
        .values('product__name').annotate(qty=Sum('quantity')))}
    instagram_sales_by_product = {r['product__name']: r['qty'] for r in (
        ManualSaleItem.objects.filter(sale__in=instagram_sales, product__isnull=False)
        .values('product__name').annotate(qty=Sum('quantity')))}
    wishlist_by_product = {r['product__name']: r['n'] for r in (
        wishlist_events_qs.filter(event_type='add').values('product__name').annotate(n=Count('id')))}

    # --- Preferencia de canal directo: cuántos clientes prefieren WhatsApp vs. Instagram ---
    whatsapp_clicks_qs = WhatsappClickEvent.objects.filter(session__is_bot=False, created_at__range=(start_dt, end_dt))
    instagram_clicks_qs = InstagramClickEvent.objects.filter(session__is_bot=False, created_at__range=(start_dt, end_dt))
    whatsapp_clicks_total = whatsapp_clicks_qs.count()
    instagram_clicks_total = instagram_clicks_qs.count()
    whatsapp_clicks_sessions = whatsapp_clicks_qs.values('session').distinct().count()
    instagram_clicks_sessions = instagram_clicks_qs.values('session').distinct().count()
    channel_clicks_total = whatsapp_clicks_total + instagram_clicks_total
    whatsapp_click_share = round(whatsapp_clicks_total / channel_clicks_total * 100, 1) if channel_clicks_total else 0
    instagram_click_share = round(instagram_clicks_total / channel_clicks_total * 100, 1) if channel_clicks_total else 0

    product_names = (set(views_by_product) | set(adds_by_product) | set(web_sales_by_product)
                     | set(whatsapp_sales_by_product) | set(instagram_sales_by_product) | set(wishlist_by_product))
    top_products = sorted([
        {
            'name': name,
            'views': views_by_product.get(name, 0),
            'cart_adds': adds_by_product.get(name, 0),
            'wishlist': wishlist_by_product.get(name, 0),
            'sales': (web_sales_by_product.get(name, 0) + whatsapp_sales_by_product.get(name, 0)
                      + instagram_sales_by_product.get(name, 0)),
            # % de vistas de este producto que terminaron en un agregado al carrito.
            'view_to_cart_rate': (
                round(adds_by_product.get(name, 0) / views_by_product[name] * 100, 1)
                if views_by_product.get(name) else None
            ),
        }
        for name in product_names
    ], key=lambda p: (-p['sales'], -p['cart_adds'], -p['views']))[:10]

    # --- Vista → carrito (agregado, todos los productos) ---
    total_product_views = sum(views_by_product.values())
    total_product_cart_adds = sum(adds_by_product.values())
    view_to_cart_rate = (
        round(total_product_cart_adds / total_product_views * 100, 1) if total_product_views else 0
    )

    # --- Ticket promedio (AOV) y reparto de ingresos por canal ---
    avg_order_value = (float(combined_revenue) / combined_sales_count) if combined_sales_count else 0

    # --- Carrito: agregados vs. quitados (fricción dentro del carrito) ---
    cart_remove_total = cart_events_qs.filter(event_type='remove').count()

    # --- Rebote: sesiones con una sola página vista ---
    single_view_sessions = (PageView.objects.filter(session__in=sessions_qs)
                            .values('session').annotate(n=Count('id')).filter(n=1).count())
    bounce_rate = (single_view_sessions / visits * 100) if visits else 0

    # --- Fuentes de tráfico (referrer agrupado por canal) ---
    site_host = next((h for h in settings.ALLOWED_HOSTS if h and '*' not in h), '')
    source_counter = {}
    for ref in sessions_qs.values_list('referrer', flat=True):
        key = _classify_source(ref, site_host)
        source_counter[key] = source_counter.get(key, 0) + 1
    source_order = ['Directo', 'Instagram', 'Google', 'Facebook', 'TikTok', 'WhatsApp', 'Otro']
    source_labels, source_values = _labels_and_counts(source_counter, source_order)

    # --- Dispositivos ---
    device_counter = {}
    for ua in sessions_qs.values_list('user_agent', flat=True):
        key = _classify_device(ua)
        device_counter[key] = device_counter.get(key, 0) + 1
    device_order = ['Móvil', 'Escritorio', 'Tablet']
    device_labels, device_values = _labels_and_counts(device_counter, device_order)

    # --- Actividad por hora del día (0–23) ---
    hour_counter = {r['h']: r['c'] for r in (
        sessions_qs.annotate(h=ExtractHour('first_seen')).values('h').annotate(c=Count('id')))}
    hourly_counts = [hour_counter.get(h, 0) for h in range(24)]

    # --- Páginas más vistas (con tiempo promedio) ---
    # Solo se muestran las rutas del sistema de compras (inicio, menú, carrito,
    # checkout, confirmación): son las únicas con page_label asignado por el
    # middleware (ver PAGE_LABELS); el resto de rutas rastreadas se excluye.
    label_to_view = {label: view_name for view_name, label in PAGE_LABELS.items()}
    pages_qs = (PageView.objects.filter(entered_at__range=(start_dt, end_dt), session__is_bot=False)
                .exclude(page_label='')
                .values('page_label').annotate(views=Count('id'), avg_dur=Avg('duration_seconds'))
                .order_by('-views')[:10])
    top_pages = [{
        'path': _current_route(label_to_view.get(r['page_label'], '')) or '—',
        'label': r['page_label'],
        'views': r['views'],
        'avg_dur': round(r['avg_dur'], 1) if r['avg_dur'] is not None else None,
    } for r in pages_qs]

    return {
        'visits': visits,
        'cart_add_total': cart_add_total,
        'wishlist_add_total': wishlist_add_total,
        'avg_duration': avg_duration,
        'median_duration': median_duration,
        'abandonment_rate': round(abandonment_rate, 1),
        'abandoned_count': len(abandoned_keys),
        'abandonment_candidates': len(candidate_session_keys),
        'abandonment_window_minutes': window_minutes,
        'combined_revenue': float(combined_revenue),
        'combined_sales_count': combined_sales_count,
        'web_revenue': float(web_revenue),
        'whatsapp_revenue': float(whatsapp_revenue),
        'instagram_revenue': float(instagram_revenue),
        'web_sales_count': web_sales_count,
        'whatsapp_sales_count': whatsapp_sales_count,
        'instagram_sales_count': instagram_sales_count,
        'avg_order_value': round(avg_order_value, 2),
        'conversion_rate': round(conversion_rate, 1),
        'cart_remove_total': cart_remove_total,
        'bounce_rate': round(bounce_rate, 1),
        'view_to_cart_rate': view_to_cart_rate,
        'funnel_labels': [f['label'] for f in funnel],
        'funnel_values': [f['value'] for f in funnel],
        'sales_dates': sales_dates,
        'web_sales_series': web_series,
        'whatsapp_sales_series': whatsapp_series,
        'instagram_sales_series': instagram_series,
        'combined_sales_series': combined_series,
        'visit_dates': visit_dates,
        'visit_counts': visit_counts,
        'top_products': top_products,
        'whatsapp_clicks_total': whatsapp_clicks_total,
        'instagram_clicks_total': instagram_clicks_total,
        'whatsapp_clicks_sessions': whatsapp_clicks_sessions,
        'instagram_clicks_sessions': instagram_clicks_sessions,
        'whatsapp_click_share': whatsapp_click_share,
        'instagram_click_share': instagram_click_share,
        'source_labels': source_labels,
        'source_values': source_values,
        'device_labels': device_labels,
        'device_values': device_values,
        'hourly_counts': hourly_counts,
        'top_pages': top_pages,
    }
