from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db.models import ProtectedError, Q
from django.shortcuts import get_object_or_404, redirect, render

from analytics.reports import resolve_dashboard_context
from catalog.models import Extra, Product
from orders.forms import ManualSaleForm, ManualSaleItemFormSet
from orders.models import DeliveryZone, ManualSale, Order
from orders.whatsapp import connection_context

from .forms import DeliveryZoneForm, ExtraForm, OrderStatusForm, ProductForm

PER_PAGE = 20


def _paginate(request, queryset, per_page=PER_PAGE):
    """Pagina un queryset y arma la querystring sin 'page', para que los
    enlaces de paginación conserven los filtros activos."""
    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))
    querystring = request.GET.copy()
    querystring.pop('page', None)
    return page_obj, querystring.urlencode()


@staff_member_required
def dashboard(request):
    context = {
        'product_count': Product.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'zone_count': DeliveryZone.objects.filter(active=True).count(),
        'whatsapp_state': connection_context()['state'],
    }
    return render(request, 'panel/dashboard.html', context)


@staff_member_required
def analytics(request):
    context = resolve_dashboard_context(request)
    context['active_nav'] = 'analitica'
    return render(request, 'panel/analytics.html', context)


# --- Productos --------------------------------------------------------------
@staff_member_required
def product_list(request):
    q = request.GET.get('q', '').strip()
    is_combo = request.GET.get('is_combo', '')
    is_active = request.GET.get('is_active', '')

    products = Product.objects.all()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(description__icontains=q))
    if is_combo in ('1', '0'):
        products = products.filter(is_combo=bool(int(is_combo)))
    if is_active in ('1', '0'):
        products = products.filter(is_active=bool(int(is_active)))

    page_obj, querystring = _paginate(request, products)
    return render(request, 'panel/product_list.html', {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'querystring': querystring,
        'q': q,
        'is_combo': is_combo,
        'is_active': is_active,
        'active_nav': 'productos',
    })


@staff_member_required
def product_form(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto guardado correctamente.')
            return redirect('panel:product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'panel/product_form.html', {'form': form, 'product': product, 'active_nav': 'productos'})


@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, f'Producto "{product.name}" eliminado.')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{product.name}": tiene pedidos asociados. '
                'Desactívalo en vez de eliminarlo.')
        return redirect('panel:product_list')
    return render(request, 'panel/confirm_delete.html', {
        'object': product, 'cancel_url': 'panel:product_list', 'active_nav': 'productos',
    })


# --- Extras ------------------------------------------------------------------
@staff_member_required
def extra_list(request):
    q = request.GET.get('q', '').strip()
    is_active = request.GET.get('is_active', '')

    extras = Extra.objects.all()
    if q:
        extras = extras.filter(name__icontains=q)
    if is_active in ('1', '0'):
        extras = extras.filter(is_active=bool(int(is_active)))

    page_obj, querystring = _paginate(request, extras)
    return render(request, 'panel/extra_list.html', {
        'page_obj': page_obj,
        'extras': page_obj.object_list,
        'querystring': querystring,
        'q': q,
        'is_active': is_active,
        'active_nav': 'extras',
    })


@staff_member_required
def extra_form(request, pk=None):
    extra = get_object_or_404(Extra, pk=pk) if pk else None
    if request.method == 'POST':
        form = ExtraForm(request.POST, instance=extra)
        if form.is_valid():
            form.save()
            messages.success(request, 'Extra guardado correctamente.')
            return redirect('panel:extra_list')
    else:
        form = ExtraForm(instance=extra)
    return render(request, 'panel/extra_form.html', {'form': form, 'extra': extra, 'active_nav': 'extras'})


@staff_member_required
def extra_delete(request, pk):
    extra = get_object_or_404(Extra, pk=pk)
    if request.method == 'POST':
        try:
            extra.delete()
            messages.success(request, f'Extra "{extra.name}" eliminado.')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{extra.name}": tiene pedidos asociados. '
                'Desactívalo en vez de eliminarlo.')
        return redirect('panel:extra_list')
    return render(request, 'panel/confirm_delete.html', {
        'object': extra, 'cancel_url': 'panel:extra_list', 'active_nav': 'extras',
    })


# --- Pedidos -------------------------------------------------------------
@staff_member_required
def order_list(request):
    q = request.GET.get('q', '').strip()
    phone = request.GET.get('phone', '').strip()
    order_type = request.GET.get('order_type', '')
    zone_id = request.GET.get('zone', '')
    status = request.GET.get('status', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    orders = Order.objects.select_related('delivery_zone').all()
    if q:
        orders = orders.filter(customer_name__icontains=q)
    if phone:
        orders = orders.filter(phone__icontains=phone)
    if order_type:
        orders = orders.filter(order_type=order_type)
    if zone_id:
        orders = orders.filter(delivery_zone_id=zone_id)
    if status:
        orders = orders.filter(status=status)
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    page_obj, querystring = _paginate(request, orders)
    return render(request, 'panel/order_list.html', {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'querystring': querystring,
        'q': q,
        'phone': phone,
        'order_type': order_type,
        'zone_id': zone_id,
        'status': status,
        'date_from': date_from,
        'date_to': date_to,
        'order_type_choices': Order.ORDER_TYPE_CHOICES,
        'status_choices': Order.STATUS_CHOICES,
        'zones': DeliveryZone.objects.all(),
        'active_nav': 'pedidos',
    })


@staff_member_required
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related('items__product', 'items__extras__extra'), pk=pk)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, f'Estado del pedido #{order.id} actualizado.')
            return redirect('panel:order_detail', pk=order.pk)
    else:
        form = OrderStatusForm(instance=order)
    return render(request, 'panel/order_detail.html', {'order': order, 'form': form, 'active_nav': 'pedidos'})


# --- Zonas de delivery -------------------------------------------------------
@staff_member_required
def zone_list(request):
    q = request.GET.get('q', '').strip()
    is_active = request.GET.get('is_active', '')

    zones = DeliveryZone.objects.all()
    if q:
        zones = zones.filter(name__icontains=q)
    if is_active in ('1', '0'):
        zones = zones.filter(active=bool(int(is_active)))

    page_obj, querystring = _paginate(request, zones)
    return render(request, 'panel/zone_list.html', {
        'page_obj': page_obj,
        'zones': page_obj.object_list,
        'querystring': querystring,
        'q': q,
        'is_active': is_active,
        'active_nav': 'zonas',
    })


@staff_member_required
def zone_form(request, pk=None):
    zone = get_object_or_404(DeliveryZone, pk=pk) if pk else None
    if request.method == 'POST':
        form = DeliveryZoneForm(request.POST, instance=zone)
        if form.is_valid():
            form.save()
            messages.success(request, 'Zona de delivery guardada correctamente.')
            return redirect('panel:zone_list')
    else:
        form = DeliveryZoneForm(instance=zone)
    return render(request, 'panel/zone_form.html', {'form': form, 'zone': zone, 'active_nav': 'zonas'})


@staff_member_required
def zone_delete(request, pk):
    zone = get_object_or_404(DeliveryZone, pk=pk)
    if request.method == 'POST':
        try:
            zone.delete()
            messages.success(request, f'Zona "{zone.name}" eliminada.')
        except ProtectedError:
            messages.error(
                request,
                f'No se puede eliminar "{zone.name}": tiene pedidos asociados. '
                'Desactívala en vez de eliminarla.')
        return redirect('panel:zone_list')
    return render(request, 'panel/confirm_delete.html', {
        'object': zone, 'cancel_url': 'panel:zone_list', 'active_nav': 'zonas',
    })


# --- WhatsApp -----------------------------------------------------------
@staff_member_required
def whatsapp(request):
    ctx = connection_context()
    ctx['active_nav'] = 'whatsapp'
    return render(request, 'panel/whatsapp.html', ctx)


# --- Ventas manuales (WhatsApp / Instagram) ----------------------------------
@staff_member_required
def manual_sale_list(request):
    channel = request.GET.get('channel', '')

    sales = ManualSale.objects.prefetch_related('items').all()
    if channel:
        sales = sales.filter(channel=channel)

    page_obj, querystring = _paginate(request, sales)
    return render(request, 'panel/manual_sale_list.html', {
        'page_obj': page_obj,
        'sales': page_obj.object_list,
        'querystring': querystring,
        'channel': channel,
        'channel_choices': ManualSale.CHANNEL_CHOICES,
        'active_nav': 'ventas_manuales',
    })


@staff_member_required
def manual_sale_create(request):
    if request.method == 'POST':
        form = ManualSaleForm(request.POST)
        if form.is_valid():
            sale = form.save(commit=False)
            sale.logged_by = request.user
            sale.save()
            formset = ManualSaleItemFormSet(request.POST, instance=sale)
            if formset.is_valid():
                formset.save()
            messages.success(request, 'Venta registrada correctamente.')
            return redirect('panel:manual_sale_list')
        formset = ManualSaleItemFormSet(request.POST)
    else:
        form = ManualSaleForm()
        formset = ManualSaleItemFormSet()

    return render(request, 'panel/manual_sale_form.html', {
        'form': form, 'formset': formset, 'active_nav': 'ventas_manuales',
    })
