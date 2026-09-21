#!/usr/bin/env python
"""
Script automatizado para migração de SQLite para PostgreSQL.
Uso: python migrate_to_postgres.py [--database-url POSTGRES_URL] [--yes]
"""
import os
import sys
import shutil
from datetime import datetime
import subprocess
from pathlib import Path
import argparse

BASE_DIR = Path(__file__).resolve().parent

def find_sqlite_db():
    """Localiza o arquivo do banco SQLite atual"""
    candidates = [
        BASE_DIR / 'devadmin' / 'data' / 'db.sqlite3',
        BASE_DIR / 'db.sqlite3',
    ]
    for c in candidates:
        if c.exists() and c.stat().st_size > 0:
            return c
    return None

def backup_sqlite(sqlite_path):
    """Cria backup do banco SQLite"""
    backup_file = sqlite_path.parent / f"db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sqlite3"
    shutil.copy2(sqlite_path, backup_file)
    print(f"✅ Backup SQLite criado: {backup_file}")
    return backup_file

def export_sqlite_data(output_file):
    """Exporta todos os dados do SQLite usando dumpdata nativo do Django"""
    print("📤 Exportando dados do SQLite com dumpdata...")
    env = os.environ.copy()
    env.pop('DATABASE_URL', None)  # Garante uso do SQLite local
    
    cmd = [
        sys.executable, "manage.py", "dumpdata",
        "--natural-foreign",
        "--natural-primary",
        "--exclude", "contenttypes",
        "--exclude", "auth.Permission",
        "--exclude", "sessions.Session",
        "--indent", "2",
        "-o", str(output_file)
    ]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro ao exportar dados: {result.stderr}")
        return False
    
    print(f"✅ Dados exportados para: {output_file} ({output_file.stat().st_size} bytes)")
    return True

def test_postgres_connection(db_url):
    """Testa se a conexão com o PostgreSQL está funcionando"""
    print(f"\n🔍 Testando conexão com PostgreSQL...")
    try:
        import dj_database_url
        import psycopg2
        cfg = dj_database_url.parse(db_url)
        conn = psycopg2.connect(
            dbname=cfg['NAME'],
            user=cfg['USER'],
            password=cfg['PASSWORD'],
            host=cfg['HOST'] or 'localhost',
            port=cfg['PORT'] or 5432,
            connect_timeout=5
        )
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"✅ Conexão bem-sucedida! {version}")
        return True
    except Exception as e:
        print(f"❌ Falha ao conectar no PostgreSQL: {e}")
        return False

def run_postgres_migrations(db_url):
    """Aplica migrações no PostgreSQL"""
    print("\n⚙️  Aplicando migrações no PostgreSQL...")
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    cmd = [sys.executable, "manage.py", "migrate", "--noinput"]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro nas migrações:\n{result.stderr}")
        return False
    print("✅ Migrações aplicadas com sucesso no PostgreSQL.")
    return True

def import_postgres_data(db_url, fixture_file):
    """Carrega dados no PostgreSQL usando loaddata"""
    print(f"\n📥 Importando dados para o PostgreSQL a partir de {fixture_file.name}...")
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    cmd = [sys.executable, "manage.py", "loaddata", str(fixture_file)]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Erro no loaddata:\n{result.stderr}")
        return False
    print(result.stdout.strip())
    print("✅ Dados importados com sucesso!")
    return True

def reset_postgres_sequences(db_url):
    """Corrige sequências autoincrement no PostgreSQL para evitar erro de ID duplicado"""
    print("\n🔄 Atualizando sequências de IDs no PostgreSQL...")
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    
    # Gera comandos SQL para resetar sequências
    cmd = [sys.executable, "manage.py", "sqlsequencereset", "habitusapp", "auth"]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip():
        sql = result.stdout
        import dj_database_url
        import psycopg2
        cfg = dj_database_url.parse(db_url)
        conn = psycopg2.connect(
            dbname=cfg['NAME'],
            user=cfg['USER'],
            password=cfg['PASSWORD'],
            host=cfg['HOST'] or 'localhost',
            port=cfg['PORT'] or 5432
        )
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(sql)
        cur.close()
        conn.close()
        print("✅ Sequências de IDs atualizadas com sucesso!")
    else:
        print("⚠️  Nenhuma sequência precisou ser atualizada.")

def verify_migration(db_url):
    """Verifica e exibe contagem de dados migrados no PostgreSQL"""
    print("\n📊 Verificando contagem de dados no PostgreSQL:")
    env = os.environ.copy()
    env['DATABASE_URL'] = db_url
    script = """
from habitusapp.models import Exercicio, Treino, Aluno, Professor, Admin, Noticia, TreinoExercicio, Notificacao, Progresso, SolicitacaoDeTreino
from django.contrib.auth.models import User

models = [User, Exercicio, Treino, Aluno, Professor, Admin, Noticia, TreinoExercicio, Notificacao, Progresso, SolicitacaoDeTreino]
for m in models:
    print(f"   ✓ {m.__name__}: {m.objects.count()} registro(s)")
"""
    cmd = [sys.executable, "manage.py", "shell", "-c", script]
    result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env, capture_output=True, text=True)
    print(result.stdout)

def main():
    parser = argparse.ArgumentParser(description="Migrador SQLite para PostgreSQL")
    parser.add_argument("--database-url", default=os.getenv("DATABASE_URL", "postgres://habitus:habituspassword@localhost:5432/habitus"),
                        help="URL de conexão com o PostgreSQL")
    parser.add_argument("--yes", "-y", action="store_true", help="Executa sem pedir confirmação")
    args = parser.parse_args()

    print("=" * 60)
    print("🚀 MIGRAÇÃO HABITUS: SQLite → PostgreSQL")
    print("=" * 60)

    # 1. Localiza SQLite
    sqlite_db = find_sqlite_db()
    if not sqlite_db:
        print("❌ Nenhum banco SQLite encontrado.")
        sys.exit(1)
    print(f"📁 Banco SQLite encontrado: {sqlite_db}")

    # 2. Backup SQLite
    backup_file = backup_sqlite(sqlite_db)

    # 3. Exporta dados
    export_file = BASE_DIR / "datadump.json"
    if not export_sqlite_data(export_file):
        sys.exit(1)

    # 4. Confirmação
    if not args.yes:
        resp = input(f"\nProsseguir com a migração para {args.database_url}? [S/n]: ")
        if resp.lower() not in ('s', 'sim', 'y', 'yes', ''):
            print("Migração cancelada pelo usuário.")
            sys.exit(0)

    # 5. Testa conexão PostgreSQL
    if not test_postgres_connection(args.database_url):
        print("\nCertifique-se de que o container PostgreSQL está em execução:")
        print("  docker compose up -d db")
        sys.exit(1)

    # 6. Migrações no PostgreSQL
    if not run_postgres_migrations(args.database_url):
        sys.exit(1)

    # 7. Importa dados
    if not import_postgres_data(args.database_url, export_file):
        sys.exit(1)

    # 8. Corrige sequences
    reset_postgres_sequences(args.database_url)

    # 9. Verificação final
    verify_migration(args.database_url)

    print("=" * 60)
    print("🎉 Migração para PostgreSQL concluída com sucesso!")
    print(f"📦 Backup SQLite salvo em: {backup_file}")
    print(f"📄 Fixture de dados salva em: {export_file}")
    print("=" * 60)

if __name__ == "__main__":
    main()