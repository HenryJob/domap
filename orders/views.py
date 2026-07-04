from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from cart.cart import Cart
from cart.services import summary_context
from .forms import OrderLookupForm, ManualSaleForm, ManualSaleItemFormSet
from .models import Order, ManualSale
from .whatsapp import EvolutionClient, EvolutionError


def cart_summary_partial(request):
    """Devuelve solo el HTML del resumen del pedido, para refrescarlo por AJAX
    sin recargar la página (y así no perder lo que el cliente ya escribió en
    el formulario de Completa tu pedido)."""
    cart = Cart(request)
    return render(request, 'orders/_summary_partial.html', summary_context(cart))


def checkout(request):
    """El carrito (cart:cart_detail) ya gestiona todo el pedido en una sola
    página; esta ruta se conserva solo por compatibilidad con enlaces
    existentes (footer, favoritos guardados, etc.)."""
    return redirect('cart:cart_detail')


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    token = request.GET.get('t', '')
    owns_via_user = request.user.is_authenticated and order.user_id == request.user.id
    owns_via_token = bool(token) and token == order.access_token
    if not (owns_via_user or owns_via_token):
        raise Http404()
    return render(request, 'orders/order_success.html', {'order': order})


def order_lookup(request):
    if request.method == 'POST':
        form = OrderLookupForm(request.POST)
        if form.is_valid():
            order = Order.objects.filter(
                id=form.cleaned_data['order_number'],
                phone=form.cleaned_data['phone'],
            ).first()
            if order:
                success_url = reverse('orders:order_success', args=[order.id]) + f'?t={order.access_token}'
                return redirect(success_url)
            messages.error(request, 'No encontramos un pedido con esos datos.')
    else:
        form = OrderLookupForm()
    return render(request, 'orders/order_lookup.html', {'form': form})


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
            messages.success(request, 'Venta de WhatsApp registrada correctamente.')
            return redirect('orders:manual_sale_list')
        formset = ManualSaleItemFormSet(request.POST)
    else:
        form = ManualSaleForm()
        formset = ManualSaleItemFormSet()

    return render(request, 'orders/manual_sale_form.html', {'form': form, 'formset': formset})


@staff_member_required
def manual_sale_list(request):
    sales = ManualSale.objects.prefetch_related('items').all()[:100]
    return render(request, 'orders/manual_sale_list.html', {'sales': sales})


# --- Conexión de WhatsApp (Evolution API) ---------------------------------
def _qr_context():
    """Estado de la conexión de WhatsApp y, si hace falta, el QR para escanear.
    Devuelve un dict listo para la plantilla; nunca lanza."""
    ctx = {
        'enabled': settings.WHATSAPP_NOTIFY_ENABLED,
        'instance': settings.EVOLUTION_INSTANCE,
        'has_key': bool(settings.EVOLUTION_API_KEY),
        'state': None,
        'qr_base64': None,
        'error': None,
    }
    if not ctx['has_key']:
        ctx['error'] = 'Falta configurar EVOLUTION_API_KEY en el archivo .env.'
        return ctx

    client = EvolutionClient()
    try:
        state = client.connection_state()
        if state is None:
            # La instancia todavía no existe: créala para poder emparejar.
            client.create_instance()
            state = 'connecting'
        ctx['state'] = state
        if state != 'open':
            data = client.connect()
            ctx['qr_base64'] = data.get('base64') or (data.get('qrcode') or {}).get('base64')
    except EvolutionError as exc:
        ctx['error'] = str(exc)
    return ctx


@staff_member_required
def whatsapp_connect(request):
    """Página de staff: muestra el estado y el QR para que el administrador
    conecte su número de WhatsApp escaneándolo con su teléfono."""
    return render(request, 'orders/whatsapp_connect.html', _qr_context())


@staff_member_required
def whatsapp_state(request):
    """Endpoint JSON para que la página consulte el estado y refresque el QR
    sin recargar (polling mientras el admin escanea)."""
    ctx = _qr_context()
    return JsonResponse({
        'state': ctx['state'],
        'qr_base64': ctx['qr_base64'],
        'error': ctx['error'],
    })


@staff_member_required
@require_POST
def whatsapp_logout(request):
    """Desconecta el número actual (para conectar otro)."""
    try:
        EvolutionClient().logout()
        messages.success(request, 'WhatsApp desconectado. Escanea el QR para conectar un número.')
    except EvolutionError as exc:
        messages.error(request, f'No se pudo desconectar: {exc}')
    return redirect('orders:whatsapp_connect')
