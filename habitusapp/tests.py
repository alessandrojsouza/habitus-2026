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
