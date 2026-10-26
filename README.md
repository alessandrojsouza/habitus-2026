<p align="center">
  <img src="https://github.com/lades-cnat/academia-cnat/blob/main/docs/imgs/logo-habitus.png?raw=true" alt="Logo Habitus" width="120" /><br/>
  <span style="font-size: 2.5em; font-weight: bold;">Habitus</span><br/>
  <em>Plataforma de gestão de treinos e bem-estar da academia do IFRN – Campus Natal Central</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.12" />
  <img src="https://img.shields.io/badge/Django-4.2_LTS-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 4.2" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL 16" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Compose" />
  <img src="https://img.shields.io/badge/SUAP-IFRN-007A33?style=for-the-badge" alt="SUAP IFRN" />
</p>

---

## 📌 Sobre o Projeto

O **Habitus** é uma aplicação web voltada aos servidores e alunos do **IFRN – Campus Natal Central (CNAT)** que utilizam a academia do campus. O projeto foi idealizado para digitalizar e integrar rotinas de exercícios, planos de treino personalizados e avaliações físicas em um ambiente moderno, seguro e acessível.

---

## ✨ Funcionalidades

- **Autenticação Unificada com SUAP:** Login institucional integrado diretamente à API do SUAP (IFRN).
- **Gestão e Execução de Treinos:** Acompanhamento interativo do treino em tempo real com marcação de exercícios concluídos, séries, repetições e cargas.
- **Área do Professor / Instrutor:** Prescrição e edição de fichas de treino personalizadas para alunos e publicação de avisos no mural.
- **Acompanhamento Antropométrico:** Histórico de progresso físico com registro de medidas corporais, dobras cutâneas e peso.
- **Feed e Notificações:** Avisos da academia, solicitações de treino e comunicados gerais.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem & Framework:** Python 3.12 e Django 4.2 LTS
- **Banco de Dados:** PostgreSQL 16
- **Frontend:** HTML5, CSS3 responsivo e JavaScript
- **Servidor & Estáticos:** Gunicorn e WhiteNoise
- **Conteinerização:** Docker e Docker Compose
- **Integrações:** API REST do SUAP (IFRN)

---

## 🚀 Como Rodar o Projeto com Docker

O projeto está configurado para execução rápida e padronizada utilizando **Docker Compose**. O ambiente já sobe o banco de dados PostgreSQL, aplica as migrações e carrega os dados iniciais (`datadump.json`) de forma automática.

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) e [Docker Compose](https://docs.docker.com/compose/) instalados.

### 1. Clonar o repositório
```bash
git clone https://github.com/alessandrojsouza/habitus-2026.git
cd habitus-2026
```

### 2. Subir os contêineres
```bash
docker compose up -d
```

> **Automação inicial:** O script de inicialização aguarda o PostgreSQL estar pronto, executa as migrações (`migrate`), importa os 49 exercícios e dados pré-cadastrados do `datadump.json` e monta a pasta de mídias (`devadmin/media/`).

### 3. Acessar a aplicação
- **Aplicação Web:** [http://localhost:8000](http://localhost:8000)
- **Painel Administrativo:** [http://localhost:8000/admin](http://localhost:8000/admin)

### Outros comandos
```bash
# Parar os contêineres:
docker compose down
```

---

## 📄 Diagramas do Projeto

- 📊 [Diagrama de Classes](doc/Diagrama%20Classe%20-%20Habitus.png)

---

## 👨‍🏫 Professor Orientador

<p align="center">
  <img src="https://github.com/alessandrojsouza.png" width="110" style="border-radius: 50%" alt="Alessandro Souza"/><br/>
  <strong><a href="https://github.com/alessandrojsouza">Alessandro Souza</a></strong>
</p>

---

## 👨‍💻 Integrantes do Grupo

<table align="center">
  <tr>
    <td align="center">
      <img src="https://github.com/Ana-Julia-06.png" width="90" style="border-radius: 50%" alt="Ana Júlia"/><br/>
      <strong>Ana Júlia</strong><br/>
      <a href="https://github.com/Ana-Julia-06">@Ana-Julia-06</a>
    </td>
    <td align="center">
      <img src="https://github.com/K4ues.png" width="90" style="border-radius: 50%" alt="Kauê Silva"/><br/>
      <strong>Kauê Silva</strong><br/>
      <a href="https://github.com/K4ues">@K4ues</a>
    </td>
    <td align="center">
      <img src="https://github.com/micaaell.png" width="90" style="border-radius: 50%" alt="Micael Dantas"/><br/>
      <strong>Micael Dantas</strong><br/>
      <a href="https://github.com/micaaell">@micaaell</a>
    </td>
    <td align="center">
      <img src="https://github.com/taleslourenco.png" width="90" style="border-radius: 50%" alt="Tales Lourenço"/><br/>
      <strong>Tales Lourenço</strong><br/>
      <a href="https://github.com/taleslourenco">@taleslourenco</a>
    </td>
    <td align="center">
      <img src="https://github.com/ArthurPinheiroM.png" width="90" style="border-radius: 50%" alt="Arthur Pinheiro"/><br/>
      <strong>Arthur Pinheiro</strong><br/>
      <a href="https://github.com/ArthurPinheiroM">@ArthurPinheiroM</a>
    </td>
  </tr>
</table>
