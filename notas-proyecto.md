# Notas del proyecto — Mordé

Resumen del estado actual para retomar el trabajo en cualquier momento. Última actualización: 2026-06-30.

## Qué es esto

Sitio de e-commerce para "Mordé" (waffles saludables a base de garbanzo, Lima, Perú), construido desde cero a partir de 3 capturas de diseño (Inicio, Menú, Pedidos), con pedidos por WhatsApp o por carrito web, y un sistema integrado de analítica que mide visitas, tiempo en página, intención de compra (carrito/favoritos), abandono de carrito y conversión hacia ventas (web + WhatsApp registrado manualmente).

Las 3 capturas originales están en `design_reference/`.

## Qué se hizo

### Estructura del proyecto
- Proyecto Django 5.1 nuevo (`domap/`), aislado en su propio entorno virtual (`venv/`) para no afectar el otro proyecto Django de esta máquina (`librarymanagement`, que usa Django 3.0.5 y ya no corre bajo el Python 3.13 instalado actualmente — eso ya estaba roto antes de tocar nada).
- 5 apps: `core` (Inicio + partials compartidos), `catalog` (productos/extras + Menú), `cart` (carrito y favoritos en sesión, sin modelos en BD), `orders` (checkout web + registro manual de ventas WhatsApp), `analytics` (tracking + dashboard).
- Stack clásico: templates server-rendered + Bootstrap 5 + JS vanilla. Sin DRF, sin SPA, sin Celery/Redis (negocio pequeño, no hace falta esa infraestructura).

### Catálogo y sitio
- Productos, extras/combos cargados con `python manage.py seed_products` (datos tomados directo de las capturas: precios, nombres, descripciones).
- Las 3 páginas (Inicio, Menú, Pedidos) replican el diseño de las capturas, con los mismos tokens visuales (café `#2e1c12`, crema `#faf3ea`, ámbar `#d98e3f`, botones tipo píldora).
- Carrito y lista de deseos viven en la sesión de Django (no en BD) porque son estado efímero antes del checkout.
- Al hacer clic en "Pedir" se abre un modal para elegir cantidad del producto **y cantidad de cada topping/extra por separado** (ej. "2x Miel"), no solo una casilla de sí/no.
- El resumen del pedido (carrito) permite eliminar líneas y cambiar cantidad con botones +/−, sin recargar la página completa (ver decisión más abajo).

### Checkout y ventas
- `Order` / `OrderItem` / `OrderItemExtra` (con cantidad propia por extra) para pedidos completados por la web.
- `ManualSale` / `ManualSaleItem`: el staff registra a mano las ventas cerradas por WhatsApp (con un código corto opcional de sesión para correlacionarlas), para que cuenten en la conversión total.
- Formulario de checkout con: tipo de pedido (delivery/recojo), dirección, fecha/hora, método de pago, notas.

### Analítica
- `TrackingMiddleware` registra cada sesión de visitante y cada vista de página (excluyendo `/admin/`, `/static/`, `/media/`, `/analytics/`).
- Beacon JS (`navigator.sendBeacon`) mide el tiempo real en cada página al salir/cambiar de pestaña.
- Eventos separados para: agregar/quitar del carrito, agregar/quitar de favoritos, inicio de checkout, vista de producto, clic en botón de WhatsApp.
- Detección simple de bots por user-agent (excluidos de todas las métricas).
- Dashboard en `/analytics/panel/` (solo staff): visitas en el tiempo, tiempo promedio/mediano por página, carrito vs. favoritos, tasa de abandono de carrito, embudo de conversión (visitas → carrito → checkout → completado), ventas en el tiempo (web + WhatsApp combinadas), tabla de productos más vistos/agregados/vendidos. Todo calculado al vuelo con consultas ORM (sin tareas programadas).

## Decisiones tomadas (y por qué)

- **Venv propio en vez de instalar Django globalmente**: evita romper el otro proyecto Django de la máquina.
- **Carrito en sesión, no en BD**: es estado temporal sin valor una vez convertido en `Order`; evita tablas y migraciones de más.
- **`Order.session_key` es un `CharField` plano, no una FK** a `VisitorSession`: mantiene la app de analítica desacoplada de la app transaccional (`orders`), comparando por valor en vez de relación.
- **Ventas de WhatsApp = registro manual del staff**: no hay forma de rastrear WhatsApp automáticamente, así que se valida con un formulario protegido (`staff_member_required`) y un código corto opcional para correlacionar con la sesión web.
- **Abandono/embudo calculados al vuelo, no con tareas programadas**: no hay Celery/cron en este proyecto; al volumen de un negocio pequeño, las consultas directas en el dashboard son suficientes.
- **Toppings/extras con cantidad**: se guardan como una lista plana con repeticiones (ej. `[3, 3, 5]` = 2x extra-3 + 1x extra-5) y se agrupan al mostrarlos, en vez de cambiar a una estructura más compleja — cambio mínimo que ya daba el resultado pedido.
- **Resumen del pedido se refresca por AJAX, no recargando la página**: al principio los botones +/−/eliminar hacían `location.reload()`, pero eso borraba lo que el cliente ya había escrito en el formulario (nombre, dirección, etc.). Se cambió a un endpoint que devuelve solo el HTML del resumen (`/pedidos/resumen-parcial/`) y se reemplaza con JS, dejando el formulario intacto.
- **Cache-busting con `STATIC_VERSION`**: para que el navegador del cliente no siga sirviendo una versión vieja de `cart.js`/`morde.css` desde caché cada vez que se actualizan.

## Bugs reales encontrados y corregidos durante el desarrollo

1. La cookie CSRF no se generaba en la primera visita (el `{% csrf_token %}` solo aparecía dentro del formulario de checkout cuando el carrito no estaba vacío) → los botones de "Pedir"/favoritos fallaban en silencio. Se agregó un `<form hidden>{% csrf_token %}</form>` en `base.html`.
2. El embudo de conversión no excluía sesiones de bots en la etapa "completado (web)", a diferencia del resto de etapas. Corregido en `analytics/reports.py`.
3. **El bug más serio**: el formulario de checkout nunca definía `forms.RadioSelect` para "tipo de pedido" y "método de pago", así que Django usaba un `<select>` (dropdown) por defecto, pero la plantilla los recorría como si fueran radios — esto renderizaba `<option>` sueltas fuera de un `<select>`, que el navegador no puede seleccionar y a veces duplica visualmente. Se corrigió especificando el widget correcto y rediseñando como botones tipo píldora (patrón `btn-check` + `:checked`).
4. No había forma de eliminar ni cambiar cantidad en el resumen del pedido — se agregó.
5. Los toppings no se podían asociar a un producto específico al pedirlo — se agregó el modal de selección con contador por topping.

## Qué falta / pendiente

- **Seguridad para producción**: `DEBUG=True`, `SECRET_KEY` insegura hardcodeada, `ALLOWED_HOSTS` limitado a localhost — nada de esto está listo para desplegar tal cual.
- **Usuario admin con contraseña por defecto** (`admin` / `admin12345`) — cambiar antes de usar en serio.
- **Número de WhatsApp es un placeholder** (`51999999999` en `settings.py`) — falta poner el real.
- **Sin suite de tests automatizada**: todo se verificó manualmente con `curl` y revisiones de código durante el desarrollo, no hay `pytest`/`unittest` escritos.
- **Sin pasarela de pago real**: "Yape/Plin/Tarjeta" son solo etiquetas en el formulario, no hay integración de cobro.
- **Sin notificaciones** (email/SMS) al cliente o al negocio cuando entra un pedido.
- **La cuota de delivery no se recalcula dinámicamente** en el resumen si el cliente cambia de "Delivery" a "Recojo" antes de enviar el formulario (se ve el valor inicial hasta que se envía).
- **Sin paginación** en la lista de ventas WhatsApp ni en la tabla de productos del dashboard — puede volverse larga si crece el negocio.
- **No probado en dispositivos móviles reales** (el CSS es responsive vía Bootstrap, pero no se verificó en un viewport/dispositivo real).
- **Imágenes de productos**: si no se sube una imagen en el admin, se usa una foto de stock de Unsplash como placeholder.

## Cómo correrlo

```bash
cd domap
venv\Scripts\activate
python manage.py runserver
```

Más detalles en `README.md`.
