# Guia de Configuração e Execução - Habitus

Este documento contém todas as instruções para execução em contêineres Docker, persistência de dados, orientações do `.gitignore` e comandos para commit.

---

## 🚀 Como Executar em Qualquer Computador com Docker (Zero Configuração)

A forma recomendada para rodar o projeto em qualquer ambiente (Windows, Linux ou macOS) é utilizando o Docker Compose.

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) instalados na máquina.

### 1. Clonar o repositório
```bash
git clone https://github.com/alessandrojsouza/habitus-2026.git
cd habitus-2026
```

### 2. Subir os Contêineres
```bash
docker compose up -d
```

> **Automação na primeira inicialização:**
> 1. O contêiner **PostgreSQL 16** (`habitus_db`) é criado junto ao volume persistente de banco de dados (`postgres_data`).
> 2. O contêiner da **Aplicação Django** (`habitus_web`) aguarda a prontidão do banco PostgreSQL.
> 3. As migrações são executadas automaticamente via `migrate`.
> 4. Se o banco for novo, o script `entrypoint.sh` **importa automaticamente o `datadump.json`** (com todos os 49 exercícios, treinos, alunos e usuários) e atualiza as sequências de IDs.
> 5. A pasta local `devadmin/media/` é montada como volume para servir todas as imagens e vídeos dos exercícios.

### 3. Acessar a Aplicação
- **Aplicação Web:** [http://localhost:8000](http://localhost:8000)
- **Painel Administrativo:** [http://localhost:8000/admin](http://localhost:8000/admin)

---

## 🛠️ Comandos Úteis com Docker

- **Acompanhar logs da aplicação em tempo real:**
  ```bash
  docker compose logs -f web
  ```
- **Parar os contêineres:**
  ```bash
  docker compose down
  ```
- **Parar e remover volumes (atenção: apaga dados do PostgreSQL):**
  ```bash
  docker compose down -v
  ```
- **Recarregar manualmente o dump de dados iniciais:**
  ```bash
  docker compose exec web python manage.py loaddata datadump.json
  ```
- **Acessar o terminal do contêiner Django:**
  ```bash
  docker compose exec web bash
  ```
- **Acessar o Django Shell:**
  ```bash
  docker compose exec web python manage.py shell
  ```

---

## 📦 Estrutura do `.gitignore`

O arquivo `.gitignore` foi configurado para manter o repositório seguro e limpo:

* **O que NÃO é enviado ao repositório:**
  - `.env` e `.env.local` (variáveis com chaves e credenciais locais).
  - `*.sqlite3` e backups (banco local legado SQLite).
  - `__pycache__/` e arquivos compilados `.pyc`.
  - `devadmin/staticfiles/` (arquivos estáticos gerados por `collectstatic`).

* **O que É mantido no repositório:**
  - `datadump.json` (backup dos dados em formato JSON para recriação do banco em novas máquinas).
  - `devadmin/media/` (imagens e vídeos dos exercícios cadastrados).
  - `docker-compose.yml`, `Dockerfile`, `entrypoint.sh`, `.dockerignore` e `.env.example`.

---

## 📝 Como Fazer o Commit das Alterações

Para salvar as mudanças no Git e enviar ao repositório remoto:

```bash
# 1. Adicionar os arquivos alterados e novos
git add .

# 2. Conferir o status dos arquivos que serão comitados
git status

# 3. Realizar o commit
git commit -m "feat: migra para PostgreSQL e adiciona orquestracao com Docker Compose e volumes"

# 4. Enviar para a branch principal
git push origin main
```

---

## 💻 Execução Local sem Docker (Opcional)

1. Crie e ative um ambiente virtual Python (3.12+):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac ou venv\Scripts\activate no Windows
   ```
2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Crie o arquivo `.env` a partir do template:
   ```bash
   cp .env.example .env
   ```
   *(Defina `DATABASE_URL` para conectar ao PostgreSQL ou deixe em branco para usar SQLite local).*
4. Execute as migrações e inicie o servidor:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
