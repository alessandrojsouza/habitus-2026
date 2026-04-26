from django.shortcuts import render, redirect, get_object_or_404
from habitusapp.forms import AlunoForm, ProfessorForm, ProfessorEditForm
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from habitusapp.models import Admin
from django.contrib import messages
from django.conf import settings
import os
from habitusapp.models import Noticia, Admin, Professor, Exercicio, Aluno
from habitusapp.forms import NoticiaForm, ExercicioForm
from django.db.models import Q

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from habitusapp.forms import ProfessorCadastroForm


@login_required
def professores(request):
    busca = request.GET.get('busca', '')

    grupo_professor = Group.objects.get(name='Professor')
    
    # Inicialmente não mostra nenhum professor, só mostra quando há busca
    if busca:
        usuarios_professores = grupo_professor.user_set.filter(
            Q(professor__nome__icontains=busca) | Q(professor__matricula__icontains=busca)
        ).order_by('professor__nome')
    else:
        # Retorna queryset vazio quando não há busca
        usuarios_professores = grupo_professor.user_set.none()

    context = {
        'usuarios_professores': usuarios_professores,
        'busca': busca,
    }
    return render(request, 'PagsAdmin/professores.html', context)


@csrf_protect
@login_required
def novo_professor(request):
    if request.method == 'POST':
        form = ProfessorForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Professor cadastrado com sucesso!')
                return redirect('professores')
            except Exception as e:
                messages.error(request, f'Erro ao cadastrar professor: {e}')
    else:
        form = ProfessorForm()
    return render(request, 'PagsAdmin/novo_professor.html', {'form': form})


@login_required
def professor(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    return render(request, 'PagsAdmin/professor.html', {'professor': professor})

@csrf_protect
@login_required
@require_POST
def atualizar_foto_professor(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    
    if 'foto' in request.FILES:
        # Remove a foto antiga se existir
        if professor.foto_perfil:
            professor.foto_perfil.delete(save=False)
        
        professor.foto_perfil = request.FILES['foto']
        professor.save()
        return JsonResponse({
            'success': True,
            'message': 'Foto atualizada com sucesso!',
            'foto_url': professor.foto_perfil.url
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Nenhuma foto foi selecionada.'
    }, status=400)

@csrf_protect
@login_required
def editar_professor(request, pk):
    professor = get_object_or_404(Professor, pk=pk)
    
    if request.method == 'POST':
        form = ProfessorEditForm(request.POST, request.FILES, instance=professor)
        if form.is_valid():
            form.save()
            messages.success(request, 'Professor atualizado com sucesso!')
            return redirect('professor', pk=professor.pk)
    else:
        form = ProfessorEditForm(instance=professor)
    
    return render(request, 'PagsAdmin/editar_professor.html', {
        'professor': professor,
        'form': form
    })








@csrf_protect
@login_required
def exercicios(request):
    busca = request.GET.get('busca', '')
    grupo_muscular = request.GET.get('grupo_muscular', '')
    
    # Verifica se há algum critério de pesquisa
    has_search_criteria = bool(busca.strip() or grupo_muscular)
    
    if has_search_criteria:
        exercicios = Exercicio.objects.all().order_by('nome')
        
        if busca.strip():
            exercicios = exercicios.filter(
                Q(nome__icontains=busca.strip())
            )
        if grupo_muscular:
            exercicios = exercicios.filter(grupo_muscular=grupo_muscular)
    else:
        # Se não há critério de pesquisa, retorna queryset vazio
        exercicios = Exercicio.objects.none()

    context = {
        'exercicios': exercicios,
        'busca': busca,
        'grupo_muscular': grupo_muscular,
    }

    return render(request, 'PagsAdmin/exercicios.html', context)

@csrf_protect
@login_required
def novo_exercicio(request):
    if request.method == 'POST':
        form = ExercicioForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício cadastrado com sucesso!')
            return redirect('exercicios')
    else:
        form = ExercicioForm()
    return render(request, 'PagsAdmin/novo_exercicio.html', {'form': form})


@csrf_protect
@login_required
def excluir_exercicio(request, exercicio_id):
    if request.method == 'POST':
        exercicio = get_object_or_404(Exercicio, id=exercicio_id)
        exercicio.delete()
        messages.success(request, 'Exercício excluído com sucesso!')
    return redirect('exercicios')

@csrf_protect
@login_required
def editar_exercicio(request, exercicio_id):
    exercicio = get_object_or_404(Exercicio, id=exercicio_id)
    
    if request.method == 'POST':
        form = ExercicioForm(request.POST, request.FILES, instance=exercicio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exercício editado com sucesso!')
            return redirect('exercicios')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = ExercicioForm(instance=exercicio)
    
    return render(request, 'PagsAdmin/editar_exercicio.html', {
        'form': form, 
        'exercicio': exercicio
    })

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST

def is_admin(user):
    return user.groups.filter(name='Admin').exists()

@login_required
@require_POST
def inativar_reativar_professor(request, pk):
    # Verifica se o usuário é admin
    if not is_admin(request.user):
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('feed')
    
    professor = get_object_or_404(Professor, pk=pk)
    
    # Impede que um admin inative/reative a si mesmo
    if professor.user == request.user:
        messages.error(request, 'Você não pode modificar o status da sua própria conta.')
        return redirect('professores')
    
    # Alterna o status do usuário
    user = professor.user
    if user.is_active:
        # Se está ativo, inativa
        user.is_active = False
        user.save()
        messages.success(request, f'Conta do professor {professor.nome} inativada com sucesso!')
    else:
        # Se está inativo, reativa
        user.is_active = True
        user.save()
        messages.success(request, f'Conta do professor {professor.nome} reativada com sucesso!')
    
    return redirect('professores')

@login_required
@require_POST
def inativar_reativar_aluno(request, pk):
    # Verifica se o usuário é admin
    if not is_admin(request.user):
        messages.error(request, 'Você não tem permissão para realizar esta ação.')
        return redirect('gerenciar_alunos')
    
    aluno = get_object_or_404(Aluno, pk=pk)
    
    # Impede que um admin inative/reative a si mesmo (se for aluno também)
    if aluno.user == request.user:
        messages.error(request, 'Você não pode modificar o status da sua própria conta.')
        return redirect('ver_aluno', aluno_id=pk)
    
    # Alterna o status do usuário
    user = aluno.user
    if user.is_active:
        # Se está ativo, inativa
        user.is_active = False
        user.save()
        messages.success(request, f'Conta do aluno {aluno.nome} inativada com sucesso!')
    else:
        # Se está inativo, reativa
        user.is_active = True
        user.save()
        messages.success(request, f'Conta do aluno {aluno.nome} reativada com sucesso!')
    
    return redirect('ver_aluno', aluno_id=pk)



def eh_admin_gestor(user):
    return user.groups.filter(name='Admin_Gestor').exists()

@user_passes_test(eh_admin_gestor)
def cadastrar_professor(request):
    if request.method == 'POST':
        form = ProfessorCadastroForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('gerenciar_professores') # Redireciona para a lista
    else:
        form = ProfessorCadastroForm()
    return render(request, 'PagsAdminGestor/cadastrar_professor.html', {'form': form})