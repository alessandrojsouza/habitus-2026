#!/bin/bash
set -e

# Garante a existência e permissões da pasta media no boot
mkdir -p /usr/src/python/app/devadmin/media
chmod -R 777 /usr/src/python/app/devadmin/media

# Aguarda o banco de dados se for PostgreSQL
if [ -n "$DATABASE_URL" ]; then
    echo "Aguardando disponibilidade do banco de dados..."
    python -c "
import sys, time
import dj_database_url
import psycopg2

db_url = '$DATABASE_URL'
if 'postgres' in db_url:
    cfg = dj_database_url.parse(db_url)
    for i in range(30):
        try:
            conn = psycopg2.connect(
                dbname=cfg['NAME'],
                user=cfg['USER'],
                password=cfg['PASSWORD'],
                host=cfg['HOST'],
                port=cfg['PORT'] or 5432,
                connect_timeout=3
            )
            conn.close()
            print('Conexão com PostgreSQL estabelecida com sucesso!')
            sys.exit(0)
        except Exception as e:
            print(f'Tentativa {i+1}/30: Aguardando PostgreSQL... ({e})')
            time.sleep(1)
    print('Não foi possível conectar ao PostgreSQL.')
    sys.exit(1)
"
fi

# Aplica as migrações do banco de dados
echo "Aplicando migrações..."
python manage.py migrate --noinput

# Carregamento automático de dados se o banco estiver vazio em uma nova máquina
if [ -f "datadump.json" ]; then
    python -c "
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'devadmin.settings.development')
django.setup()
from habitusapp.models import Exercicio
if Exercicio.objects.count() == 0:
    print('Banco novo detectado! Carregando dados iniciais de datadump.json...')
    from django.core.management import call_command
    call_command('loaddata', 'datadump.json')
    import io
    from django.db import connection
    out = io.StringIO()
    call_command('sqlsequencereset', 'habitusapp', 'auth', stdout=out)
    sql = out.getvalue()
    if sql:
        with connection.cursor() as cur:
            cur.execute(sql)
    print('Dados iniciais carregados e sequências atualizadas com sucesso!')
else:
    print(f'Banco já inicializado ({Exercicio.objects.count()} exercícios encontrados).')
"
fi

# Inicia o servidor
echo "Iniciando o servidor..."
exec "$@"