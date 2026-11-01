from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from habitusapp.models import Aluno, ConfirmacaoSenha

from django.template.context import BaseContext
def _fixed_base_copy(self):
    duplicate = object.__new__(self.__class__)
    duplicate.__dict__.update(self.__dict__)
    duplicate.dicts = self.dicts[:]
    return duplicate
BaseContext.__copy__ = _fixed_base_copy



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

    def test_login_page_renders_only_suap_option_and_matricula(self):
        """Verifica se na página de login os botões convencionais foram removidos e o placeholder é Matrícula"""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        
        # Placeholder Matrícula presente
        self.assertIn('placeholder="Matrícula"', content)
        # Botão SUAP presente
        self.assertIn('btn-suap', content)
        self.assertIn('Entrar com SUAP', content)
        
        # Botões de entrar convencional e criar conta / cadastrar removidos
        self.assertNotIn('btn-principal', content)
        self.assertNotIn('btn-secundario', content)
        self.assertNotIn('Criar Conta', content)
        self.assertNotIn('class="ou-linha"', content)

    @patch('habitusapp.views.viewsUsuario.autenticar_no_suap')
    def test_login_com_enter_autentica_automaticamente_com_suap(self, mock_auth):
        """Testa se submeter o formulário sem clicar em botão (apenas tecla Enter) autentica pelo SUAP"""
        mock_auth.return_value = (
            True,
            {
                'identificacao': '20231011110088',
                'nome': 'Aluno Enter Test',
                'email': 'alunoenter@escolar.ifrn.edu.br',
                'cpf': '12312312312',
                'data_de_nascimento': '2001-01-01',
                'foto': None
            },
            {'access': 'acc_enter', 'refresh': 'ref_enter'},
            None
        )

        # Ao apertar Enter no input, tipicamente são enviados os campos 'matricula' e 'senha'
        response = self.client.post(reverse('login'), {
            'matricula': '20231011110088',
            'senha': 'senha_suap_enter'
        })
        self.assertRedirects(response, reverse('feed'))
        mock_auth.assert_called_once_with('20231011110088', 'senha_suap_enter')


import datetime
from habitusapp.models import Treino, Progresso, Professor


class ExcluirTreinoProgressoTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='aluno_teste',
            email='aluno@example.com',
            password='password123'
        )
        self.aluno = Aluno.objects.create(
            user=self.user,
            nome='Aluno Teste',
            cpf='11122233344',
            data_nasc='2000-01-01'
        )

    def test_excluir_treino_unico_zera_contagem_e_concluidos(self):
        """Ao excluir o único treino do usuário, a contagem de sessões e os concluídos associados são zerados."""
        self.client.login(username='aluno_teste', password='password123')

        treino = Treino.objects.create(
            nome='Treino A',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),  # 10 dias
            usuario=self.user
        )

        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=10,
            concluidos=3,
            ultimo_treino_id=treino.id,
            dias_treinados=[
                {'date': '2026-10-02', 'treino_id': treino.id, 'nome': treino.nome},
                {'date': '2026-10-03', 'treino_id': treino.id, 'nome': treino.nome},
                {'date': '2026-10-04', 'treino_id': treino.id, 'nome': treino.nome},
            ]
        )

        # Exclui o treino via POST
        response = self.client.post(reverse('excluir_treino', args=[treino.id]))
        self.assertRedirects(response, reverse('treinos'))

        self.assertEqual(Treino.objects.filter(id=treino.id).count(), 0)

        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 0)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])
        self.assertIsNone(progresso.ultimo_treino_id)

        # Verifica na página de treinos o que é mostrado para o usuário
        resp_treinos = self.client.get(reverse('treinos'))
        self.assertContains(resp_treinos, '0 / 0 sessões')

    def test_excluir_treino_multiplo_subtrai_apenas_concluidos_e_sessao_associadas(self):
        """Ao excluir um treino específico entre vários, apenas suas sessões e concluídos são removidos."""
        self.client.login(username='aluno_teste', password='password123')

        treino_a = Treino.objects.create(
            nome='Treino A',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),  # 10 dias
            usuario=self.user
        )
        treino_b = Treino.objects.create(
            nome='Treino B',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 21),  # 20 dias
            usuario=self.user
        )

        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=15,  # (10 + 20) / 2
            concluidos=3,        # 2 do Treino A e 1 do Treino B
            ultimo_treino_id=treino_a.id,
            dias_treinados=[
                {'date': '2026-10-02', 'treino_id': treino_a.id, 'nome': treino_a.nome},
                {'date': '2026-10-03', 'treino_id': treino_a.id, 'nome': treino_a.nome},
                {'date': '2026-10-04', 'treino_id': treino_b.id, 'nome': treino_b.nome},
            ]
        )

        # Exclui apenas o Treino A
        response = self.client.post(reverse('excluir_treino', args=[treino_a.id]))
        self.assertRedirects(response, reverse('treinos'))

        self.assertEqual(Treino.objects.filter(id=treino_a.id).count(), 0)
        self.assertEqual(Treino.objects.filter(id=treino_b.id).count(), 1)

        progresso.refresh_from_db()
        # Resta apenas o Treino B (20 dias)
        self.assertEqual(progresso.progresso_valor, 20)
        # 3 concluídos - 2 do treino A = 1 concluído
        self.assertEqual(progresso.concluidos, 1)
        self.assertEqual(len(progresso.dias_treinados), 1)
        self.assertEqual(progresso.dias_treinados[0]['treino_id'], treino_b.id)
        self.assertIsNone(progresso.ultimo_treino_id)

        # Verifica na página de treinos o que é mostrado para o usuário
        resp_treinos = self.client.get(reverse('treinos'))
        self.assertContains(resp_treinos, '1 / 20 sessões')

    def test_excluir_treino_professor_atualiza_progresso_do_aluno(self):
        """Ao professor excluir treino de um aluno, o progresso do aluno é devidamente atualizado."""
        user_prof = User.objects.create_user(
            username='prof_teste',
            email='prof@example.com',
            password='password123'
        )
        professor = Professor.objects.create(
            user=user_prof,
            nome='Prof Teste',
            email='prof@example.com',
            cpf='99988877766',
            data_nasc='1980-01-01',
            data_admissao='2020-01-01'
        )

        treino = Treino.objects.create(
            nome='Treino Aluno',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 16),  # 15 dias
            usuario=self.user,
            professor=professor
        )

        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=15,
            concluidos=2,
            dias_treinados=[
                {'date': '2026-10-02', 'treino_id': treino.id, 'nome': treino.nome},
                {'date': '2026-10-03', 'treino_id': treino.id, 'nome': treino.nome},
            ]
        )

        self.client.login(username='prof_teste', password='password123')
        response = self.client.post(
            reverse('excluir_treino_professor', kwargs={'treino_id': treino.id, 'aluno_id': self.aluno.id})
        )
        self.assertRedirects(response, reverse('gerenciar_treinos', kwargs={'aluno_id': self.aluno.id}))

        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 0)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])

    def test_apagar_todos_treinos_zera_progresso(self):
        """Ao apagar todos os treinos em configuracoes, zera sessões e concluídos."""
        self.client.login(username='aluno_teste', password='password123')

        t1 = Treino.objects.create(
            nome='Treino 1',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),
            usuario=self.user
        )
        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=10,
            concluidos=2,
            dias_treinados=[{'date': '2026-10-02', 'treino_id': t1.id, 'nome': t1.nome}]
        )

        response = self.client.post(reverse('apagar_todos_treinos'))
        self.assertRedirects(response, reverse('configuracoes'))

        self.assertEqual(Treino.objects.filter(usuario=self.user).count(), 0)
        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 0)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])

    def test_excluir_treino_quando_treino_restante_tem_zero_concluidos(self):
        """Ao excluir um treino concluído, o treino restante com 0 concluídos mantém suas sessões atribuídas e concluídos zerado."""
        self.client.login(username='aluno_teste', password='password123')

        treino_a = Treino.objects.create(
            nome='Treino A',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),  # 10 dias
            usuario=self.user
        )
        treino_b = Treino.objects.create(
            nome='Treino B',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 21),  # 20 dias
            usuario=self.user
        )

        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=15,  # (10 + 20) / 2
            concluidos=2,        # 2 do Treino A, 0 do Treino B
            ultimo_treino_id=treino_a.id,
            dias_treinados=[
                {'date': '2026-10-02', 'treino_id': treino_a.id, 'nome': treino_a.nome},
                {'date': '2026-10-03', 'treino_id': treino_a.id, 'nome': treino_a.nome},
            ]
        )

        response = self.client.post(reverse('excluir_treino', args=[treino_a.id]))
        self.assertRedirects(response, reverse('treinos'))

        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 20)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])

        resp_treinos = self.client.get(reverse('treinos'))
        self.assertContains(resp_treinos, '0 / 20 sessões')

    def test_finalizar_treino_e_depois_excluir(self):
        """Fluxo completo: finalizar treino registra progresso; ao excluir o treino, todo progresso é apagado."""
        self.client.login(username='aluno_teste', password='password123')

        treino = Treino.objects.create(
            nome='Treino Funcional',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),  # 10 dias
            usuario=self.user
        )
        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=10,
            concluidos=0
        )

        # Finaliza o treino 1 vez
        resp_finalizar = self.client.get(reverse('finalizar_treino', args=[treino.id]))
        self.assertRedirects(resp_finalizar, reverse('treinos'))

        progresso.refresh_from_db()
        self.assertEqual(progresso.concluidos, 1)
        self.assertEqual(len(progresso.dias_treinados), 1)
        self.assertEqual(progresso.dias_treinados[0]['treino_id'], treino.id)

        # Exclui o treino
        resp_excluir = self.client.post(reverse('excluir_treino', args=[treino.id]))
        self.assertRedirects(resp_excluir, reverse('treinos'))

        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 0)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])

        resp_treinos = self.client.get(reverse('treinos'))
        self.assertContains(resp_treinos, '0 / 0 sessões')

    def test_excluir_treino_direto_model_delete_dispara_signal(self):
        """Exclusão direta do Treino via model.delete() ativa o signal e ajusta o progresso do usuário."""
        treino = Treino.objects.create(
            nome='Treino Direto',
            data_inicio=datetime.date(2026, 10, 1),
            data_fim=datetime.date(2026, 10, 11),
            usuario=self.user
        )
        progresso = Progresso.objects.create(
            usuario=self.user,
            progresso_valor=10,
            concluidos=2,
            dias_treinados=[
                {'date': '2026-10-02', 'treino_id': treino.id, 'nome': treino.nome},
                {'date': '2026-10-03', 'treino_id': treino.id, 'nome': treino.nome},
            ]
        )

        treino.delete()

        progresso.refresh_from_db()
        self.assertEqual(progresso.progresso_valor, 0)
        self.assertEqual(progresso.concluidos, 0)
        self.assertEqual(progresso.dias_treinados, [])
