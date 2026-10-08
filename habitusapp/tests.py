from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from habitusapp.models import Aluno, ConfirmacaoSenha


class ConfirmacaoSenhaTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='oldpassword123'
        )
        self.aluno = Aluno.objects.create(
            user=self.user,
            nome='Test User',
            cpf='12345678901',
            data_nasc='2000-01-01'
        )
        self.client = Client()

    def test_editar_perfil_senha_diferente_confirmacao(self):
        """Testa se lança erro caso nova senha e confirmação não coincidam"""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.post(reverse('editar_perfil'), {
            'nome': 'Test User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'data_nasc': '2000-01-01',
            'new_password': 'newpassword123',
            'confirm_password': 'differentpassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'As senhas digitadas não coincidem.')
        self.assertEqual(ConfirmacaoSenha.objects.count(), 0)

    def test_editar_perfil_senha_curta(self):
        """Testa se lança erro caso a nova senha tenha menos de 6 caracteres"""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.post(reverse('editar_perfil'), {
            'nome': 'Test User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'data_nasc': '2000-01-01',
            'new_password': '123',
            'confirm_password': '123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A nova senha deve ter no mínimo 6 caracteres.')
        self.assertEqual(ConfirmacaoSenha.objects.count(), 0)

    def test_solicitacao_mudanca_senha_envia_email_e_cria_token(self):
        """Testa envio de email e criação de token ao alterar a senha em editar_perfil"""
        self.client.login(username='testuser', password='oldpassword123')
        response = self.client.post(reverse('editar_perfil'), {
            'nome': 'Test User',
            'username': 'testuser',
            'email': 'testuser@example.com',
            'data_nasc': '2000-01-01',
            'new_password': 'newpassword123',
            'confirm_password': 'newpassword123',
        })
        self.assertRedirects(response, reverse('meus_dados'))

        # Verifica se o token foi criado no banco
        self.assertEqual(ConfirmacaoSenha.objects.filter(user=self.user).count(), 1)
        confirmacao = ConfirmacaoSenha.objects.get(user=self.user)
        self.assertEqual(confirmacao.nova_senha, 'newpassword123')

        # Verifica se a senha original do usuário AINDA NÃO foi alterada
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123'))
        self.assertFalse(self.user.check_password('newpassword123'))

        # Verifica se o email de confirmação foi enviado
        self.assertEqual(len(mail.outbox), 1)
        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.to, ['testuser@example.com'])
        self.assertIn('Confirme a alteração de sua senha', sent_email.subject)
        self.assertIn(confirmacao.token, sent_email.body)

    def test_confirmar_senha_sucesso_usuario_logado(self):
        """Testa confirmação via link quando usuário está logado"""
        self.client.login(username='testuser', password='oldpassword123')
        confirmacao = ConfirmacaoSenha.objects.create(
            user=self.user,
            nova_senha='newpassword123'
        )
        url = reverse('confirmar_senha', args=[confirmacao.token])
        
        response = self.client.get(url)
        self.assertRedirects(response, reverse('meus_dados'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        self.assertEqual(ConfirmacaoSenha.objects.filter(user=self.user).count(), 0)

    def test_confirmar_senha_sucesso_deslogado(self):
        """Testa confirmação via link quando usuário abre link sem estar logado"""
        confirmacao = ConfirmacaoSenha.objects.create(
            user=self.user,
            nova_senha='newpassword123'
        )
        url = reverse('confirmar_senha', args=[confirmacao.token])
        
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login'))

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword123'))
        self.assertEqual(ConfirmacaoSenha.objects.filter(user=self.user).count(), 0)

    def test_confirmar_senha_token_invalido(self):
        """Testa comportamento com token inválido"""
        url = reverse('confirmar_senha', args=['token-inexistente'])
        response = self.client.get(url)
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('oldpassword123'))


from unittest.mock import patch, MagicMock
from habitusapp.suap import autenticar_no_suap, sincronizar_ou_criar_aluno_suap, formatar_cpf


class SuapAuthTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_formatar_cpf(self):
        self.assertEqual(formatar_cpf('12345678901'), '123.456.789-01')
        self.assertEqual(formatar_cpf('123.456.789-01'), '123.456.789-01')
        self.assertEqual(formatar_cpf('', '20231011110020'), 'SUAP2023101111')

    @patch('requests.post')
    @patch('requests.get')
    def test_autenticar_no_suap_sucesso(self, mock_get, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            'access': 'fake_access_token',
            'refresh': 'fake_refresh_token',
            'username': '20231011110020'
        }
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            'identificacao': '20231011110020',
            'nome': 'Aluno Teste SUAP',
            'email': 'aluno@escolar.ifrn.edu.br',
            'cpf': '11122233344',
            'data_de_nascimento': '2002-05-15',
            'foto': None
        }
        mock_get.return_value = mock_get_resp

        sucesso, dados, tokens, erro = autenticar_no_suap('20231011110020', 'senha123')
        self.assertTrue(sucesso)
        self.assertIsNone(erro)
        self.assertEqual(tokens['access'], 'fake_access_token')
        self.assertEqual(dados['identificacao'], '20231011110020')
        self.assertEqual(dados['nome'], 'Aluno Teste SUAP')

    @patch('requests.post')
    def test_autenticar_no_suap_credenciais_invalidas(self, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 401
        mock_post.return_value = mock_post_resp

        sucesso, dados, tokens, erro = autenticar_no_suap('20231011110020', 'senha_errada')
        self.assertFalse(sucesso)
        self.assertIn('incorretos', erro)

    def test_sincronizar_ou_criar_aluno_suap_cria_novo(self):
        dados_suap = {
            'identificacao': '20231011110020',
            'nome': 'Novo Aluno SUAP',
            'email': 'novoaluno@escolar.ifrn.edu.br',
            'cpf': '99988877766',
            'data_de_nascimento': '2003-04-10',
            'foto': None
        }
        user = sincronizar_ou_criar_aluno_suap(dados_suap)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, '20231011110020')
        self.assertTrue(hasattr(user, 'aluno'))
        self.assertEqual(user.aluno.matricula, '20231011110020')
        self.assertEqual(user.aluno.nome, 'Novo Aluno SUAP')
        self.assertTrue(user.groups.filter(name='Aluno').exists())

    @patch('habitusapp.views.viewsUsuario.autenticar_no_suap')
    def test_login_view_suap_sucesso(self, mock_auth):
        mock_auth.return_value = (
            True,
            {
                'identificacao': '20231011110099',
                'nome': 'Aluno Login View',
                'email': 'alunologin@escolar.ifrn.edu.br',
                'cpf': '55544433322',
                'data_de_nascimento': '2001-01-01',
                'foto': None
            },
            {'access': 'tok_acc', 'refresh': 'tok_ref'},
            None
        )

        response = self.client.post(reverse('login'), {
            'tipo_login': 'suap',
            'email': '20231011110099',
            'senha': 'senha_correta_suap'
        })
        self.assertRedirects(response, reverse('feed'))
        self.assertEqual(self.client.session.get('suap_access_token'), 'tok_acc')

    @patch('habitusapp.views.viewsUsuario.autenticar_no_suap')
    def test_login_view_suap_falha(self, mock_auth):
        mock_auth.return_value = (
            False,
            None,
            None,
            'Matrícula ou senha do SUAP incorretos! Verifique suas credenciais no SUAP.'
        )

        response = self.client.post(reverse('login'), {
            'tipo_login': 'suap',
            'email': '20231011110099',
            'senha': 'senha_incorreta'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'incorretos')

