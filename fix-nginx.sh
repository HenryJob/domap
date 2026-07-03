#!/usr/bin/env bash
# Corrige /etc/nginx/sites-available/morde: quita el bloque location /static/
# (que apuntaba a una carpeta inexistente en el host) y deja que Nginx pase
# todo a Gunicorn/Whitenoise, que ya sirve los estáticos correctamente.
# Conserva el bloque HTTPS agregado por Certbot.
set -euo pipefail

sudo tee /etc/nginx/sites-available/morde > /dev/null << 'EOF'
server {
    server_name morde.bulpon.com;

    client_max_body_size 20M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/morde.bulpon.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/morde.bulpon.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
server {
    if ($host = morde.bulpon.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name morde.bulpon.com;
    return 404; # managed by Certbot
}
EOF

sudo nginx -t
sudo systemctl restart nginx
echo "Listo. Prueba https://morde.bulpon.com"
