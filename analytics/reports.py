"""Agregaciones para el dashboard de analítica. Todo se calcula al vuelo
(sin Celery/cron) ya que el volumen esperado es de un negocio pequeño."""

import statistics
from datetime import timedelta

from django.conf import settings
from django.db.models import Sum, Count, Max
from django.db.models.functions import TruncDate
from django.utils import timezone

from catalog.models import Product
from orders.models import Order, OrderItem, ManualSale, ManualSaleItem
from .models import (
    VisitorSession, PageView, CartEvent, WishlistEvent, CheckoutEvent, ProductViewEvent,
    WhatsappClickEvent, InstagramClickEvent,
)


def _merge_series(*series_dicts):
    """series_dicts: lista de {date: float}. Devuelve fechas ordenadas + listas alineadas por serie."""
    all_dates = sorted(set().union(*[d.keys() for d in series_dicts]))
    return all_dates, [[float(d.get(date, 0)) for date in all_dates] for d in series_dicts]


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
    cutoff = timezone.now() - timedelta(minutes=window_minutes)
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

    # --- KPI de ventas combinadas (web + WhatsApp registrado manualmente) ---
    whatsapp_sales = ManualSale.objects.filter(sale_date__range=(start_dt, end_dt))
    web_revenue = web_orders.aggregate(s=Sum('total'))['s'] or 0
    whatsapp_revenue = whatsapp_sales.aggregate(s=Sum('total_amount'))['s'] or 0
    combined_revenue = web_revenue + whatsapp_revenue
    combined_sales_count = web_orders.count() + whatsapp_sales.count()
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
    sales_dates, (web_series, whatsapp_series) = _merge_series(web_by_day, whatsapp_by_day)
    combined_series = [w + wa for w, wa in zip(web_series, whatsapp_series)]

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

    product_names = set(views_by_product) | set(adds_by_product) | set(web_sales_by_product) | set(whatsapp_sales_by_product)
    top_products = sorted([
        {
            'name': name,
            'views': views_by_product.get(name, 0),
            'cart_adds': adds_by_product.get(name, 0),
            'sales': web_sales_by_product.get(name, 0) + whatsapp_sales_by_product.get(name, 0),
        }
        for name in product_names
    ], key=lambda p: (-p['sales'], -p['cart_adds'], -p['views']))[:10]

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
        'conversion_rate': round(conversion_rate, 1),
        'funnel_labels': [f['label'] for f in funnel],
        'funnel_values': [f['value'] for f in funnel],
        'sales_dates': sales_dates,
        'web_sales_series': web_series,
        'whatsapp_sales_series': whatsapp_series,
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
    }
