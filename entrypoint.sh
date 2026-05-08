#!/bin/bash
set -e

# Aplica as migrações do banco de dados
echo "Aplicando migrações..."
python manage.py migrate --noinput

# Inicia o servidor
echo "Iniciando o servidor..."
exec "$@"