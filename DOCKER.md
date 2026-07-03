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

## Notas

- La base de datos usada es SQLite (`db.sqlite3`), montada como bind mount — sirve para un tráfico bajo/medio. Si el proyecto crece, considera migrar a PostgreSQL.
- Los volúmenes `media_data` y `static_data` (definidos en `docker-compose.yml`) persisten aunque borres y recrees el contenedor. Solo se pierden con `docker compose down -v`.
