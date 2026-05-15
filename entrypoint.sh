#!/bin/bash
set -e

# Garante a existência e permissões da pasta media no boot
mkdir -p /usr/src/python/app/devadmin/media
chmod -R 777 /usr/src/python/app/devadmin/media

# Aplica as migrações do banco de dados
echo "Aplicando migrações..."
python manage.py migrate --noinput

# Inicia o servidor
echo "Iniciando o servidor..."
exec "$@"