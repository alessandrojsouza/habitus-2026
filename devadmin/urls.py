"""
URL configuration for devadmin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.contrib.auth.views import LogoutView
from habitusapp.views.viewsUsuario import *
from habitusapp.views.viewsAdmin import *
from habitusapp.views.viewsProfessor import *
from habitusapp.views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logout/', viewsUsuario.logout_view, name='logout'),

    # Páginas Usuário
    path('', login, name='login'),
    path('criar_conta/', criar_conta, name='criar_conta'),
    path('feed/', viewsUsuario.feed, name='feed'),
    path('treinos/', viewsUsuario.treinos, name='treinos'),
    path('treinos/<int:treino_id>/', viewsUsuario.detalhes_treino, name='detalhes_treino'),
    path('perfil/', viewsUsuario.perfil, name='perfil'),
    path("editar-perfil/", viewsUsuario.editar_perfil, name="editar_perfil"),
    path('confirmar-senha/<str:token>/', viewsUsuario.confirmar_senha, name='confirmar_senha'),
    path('perfil/editar-foto', viewsUsuario.editar_foto, name='editar_foto'),
    path('meus_dados/', viewsUsuario.meus_dados, name='meus_dados'),
    path('novo_treino/', viewsUsuario.novo_treino, name='novo_treino'),
    path('buscar-exercicios/', viewsUsuario.buscar_exercicios, name='buscar_exercicios'),
    path('notificacoes/', viewsUsuario.notificacoes, name='notificacoes'),
    path('treinos/treino/<int:treino_id>/', viewsUsuario.comecar_treino, name='treino'),
    path('treino/<int:treino_id>/finalizar/', viewsUsuario.finalizar_treino, name='finalizar_treino'),
    path('desenvolvedores/', viewsUsuario.desenvolvedores, name='desenvolvedores'),
    path('sobre_habitus/', viewsUsuario.sobre_habitus, name='sobre_habitus'),
    path('configuracoes/', viewsUsuario.configuracoes, name='configuracoes'),
    path("configuracoes/apagar_todos/", viewsUsuario.apagar_todos_treinos, name="apagar_todos_treinos"),
    path("configuracoes/zerar_progresso/", viewsUsuario.zerar_progresso, name="zerar_progresso"),
    path("treinos/<int:treino_id>/editar/", viewsUsuario.editar_treino, name="editar_treino"),
    path("treinos/<int:treino_id>/excluir/", viewsUsuario.excluir_treino, name="excluir_treino"),
    path("editar-detalhes/", viewsUsuario.editar_detalhes, name="editar_detalhes"),
    path('treino/exercicio/<int:exercicio_id>/concluir/', viewsUsuario.marcar_concluido, name='marcar_concluido'),
    path('solicitar_novo_treino/', viewsUsuario.solicitar_novo_treino, name='solicitar_novo_treino'),
    path('solicitar_novo_treino/<int:professor_id>/', viewsUsuario.solicitar_novo_treino, name='solicitar_treino_professor'),
    path('historico/', viewsUsuario.historico, name='historico'),
    path('reportar_erro/', viewsUsuario.reportar_erro, name='reportar_erro'),
    path('recuperar_senha/', viewsUsuario.recuperar_senha, name='recuperar_senha'),
    path('entrar_pelo_suap/', viewsUsuario.entrar_pelo_suap, name='entrar_pelo_suap'),
    path('meu_progresso/', viewsUsuario.meu_progresso, name='meu_progresso'),
    path('politica_de_privacidade/', viewsUsuario.politica_de_privacidade, name='politica_de_privacidade'),
    path('termos_de_uso/', viewsUsuario.termos_de_uso, name='termos_de_uso'),
    path('solicitacao/<int:solicitacao_id>/confirmar/', viewsUsuario.aceitar_solicitacao, name='aceitar_solicitacao'),
    path('solicitacao/<int:solicitacao_id>/recusar/', viewsUsuario.recusar_solicitacao, name='recusar_solicitacao'),
    path('ver_treinos_usuario/<int:user_id>/', viewsUsuario.redirecionar_treinos_por_usuario, name='ver_treinos_usuario'),
    path('adicionar_meu_progresso/', viewsUsuario.adicionar_meu_progresso, name='adicionar_meu_progresso'),
    path('editar_meu_progresso/<int:progresso_id>/', viewsUsuario.editar_meu_progresso, name='editar_meu_progresso'),

    # Páginas Professor
    path('gerenciar_noticias/', viewsProfessor.gerenciar_noticias, name='gerenciar_noticias'),
    path('editar_noticia/<int:noticia_id>/', viewsProfessor.editar_noticia, name='editar_noticia'),
    path('excluir-noticia/<int:noticia_id>/', viewsProfessor.excluir_noticia, name='excluir_noticia'),
    path('publicar_noticia/', viewsProfessor.publicar_noticia, name='publicar_noticia'),
    path('gerenciar_alunos/', viewsProfessor.gerenciar_alunos, name='gerenciar_alunos'),
    path('gerenciar_alunos/<int:aluno_id>/', viewsProfessor.gerenciar_treinos, name='gerenciar_treinos'),
    path('gerenciar_alunos/adicionar_aluno/', viewsProfessor.adicionar_aluno, name='adicionar_aluno'),
    path('ver_aluno/<int:aluno_id>/', viewsProfessor.ver_aluno, name='ver_aluno'),
    path('ver-aluno/<int:pk>/atualizar-foto', viewsProfessor.atualizar_foto_aluno, name='atualizar_foto_aluno'),
    path('aluno/<int:pk>/editar/', viewsProfessor.editar_aluno, name='editar_aluno'),
    path('gerenciar_alunos/<int:aluno_id>/adicionar_treino/', viewsProfessor.adicionar_treino, name='adicionar_treino'),
    path('gerenciar_alunos/<int:aluno_id>/treino/<int:treino_id>/editar/', viewsProfessor.editar_treino_professor, name='editar_treino_professor'),
    path('gerenciar_alunos/<int:aluno_id>/treino/<int:treino_id>/excluir/', viewsProfessor.excluir_treino_professor, name='excluir_treino_professor'),
    path('progresso_aluno/<int:aluno_id>/', viewsProfessor.progresso_aluno, name='progresso_aluno'),
    path('adicionar_progresso/<int:aluno_id>/', viewsProfessor.adicionar_progresso, name='adicionar_progresso'),
    path('editar_progresso/<int:aluno_id>/<int:progresso_id>/', viewsProfessor.editar_progresso, name='editar_progresso'),
    path('arquivar_treino/<int:aluno_id>/<int:treino_id>/', viewsProfessor.arquivar_treino, name='arquivar_treino'),

    # Páginas Admin
    path('professores/', viewsAdmin.professores, name='professores'),
    path('novo_professor/', viewsAdmin.novo_professor, name='novo_professor'),
    path('professor/<int:pk>/', viewsAdmin.professor, name='professor'),
    path('professor/<int:pk>/atualizar-foto/', viewsAdmin.atualizar_foto_professor, name='atualizar_foto_professor'),
    path('editar_professor/<int:pk>/editar/', viewsAdmin.editar_professor, name='editar_professor'),
    path('exercicios/', viewsAdmin.exercicios, name='exercicios'),
    path('novo_exercicio/', viewsAdmin.novo_exercicio, name='novo_exercicio'),
    path('editar_exercicio/<int:exercicio_id>/', viewsAdmin.editar_exercicio, name='editar_exercicio'),
    path('excluir_exercicio/<int:exercicio_id>/', viewsAdmin.excluir_exercicio, name='excluir_exercicio'),
    path('professor/<int:pk>/inativar-reativar/', viewsAdmin.inativar_reativar_professor, name='inativar_reativar_professor'),
    path('aluno/<int:pk>/inativar-reativar/', viewsAdmin.inativar_reativar_aluno, name='inativar_reativar_aluno'),
    path('cadastrar-professor/', viewsAdmin.cadastrar_professor, name='cadastrar_professor'),
]

# Configuração de arquivos de mídia (Apenas em DEBUG)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)