#!/usr/bin/env bash
# Script de despliegue para servidor Ubuntu (primera vez).
# Uso: bash deploy.sh
set -euo pipefail

echo "== 1. Instalando Docker (si no está instalado) =="
if ! command -v docker &> /dev/null; then
  sudo apt update
  sudo apt install -y ca-certificates curl gnupg

  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg

  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt update
  sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

  sudo usermod -aG docker "$USER"
  echo "Docker instalado. Si es la primera vez, cierra sesión y vuelve a entrar (o corre 'newgrp docker') para usar docker sin sudo."
else
  echo "Docker ya está instalado, se omite este paso."
fi

echo "== 2. Configurando variables de entorno (.env) =="
if [ ! -f .env ]; then
  cp .env.example .env
  SECRET_KEY=$(docker run --rm python:3.12-slim python -c "import secrets; print(secrets.token_urlsafe(50))")
  sed -i "s#^SECRET_KEY=.*#SECRET_KEY=${SECRET_KEY}#" .env
  sed -i "s#^DEBUG=.*#DEBUG=False#" .env
  echo ".env creado con un SECRET_KEY generado automáticamente."
  echo "IMPORTANTE: edita .env y ajusta ALLOWED_HOSTS con tu dominio real antes de continuar."
  read -rp "Presiona Enter cuando hayas revisado/editado .env para continuar..."
else
  echo ".env ya existe, se omite este paso (revísalo manualmente si necesitas cambiar algo)."
fi

echo "== 3. Preparando db.sqlite3 =="
# docker-compose.yml monta ./db.sqlite3 como bind mount de un archivo. Si el
# archivo no existe en el host (clon nuevo, está en .gitignore), Docker crea
# una carpeta en su lugar y SQLite falla con "unable to open database file".
if [ -d db.sqlite3 ]; then
  echo "db.sqlite3 es una carpeta (creada por error por Docker), eliminando..."
  rm -rf db.sqlite3
fi
if [ ! -f db.sqlite3 ]; then
  touch db.sqlite3
  echo "db.sqlite3 creado."
fi

echo "== 4. Construyendo y levantando el proyecto =="
docker compose up --build -d

echo "== 5. Aplicando migraciones =="
docker compose exec web python manage.py migrate

echo "== 6. Crear superusuario (opcional) =="
read -rp "¿Quieres crear un superusuario de Django ahora? (s/n): " crear_su
if [[ "$crear_su" == "s" || "$crear_su" == "S" ]]; then
  docker compose exec web python manage.py createsuperuser
fi

echo "== Listo =="
echo "El sitio está corriendo en el puerto 8000 del servidor."
echo "Verifica con: docker compose logs -f web"
echo "Recuerda poner un proxy inverso (Nginx/Caddy) delante para exponerlo en 80/443 con HTTPS."
