# Docker: guía de uso local y en producción

## Requisitos

- Docker y Docker Compose instalados (Docker Desktop en Windows/Mac, o `docker` + `docker compose` en Linux).

## 1. Local (desarrollo)

1. Copia el archivo de variables de entorno:

   ```
   cp .env.example .env
   ```

2. Edita `.env` y deja:

   ```
   SECRET_KEY=cualquier-valor-para-desarrollo
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. Levanta el proyecto:

   ```
   docker compose up --build
   ```

4. Abre `http://localhost:8000`.

5. Para correr comandos de Django (migraciones, crear superusuario, etc.) dentro del contenedor:

   ```
   docker compose exec web python manage.py migrate
   docker compose exec web python manage.py createsuperuser
   ```

6. Para detener:

   ```
   docker compose down
   ```

La base de datos (`db.sqlite3`) y los archivos de `media/` se mantienen entre reinicios porque están montados como volumen/bind mount en `docker-compose.yml`.

## 2. Producción (servidor)

### 2.1 Preparar el servidor

- Instala Docker y Docker Compose en el servidor (Ubuntu/Debian: sigue la guía oficial de Docker Engine).
- Clona el repositorio en el servidor:

  ```
  git clone <url-del-repo> domap
  cd domap
  ```

### 2.2 Configurar variables de entorno

1. Copia la plantilla:

   ```
   cp .env.example .env
   ```

2. Edita `.env` con valores de producción:

   ```
   SECRET_KEY=<genera-una-clave-larga-y-secreta>
   DEBUG=False
   ALLOWED_HOSTS=tudominio.com,www.tudominio.com
   ```

   Para generar un `SECRET_KEY` seguro:

   ```
   docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

   **Nunca** reutilices el `SECRET_KEY` de desarrollo ni subas el `.env` a git (ya está en `.gitignore`).

### 2.3 Levantar el proyecto

```
docker compose up --build -d
```

El flag `-d` lo deja corriendo en segundo plano.

### 2.4 Migraciones y estáticos

Las migraciones no corren solas; ejecútalas manualmente tras cada despliegue:

```
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser   # solo la primera vez
```

Los archivos estáticos ya se recopilan durante el build (`collectstatic` está en el `Dockerfile`).

### 2.5 Exponer el sitio al público

El contenedor sirve en el puerto `8000` dentro del servidor. En producción normalmente se pone un proxy inverso (Nginx o Caddy) delante para:

- Servir en el puerto 80/443.
- Manejar HTTPS (certificado con Let's Encrypt).
- Servir `staticfiles/` y `media/` directamente (más eficiente que gunicorn).

Ejemplo mínimo de bloque Nginx apuntando al contenedor:

```nginx
server {
    listen 80;
    server_name tudominio.com;

    location /static/ {
        alias /ruta/al/volumen/static_data/;
    }

    location /media/ {
        alias /ruta/al/volumen/media_data/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

(Si prefieres no instalar Nginx en el host, se puede agregar como otro servicio dentro de `docker-compose.yml` más adelante.)

### 2.6 Actualizar el proyecto tras nuevos cambios

```
git pull
docker compose up --build -d
docker compose exec web python manage.py migrate
```

### 2.7 Ver logs / detener

```
docker compose logs -f web    # ver logs en vivo
docker compose down           # detener todo
```

## 3. WhatsApp automático (Evolution API)

Cuando un cliente hace un pedido en la web, la tienda le envía por WhatsApp el
detalle completo (productos, extras, totales, dirección, pago) **desde el número
que el administrador conecte escaneando un QR**. Esto lo hace [Evolution API](https://doc.evolution-api.com/),
que ya viene incluida en `docker-compose.yml` junto con su Postgres y Redis.

### 3.1 Configurar la clave

En `.env` define una clave secreta para Evolution (la misma la usa la API y Django):

```
EVOLUTION_API_KEY=<clave-larga-y-secreta>
WHATSAPP_NOTIFY_ENABLED=False   # se pone en True recién después de conectar el número
```

Para generar la clave:

```
docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3.2 Levantar todo

```
docker compose up --build -d
```

Esto arranca `web`, `evolution-api`, `evolution-postgres` y `evolution-redis`.
Evolution queda en `http://localhost:8080` (no lo expongas al público en producción:
déjalo solo en la red interna o detrás de Nginx con autenticación, porque da control
total del número de WhatsApp).

### 3.3 Conectar el número (escanear el QR)

1. Entra al admin como staff y ve a **`http://localhost:8000/pedidos/staff/whatsapp/`**
   (o desde *Ventas WhatsApp → Conectar WhatsApp*).
2. Aparecerá un **código QR**. En el teléfono del negocio abre
   **WhatsApp → Dispositivos vinculados → Vincular un dispositivo** y escanéalo.
3. La página detecta la conexión sola y muestra **✅ Número conectado**.

### 3.4 Activar el envío

Una vez conectado, pon en `.env`:

```
WHATSAPP_NOTIFY_ENABLED=True
```

y reinicia solo la app para que tome el cambio:

```
docker compose up -d web
```

Desde ahí, cada pedido hecho en la web le llega al cliente por WhatsApp. Si el
envío falla (número inválido, Evolution caído, etc.) **el pedido igual se guarda**;
el error solo queda en los logs (`docker compose logs -f web`).

## Notas

- La base de datos usada es SQLite (`db.sqlite3`), montada como bind mount — sirve para un tráfico bajo/medio. Si el proyecto crece, considera migrar a PostgreSQL.
- Los volúmenes `media_data`, `evolution_instances`, `evolution_postgres_data` y `evolution_redis_data` (definidos en `docker-compose.yml`) persisten aunque borres y recrees el contenedor. Solo se pierden con `docker compose down -v`. Ojo: borrar `evolution_instances` obliga a re-escanear el QR.
