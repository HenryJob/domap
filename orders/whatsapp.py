"""Integración con Evolution API para enviar el detalle del pedido al cliente
por WhatsApp desde el número que el administrador conectó escaneando el QR.

Evolution corre en Docker (ver docker-compose.yml). Este módulo solo habla HTTP
con su API; nunca debe romper el checkout, así que los errores se registran en el
log y se devuelven en silencio."""
import logging
import re

from django.conf import settings

logger = logging.getLogger(__name__)


class EvolutionError(Exception):
    """Falla al hablar con Evolution API (red, credenciales o instancia)."""


class EvolutionClient:
    """Cliente mínimo de Evolution API v2 para el número de la tienda."""

    def __init__(self, instance=None):
        self.base = settings.EVOLUTION_API_URL.rstrip('/')
        self.key = settings.EVOLUTION_API_KEY
        self.instance = instance or settings.EVOLUTION_INSTANCE

    @property
    def _headers(self):
        return {'apikey': self.key, 'Content-Type': 'application/json'}

    def _request(self, method, path, payload=None):
        # Import diferido: 'requests' solo hace falta cuando WhatsApp está
        # activo, así el sitio arranca aunque la dependencia no esté instalada.
        import requests

        url = f'{self.base}{path}'
        try:
            resp = requests.request(
                method, url, json=payload, headers=self._headers, timeout=15,
            )
        except requests.RequestException as exc:
            raise EvolutionError(f'No se pudo contactar Evolution API: {exc}') from exc
        if resp.status_code >= 400:
            raise EvolutionError(
                f'Evolution API respondió {resp.status_code}: {resp.text[:300]}')
        try:
            return resp.json()
        except ValueError:
            return {}

    # --- Mensajería --------------------------------------------------------
    def send_text(self, number, text):
        """Envía un mensaje de texto. `number` en formato internacional sin '+'."""
        return self._request('POST', f'/message/sendText/{self.instance}', {
            'number': number,
            'text': text,
        })

    # --- Gestión de la instancia (conexión del número) ---------------------
    def connection_state(self):
        """Devuelve 'open' (conectado), 'connecting', 'close', o None si la
        instancia todavía no existe en Evolution."""
        try:
            data = self._request('GET', f'/instance/connectionState/{self.instance}')
        except EvolutionError:
            return None
        return (data.get('instance') or {}).get('state')

    def create_instance(self):
        """Crea la instancia (una sola vez) para poder conectar el número."""
        return self._request('POST', '/instance/create', {
            'instanceName': self.instance,
            'integration': 'WHATSAPP-BAILEYS',
            'qrcode': True,
        })

    def connect(self):
        """Pide el QR/código de emparejamiento para escanear con el WhatsApp
        del administrador. Devuelve el dict de Evolution (incluye 'base64')."""
        return self._request('GET', f'/instance/connect/{self.instance}')

    def logout(self):
        return self._request('DELETE', f'/instance/logout/{self.instance}')

    def delete_instance(self):
        return self._request('DELETE', f'/instance/delete/{self.instance}')

    def restart_instance(self):
        """Borra y recrea la instancia desde cero para forzar un QR nuevo.
        Útil cuando quedó atascada en 'connecting'/'close' sin emitir QR."""
        try:
            self.logout()
        except EvolutionError:
            pass  # puede no estar logueada; no importa
        try:
            self.delete_instance()
        except EvolutionError:
            pass  # puede no existir todavía
        return self.create_instance()


def normalize_phone(raw, country_code=None):
    """Convierte un teléfono como 'Ej. 987 654 321' o '+51 987654321' al formato
    que espera Evolution: solo dígitos con código de país (ej. '51987654321').
    Devuelve None si no hay dígitos suficientes para un número válido."""
    country_code = country_code or settings.WHATSAPP_COUNTRY_CODE
    digits = re.sub(r'\D', '', raw or '')
    if not digits:
        return None
    # '00' inicial = prefijo internacional; se descarta.
    if digits.startswith('00'):
        digits = digits[2:]
    # Número local de 9 dígitos (móvil peruano) → anteponer código de país.
    if len(digits) == 9:
        digits = f'{country_code}{digits}'
    if len(digits) < 11:
        return None
    return digits


def _soles(amount):
    return f'S/ {amount:.2f}'


def build_order_message(order):
    """Arma el texto del pedido con todos los productos, extras y totales.
    Usa markdown de WhatsApp (*negrita*)."""
    lines = [
        '🧇 *Mordé* — ¡Gracias por tu pedido! 🎉',
        '',
        f'*Pedido #{order.id}*',
        f'👤 {order.customer_name}',
        '',
        '*Tu pedido:*',
    ]
    for item in order.items.all():
        lines.append(f'• {item.quantity}x {item.product.name} — {_soles(item.line_total())}')
        for extra in item.extras.all():
            lines.append(f'   ➕ {extra.quantity}x {extra.extra.name}')

    lines += [
        '',
        f'Subtotal: {_soles(order.subtotal)}',
    ]
    if order.delivery_fee:
        lines.append(f'Delivery: {_soles(order.delivery_fee)}')
    lines += [
        f'*Total: {_soles(order.total)}*',
        '',
        f'📦 Tipo: {order.get_order_type_display()}',
    ]
    if order.order_type == 'delivery' and order.address:
        lines.append(f'📍 Dirección: {order.address}')
    lines.append(f'💳 Pago: {order.get_payment_method_display()}')
    if order.scheduled_date:
        cuando = order.scheduled_date.strftime('%d/%m/%Y')
        if order.scheduled_time:
            cuando += f" {order.scheduled_time.strftime('%H:%M')}"
        lines.append(f'🕒 Para: {cuando}')
    if order.notes:
        lines.append(f'📝 Nota: {order.notes}')

    lines += ['', '¡Ya estamos preparando todo! 🧡', 'Mordé']
    return '\n'.join(lines)


def connection_context():
    """Estado de la conexión de WhatsApp y, si hace falta, el QR para escanear.
    Lo usan tanto la página de staff como la pantalla dentro de /admin. Nunca lanza."""
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


def send_order_whatsapp(order):
    """Envía al cliente el detalle de su pedido por WhatsApp. Nunca lanza: si
    algo falla (WhatsApp apagado, número inválido, Evolution caído) lo registra
    en el log y sigue, porque el pedido ya está guardado."""
    if not settings.WHATSAPP_NOTIFY_ENABLED:
        return False
    if not settings.EVOLUTION_API_KEY:
        logger.warning('WhatsApp activo pero EVOLUTION_API_KEY está vacío; no se envía el pedido #%s', order.id)
        return False

    number = normalize_phone(order.phone)
    if not number:
        logger.warning('Pedido #%s: teléfono "%s" no es válido para WhatsApp', order.id, order.phone)
        return False

    # Captura amplia a propósito: el pedido ya está guardado, así que ni una
    # falla de red, ni 'requests' sin instalar, ni un error de Evolution deben
    # romper el checkout. Todo se registra en el log para diagnosticar.
    try:
        EvolutionClient().send_text(number, build_order_message(order))
    except Exception:
        logger.exception('No se pudo enviar el WhatsApp del pedido #%s', order.id)
        return False
    logger.info('WhatsApp del pedido #%s enviado a %s', order.id, number)
    return True
