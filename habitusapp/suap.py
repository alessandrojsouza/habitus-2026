import logging
import requests
from datetime import datetime, date
from django.contrib.auth.models import User, Group
from django.core.files.base import ContentFile
from habitusapp.models import Aluno, Professor, Admin

logger = logging.getLogger(__name__)

SUAP_URL = 'https://suap.ifrn.edu.br'
TOKEN_PAIR_URL = f"{SUAP_URL}/api/token/pair"
USER_INFO_URL = f"{SUAP_URL}/api/rh/eu/"


def formatar_cpf(cpf_raw, matricula=''):
    """
    Formata o CPF para o padrão 'XXX.XXX.XXX-XX' (14 caracteres).
    Se não for fornecido ou for inválido, gera um identificador seguro de até 14 caracteres.
    """
    if not cpf_raw:
        digitos_matricula = ''.join(filter(str.isdigit, str(matricula)))
        return f"SUAP{digitos_matricula}"[:14]
    
    digitos = ''.join(filter(str.isdigit, str(cpf_raw)))
    if len(digitos) == 11:
        return f"{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}"
    elif len(cpf_raw) <= 14:
        return str(cpf_raw)
    else:
        return str(cpf_raw)[:14]


def autenticar_no_suap(username, password):
    """
    Autentica usuário na API do SUAP através do endpoint /api/token/pair.
    
    Retorna: (sucesso: bool, dados_usuario: dict, tokens: dict, mensagem_erro: str)
    """
    username = str(username).strip()
    password = str(password)

    if not username or not password:
        return False, None, None, "Informe a matrícula e a senha do SUAP."

    payload = {
        'username': username,
        'password': password
    }

    try:
        response = requests.post(
            TOKEN_PAIR_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
    except requests.Timeout:
        logger.error("Timeout ao tentar autenticar no SUAP.")
        return False, None, None, "Tempo de resposta do SUAP esgotado. Tente novamente mais tarde."
    except requests.RequestException as e:
        logger.error(f"Erro de conexão com o SUAP: {e}")
        return False, None, None, "Não foi possível conectar ao SUAP. Verifique sua conexão e tente novamente."

    if response.status_code == 200:
        try:
            tokens = response.json()
        except Exception:
            return False, None, None, "Resposta inesperada do SUAP. Tente novamente."

        access_token = tokens.get('access')
        suap_username = tokens.get('username') or username

        # Tenta buscar os dados cadastrais do usuário via /api/rh/eu/
        dados_usuario = {}
        if access_token:
            try:
                info_response = requests.get(
                    USER_INFO_URL,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Accept': 'application/json'
                    },
                    timeout=10
                )
                if info_response.status_code == 200:
                    dados_usuario = info_response.json()
            except Exception as e:
                logger.warning(f"Não foi possível obter dados detalhados do SUAP (/api/rh/eu/): {e}")

        # Garante dados básicos caso /api/rh/eu/ não traga tudo
        if not dados_usuario.get('identificacao'):
            dados_usuario['identificacao'] = suap_username
        if not dados_usuario.get('nome'):
            dados_usuario['nome'] = suap_username
        if not dados_usuario.get('email') and not dados_usuario.get('email_preferencial'):
            dados_usuario['email'] = f"{suap_username}@escolar.ifrn.edu.br"

        return True, dados_usuario, tokens, None

    elif response.status_code == 401:
        return False, None, None, "Matrícula ou senha do SUAP incorretos! Verifique suas credenciais no SUAP."
    elif response.status_code == 400:
        return False, None, None, "Dados inválidos enviados para a autenticação do SUAP."
    else:
        logger.error(f"Erro no SUAP (HTTP {response.status_code}): {response.text}")
        return False, None, None, f"Erro no serviço do SUAP (código {response.status_code}). Tente mais tarde."


def sincronizar_ou_criar_aluno_suap(dados_suap, senha=None):
    """
    Localiza ou cria o User e o Aluno (ou associa ao Professor/Admin existente)
    com base nas informações retornadas pelo SUAP.
    """
    matricula = str(dados_suap.get('identificacao') or dados_suap.get('username') or '').strip()
    nome = str(dados_suap.get('nome') or dados_suap.get('nome_usual') or matricula).strip()[:100]
    
    email = (
        dados_suap.get('email_preferencial') or 
        dados_suap.get('email') or 
        dados_suap.get('email_secundario') or 
        f"{matricula}@escolar.ifrn.edu.br"
    ).strip().lower()

    cpf_raw = dados_suap.get('cpf')
    cpf = formatar_cpf(cpf_raw, matricula)

    # Data de nascimento
    data_nasc_raw = dados_suap.get('data_de_nascimento')
    data_nasc = None
    if data_nasc_raw:
        try:
            data_nasc = datetime.strptime(str(data_nasc_raw)[:10], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            pass
    if not data_nasc:
        data_nasc = date(2000, 1, 1)

    foto_url = dados_suap.get('foto')

    # 1. Localizar especificamente o Aluno pela matrícula do SUAP
    user = None
    aluno_existente = Aluno.objects.filter(matricula=matricula).first()
    if aluno_existente:
        user = aluno_existente.user

    # 2. Se não achou Aluno por matrícula, busca User cujo username seja exatamente a matrícula
    if not user:
        user_matricula = User.objects.filter(username=matricula).first()
        if user_matricula and hasattr(user_matricula, 'aluno'):
            user = user_matricula
            aluno_existente = user_matricula.aluno

    # === Atualização de Aluno existente com a mesma matrícula ===
    if user and aluno_existente:
        alterado = False
        if nome and aluno_existente.nome != nome:
            aluno_existente.nome = nome
            alterado = True
        if not aluno_existente.matricula:
            aluno_existente.matricula = matricula
            alterado = True
        if not aluno_existente.foto_perfil and foto_url and foto_url.startswith('http'):
            try:
                foto_res = requests.get(foto_url, timeout=5)
                if foto_res.status_code == 200:
                    aluno_existente.foto_perfil.save(f"suap_{matricula}.jpg", ContentFile(foto_res.content), save=False)
                    alterado = True
            except Exception:
                pass
        if alterado:
            aluno_existente.save()

        return user

    # === Criação de novo Usuário e Aluno ===
    username_candidato = matricula
    if User.objects.filter(username=username_candidato).exists():
        username_candidato = f"suap_{matricula}"

    partes_nome = nome.split(' ', 1)
    primeiro_nome = partes_nome[0][:30]
    ultimo_nome = partes_nome[1][:150] if len(partes_nome) > 1 else ''

    user = User.objects.create_user(
        username=username_candidato,
        email=email,
        first_name=primeiro_nome,
        last_name=ultimo_nome
    )
    user.set_unusable_password()
    user.save()

    grupo_aluno, _ = Group.objects.get_or_create(name='Aluno')
    user.groups.add(grupo_aluno)

    # Garante que o CPF seja único para criação
    cpf_final = cpf
    if Aluno.objects.filter(cpf=cpf_final).exists():
        cpf_final = f"SUAP{matricula}"[:14]
        if Aluno.objects.filter(cpf=cpf_final).exists():
            import secrets
            cpf_final = f"S{secrets.token_hex(6)}"[:14]

    # Garante que o email de Aluno seja único
    email_aluno = email
    if Aluno.objects.filter(email=email_aluno).exists():
        email_aluno = f"{matricula}_{email_aluno}"

    aluno = Aluno.objects.create(
        user=user,
        matricula=matricula,
        nome=nome,
        cpf=cpf_final,
        data_nasc=data_nasc,
        email=email_aluno
    )

    # Tenta baixar a foto do perfil
    if foto_url and isinstance(foto_url, str) and foto_url.startswith('http'):
        try:
            foto_res = requests.get(foto_url, timeout=5)
            if foto_res.status_code == 200:
                aluno.foto_perfil.save(f"suap_{matricula}.jpg", ContentFile(foto_res.content), save=True)
        except Exception as e:
            logger.warning(f"Não foi possível salvar foto do SUAP: {e}")

    return user
