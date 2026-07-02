# Mordé — sitio web + sistema de analítica

Sitio de e-commerce para "Mordé" (waffles saludables a base de garbanzo, Lima, Perú), con pedidos por WhatsApp o por carrito web, y un sistema integrado de analítica que mide visitas, tiempo en página, intención de compra (carrito/favoritos) y conversión hacia ventas.

## Cómo correrlo

```bash
cd domap
venv\Scripts\activate          # PowerShell: venv\Scripts\Activate.ps1
python manage.py runserver
```

Abre http://127.0.0.1:8000/

- Usuario admin/staff ya creado: **admin / admin12345** (cámbialo en producción).
- Panel de analítica: http://127.0.0.1:8000/analytics/panel/ (requiere staff).
- Registrar venta de WhatsApp: http://127.0.0.1:8000/pedidos/staff/ventas-whatsapp/nueva/

## Estructura

- `core` — página Inicio, partials compartidos (header/footer/CTA/pasos).
- `catalog` — productos, extras/toppings, página de Menú.
- `cart` — carrito y lista de deseos en sesión (sin modelos en BD).
- `orders` — checkout web y registro manual de ventas por WhatsApp.
- `analytics` — tracking de visitas/tiempo/eventos y el dashboard.

## Recargar el catálogo de ejemplo

```bash
python manage.py seed_products
```

## Notas

- Proyecto aislado en su propio entorno virtual (`venv/`) para no afectar otros proyectos Django en esta máquina.
- Las 3 capturas de diseño originales están en `design_reference/`.
- `WHATSAPP_NUMBER`, `DELIVERY_FEE` y `ABANDONMENT_WINDOW_MINUTES` se configuran en `domap/settings.py`.
