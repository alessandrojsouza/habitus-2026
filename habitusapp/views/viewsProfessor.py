from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.utils import timezone
from django.http import JsonResponse
from habitusapp.models import Professor, Admin, Noticia, Aluno, Treino, Progresso, TreinoExercicio
from habitusapp.signals import ajustar_progresso_ao_excluir_treino
from habitusapp.forms import AlunoForm, NoticiaForm, ProgressoForm, AlunoEditForm, TreinoFormEdit, TreinoExercicioFormSet
import datetime
import os

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt

@login_required
def gerenciar_noticias(request):
    categoria_filtro = request.GET.get('categoria', '')
    noticias = Noticia.objects.all().order_by('-data_publicacao')
    if categoria_filtro:
        noticias = noticias.filter(categoria=categoria_filtro)
    nome = None
    return render(request, 'PagsProfessor/gerenciar_noticias.html', {
        'noticias': noticias,
        'nome_usuario': nome,
        'categoria_selecionada': categoria_filtro
    })

@login_required
def publicar_noticia(request):
    nome_autor = ""
    tipo_autor = ""
    autor_user = request.user

    try:
        admin = Admin.objects.get(user=request.user)
        nome_autor = admin.nome
        tipo_autor = admin.tipo_trabalho
    except Admin.DoesNotExist:
        try:
            professor = Professor.objects.get(user=request.user)
            nome_autor = professor.nome
            tipo_autor = professor.tipo_trabalho
        except Professor.DoesNotExist:
            return redirect('erro_permissao')

    if request.method == 'POST':
        form = NoticiaForm(request.POST, request.FILES)
        if form.is_valid():
            noticia = form.save(commit=False)
            noticia.autor_user = autor_user
            noticia.autor_nome = nome_autor
            noticia.autor_tipo = tipo_autor
            noticia.save()
            return redirect('feed')
    else:
        form = NoticiaForm()

    return render(request, 'PagsProfessor/publicar_noticia.html', {'form': form})

@login_required
def editar_noticia(request, noticia_id):
    try:
        noticia = Noticia.objects.get(id=noticia_id)
    except Noticia.DoesNotExist:
        return redirect('gerenciar_noticias')
    
    if noticia.autor_user != request.user and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para editar esta notícia.')
        return redirect('gerenciar_noticias')
    
    if request.method == 'POST':
        
        form = NoticiaForm(request.POST, request.FILES, instance=noticia)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notícia atualizada com sucesso!')
            return redirect('gerenciar_noticias')
    else:
        form = NoticiaForm(instance=noticia)
    
    return render(request, 'PagsProfessor/editar_noticia.html', {
        'form': form,
        'noticia': noticia
    })

@login_required
def excluir_noticia(request, noticia_id):
    try:
        noticia = Noticia.objects.get(id=noticia_id)
    except Noticia.DoesNotExist:
        return redirect('gerenciar_noticias')
    
    if noticia.autor_user != request.user and not request.user.is_superuser:
        messages.error(request, 'Você não tem permissão para excluir esta notícia.')
        return redirect('gerenciar_noticias')
    
    if request.method == 'POST':
        if noticia.imagem and os.path.isfile(noticia.imagem.path):
                os.remove(noticia.imagem.path)
        noticia.delete()
        messages.success(request, 'Notícia excluída com sucesso!')
    
    return redirect('gerenciar_noticias')

from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from habitusapp.models import Aluno, Treino, Progresso

@login_required
def gerenciar_alunos(request):
    busca = request.GET.get('busca', '').strip()

    # Verifica se o usuário digitou algo
    has_search_criteria = bool(busca)  # True se houver texto

    if has_search_criteria:
        alunos = Aluno.objects.filter(
            Q(nome__icontains=busca) |
            Q(matricula__icontains=busca)
        ).order_by('nome')
    else:
        # Nenhum critério: retorna vazio até o usuário pesquisar
        alunos = Aluno.objects.none()

    # Adiciona informações extras somente se houver resultados
    for aluno in alunos:
        total_treinos = Treino.objects.filter(usuario=aluno.user).count()
        progresso_obj = Progresso.objects.filter(usuario=aluno.user).first()
        concluidos = progresso_obj.concluidos if progresso_obj else 0

        aluno.treinos = total_treinos
        aluno.concluidos = concluidos

    context = {
        'alunos': alunos,
        'busca': busca,
    }

    return render(request, 'PagsProfessor/gerenciar_alunos.html', context)



@login_required
def gerenciar_treinos(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    treinos_usuario = Treino.objects.filter(usuario=aluno.user, arquivado=False)

    # Progresso do aluno
    progresso_obj = Progresso.objects.filter(usuario=aluno.user).first()
    concluidos = progresso_obj.concluidos if progresso_obj else 0
    total_treinos = treinos_usuario.count()
    porcentagem = 0
    if total_treinos > 0:
        porcentagem = (concluidos / total_treinos) * 100

    context = {
        'aluno': aluno,
        'treinos_usuario': treinos_usuario,
        'concluidos': concluidos,
        'total_treinos': total_treinos,
        'porcentagem': porcentagem,
    }

    return render(request, 'PagsProfessor/gerenciar_treinos.html', context)

@login_required
def adicionar_aluno(request):
    aluno_form = AlunoForm(request.POST or None, request.FILES or None)
    progresso_form = ProgressoForm(request.POST or None)

    if request.method == 'POST':
        if aluno_form.is_valid() and progresso_form.is_valid():
            try:
                aluno = aluno_form.save()
                progresso = progresso_form.save(commit=False)
                progresso.usuario = aluno.user
                progresso.save()
                messages.success(request, 'Aluno cadastrado com sucesso!')
                return redirect('gerenciar_alunos')
            except Exception as e:
                messages.error(request, f'Ocorreu um erro inesperado: {str(e)}')
        else:
            messages.error(request, 'Erro ao cadastrar aluno. Verifique os dados e tente novamente.')

    context = {
        'aluno_form': aluno_form,
        'progresso_form': progresso_form
    }
    return render(request, 'PagsProfessor/adicionar_aluno.html', context)


@login_required
def ver_aluno(request, aluno_id):
    try:
        aluno = Aluno.objects.get(id=aluno_id)
    except Aluno.DoesNotExist:
        messages.error(request, 'Aluno não encontrado.')
        return redirect('gerenciar_alunos')
    
    # Obter o progresso MAIS RECENTE do aluno (usando first() em vez de get())
    progresso = Progresso.objects.filter(usuario=aluno.user).order_by('-data_entrada').first()
    
    # Obter treinos do aluno
    treinos = aluno.user.treino_set.all() if hasattr(aluno.user, 'treino_set') else []
    
    # Calcular IMC se tiver peso e altura no progresso
    imc = None
    if progresso and progresso.peso and progresso.altura:
        try:
            altura_metros = progresso.altura / 100
            imc = progresso.peso / (altura_metros * altura_metros)
            imc = round(imc, 1)
        except:
            imc = None
    
    context = {
        'aluno': aluno,
        'progresso': progresso,
        'treinos': treinos,
        'imc': imc,
    }
    
    return render(request, 'PagsProfessor/ver_aluno.html', context)


from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST

@csrf_protect
@login_required
@require_POST
def atualizar_foto_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)
    
    if 'foto' in request.FILES:
        # Remove a foto antiga se existir
        if aluno.foto_perfil:
            aluno.foto_perfil.delete(save=False)
        
        aluno.foto_perfil = request.FILES['foto']
        aluno.save()
        return JsonResponse({
            'success': True,
            'message': 'Foto atualizada com sucesso!',
            'foto_url': aluno.foto_perfil.url
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Nenhuma foto foi selecionada.'
    }, status=400)



@login_required
def editar_aluno(request, pk):
    aluno = get_object_or_404(Aluno, pk=pk)

    progresso = Progresso.objects.filter(usuario=aluno.user).order_by('-id').first()
    progresso_existe = progresso is not None


    if request.method == 'POST':
        aluno_form = AlunoEditForm(request.POST, request.FILES, instance=aluno)
        
        # Inicializa progresso_form apenas se progresso existe
        if progresso_existe:
            progresso_form = ProgressoForm(request.POST, instance=progresso)
        else:
            progresso_form = None

        if aluno_form.is_valid():
            # Salva o aluno
            aluno = aluno_form.save()
            
            # Salva o progresso se existir
            if progresso_existe and progresso_form:
                if progresso_form.is_valid():
                    progresso = progresso_form.save(commit=False)
                    progresso.usuario = aluno.user
                    progresso.save()
                    print("Progresso salvo com validação")
                else:
                    # Se não for válido, tenta salvar manualmente
                    print("Progresso form inválido, salvando manualmente")
                    try:
                        # Atualiza os campos manualmente
                        for field in progresso_form.fields:
                            if field in request.POST:
                                value = request.POST.get(field)
                                if value:  # Só atualiza se não estiver vazio
                                    setattr(progresso, field, value)
                        
                        progresso.usuario = aluno.user
                        progresso.save()
                        print("Progresso salvo manualmente")
                    except Exception as e:
                        print(f"Erro ao salvar progresso manualmente: {e}")

            messages.success(request, 'Aluno atualizado com sucesso!')
            return redirect('ver_aluno', aluno_id=aluno.pk)
        else:
            # Mostra erros do aluno_form
            for field, errors in aluno_form.errors.items():
                for error in errors:
                    messages.error(request, f"Erro no campo {field}: {error}")
    else:
        aluno_form = AlunoEditForm(instance=aluno)
        # Inicializa progresso_form apenas se progresso existe
        if progresso_existe:
            progresso_form = ProgressoForm(instance=progresso)
        else:
            progresso_form = None

    context = {
        'aluno': aluno,
        'aluno_form': aluno_form,
        'progresso_form': progresso_form,
        'progresso': progresso,
    }

    return render(request, 'PagsProfessor/editar_aluno.html', context)

@login_required
def adicionar_treino(request, aluno_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        nivel = request.POST.get('nivel')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        # Pega os dados dos exercícios
        exercicios_ids = request.POST.getlist('exercicios')
        series_list = request.POST.getlist('series')
        repeticoes_list = request.POST.getlist('repeticoes')
        cargas_list = request.POST.getlist('carga')
        observacoes_list = request.POST.getlist('observacoes')
        
        if not exercicios_ids:
            messages.error(request, 'Selecione pelo menos um exercício para o treino.')
            return render(request, 'PagsProfessor/adicionar_treino.html', {'aluno': aluno})
        
        try:
            # Cria o treino
            treino = Treino.objects.create(
                usuario=aluno.user,
                nome=nome,
                nivel=nivel,
                data_inicio=data_inicio,
                data_fim=data_fim
            )
            
            # Adiciona os exercícios ao treino
            from habitusapp.models import Exercicio, TreinoExercicio
            
            for i, exercicio_id in enumerate(exercicios_ids):
                exercicio = Exercicio.objects.get(id=exercicio_id)
                
                TreinoExercicio.objects.create(
                    treino=treino,
                    exercicio=exercicio,
                    series=series_list[i] if i < len(series_list) else 0,
                    repeticoes=repeticoes_list[i] if i < len(repeticoes_list) else 0,
                    carga=cargas_list[i] if i < len(cargas_list) else "0",
                    observacao=observacoes_list[i] if i < len(observacoes_list) else ""
                )
            
            # Cria notificação para o aluno
            from habitusapp.models import Notificacao
            Notificacao.objects.create(
                usuario=aluno.user,
                conteudo=f'Novo treino "{nome}" foi adicionado ao seu plano.',
                data=timezone.now(),
                lida=False
            )
            
            messages.success(request, f'Treino "{nome}" criado com sucesso para {aluno.nome}!')
            return redirect('gerenciar_treinos', aluno_id=aluno.id)
            
        except Exception as e:
            messages.error(request, f'Erro ao criar treino: {str(e)}')
    
    return render(request, 'PagsProfessor/adicionar_treino.html', {'aluno': aluno})

@csrf_protect
@login_required
def excluir_treino_professor(request, treino_id, aluno_id):
    treino = get_object_or_404(Treino, id=treino_id)
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # Verifica se o treino pertence ao aluno especificado
    if treino.usuario != aluno.user:
        messages.error(request, 'Treino não encontrado para este aluno.')
        return redirect('gerenciar_treinos', aluno_id=aluno_id)

    if request.method == "POST":
        nome_treino = treino.nome
        ajustar_progresso_ao_excluir_treino(
            treino_id=treino.id,
            usuario_id=aluno.user.id,
            treino_nome=treino.nome
        )
        treino.delete()
        messages.success(request, f'Treino "{nome_treino}" excluído com sucesso!')
        return redirect('gerenciar_treinos', aluno_id=aluno_id)

    # Se não for POST, redireciona de volta sem apagar
    return redirect('gerenciar_treinos', aluno_id=aluno_id)

@csrf_protect
@login_required
def editar_treino_professor(request, aluno_id, treino_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)
    treino = get_object_or_404(Treino, id=treino_id, usuario=aluno.user)
    
    if request.method == 'POST':
        # Processa dados básicos do treino
        nome = request.POST.get('nome')
        nivel = request.POST.get('nivel')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        
        # Pega os dados dos exercícios novos
        exercicios_ids = request.POST.getlist('exercicios')
        series_list = request.POST.getlist('series')
        repeticoes_list = request.POST.getlist('repeticoes')
        cargas_list = request.POST.getlist('carga')
        observacoes_list = request.POST.getlist('observacoes')
        
        try:
            # Atualiza os dados básicos do treino
            treino.nome = nome
            treino.nivel = nivel
            treino.data_inicio = data_inicio
            treino.data_fim = data_fim
            treino.save()
            
            # Processa formset dos exercícios existentes
            formset = TreinoExercicioFormSet(request.POST, instance=treino)
            
            if formset.is_valid():
                formset.save()
            
            # Adiciona novos exercícios se houver
            if exercicios_ids:
                from habitusapp.models.Exercicio import Exercicio
                
                for i, exercicio_id in enumerate(exercicios_ids):
                    if i < len(series_list) and i < len(repeticoes_list) and i < len(cargas_list):
                        exercicio = get_object_or_404(Exercicio, id=exercicio_id)
                        
                        TreinoExercicio.objects.create(
                            treino=treino,
                            exercicio=exercicio,
                            series=int(series_list[i]) if series_list[i] and series_list[i].isdigit() else 0,
                            repeticoes=int(repeticoes_list[i]) if repeticoes_list[i] and repeticoes_list[i].isdigit() else 0,
                            carga=cargas_list[i] if i < len(cargas_list) else '',
                            observacao=observacoes_list[i] if i < len(observacoes_list) else ''
                        )
            
            messages.success(request, f'Treino "{treino.nome}" atualizado com sucesso!')
            return redirect('gerenciar_treinos', aluno_id=aluno_id)
            
        except Exception as e:
            messages.error(request, f'Erro ao atualizar treino: {str(e)}')
    
    # GET request - exibe formulário
    formset = TreinoExercicioFormSet(instance=treino)
    
    return render(request, 'PagsProfessor/editar_treino.html', {
        'aluno': aluno,
        'treino': treino,
        'formset': formset
    })


from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from habitusapp.models import Treino, Aluno
from django.contrib.auth.models import User

def arquivar_treino(request, aluno_id, treino_id):
    aluno = get_object_or_404(Aluno, id=aluno_id)  # Buscar o aluno certo
    treino = get_object_or_404(Treino, id=treino_id, usuario=aluno.user)  # Filtra corretamente pelo usuário do aluno

    if request.user.groups.first().name != "Professor":
        messages.error(request, "Você não tem permissão para arquivar treinos.")
        return redirect('gerenciar_treinos', aluno_id=aluno_id)

    treino.arquivado = True
    from habitusapp.models import Notificacao
    Notificacao.objects.create(
        usuario=aluno.user,
        conteudo=f'Seu treino "{treino.nome}" foi arquivado pelo professor {request.user.first_name or request.user.username}.',
        data=timezone.now(),
        lida=False
    )
    treino.save()
    messages.success(request, f"O treino '{treino.nome}' foi arquivado com sucesso!")
    return redirect('gerenciar_treinos', aluno_id=aluno_id)

    

@login_required
def progresso_aluno(request, aluno_id):
    try:
        aluno = Aluno.objects.get(id=aluno_id)
    except Aluno.DoesNotExist:
        messages.error(request, 'Aluno não encontrado.')
        return redirect('gerenciar_alunos')
    
    # Busca todos os progressos do aluno ordenados por data (mais recente primeiro)
    progressos = Progresso.objects.filter(usuario=aluno.user).order_by('-data_entrada')
    
    # Progresso mais recente (para mostrar por padrão)
    progresso_recente = progressos.first() if progressos else None
    
    # Filtro por data
    data_selecionada = request.GET.get('data')
    progresso_filtrado = None
    
    if data_selecionada:
        try:
            progresso_filtrado = progressos.filter(data_entrada=data_selecionada).first()
        except:
            progresso_filtrado = None
    
    # Progresso a ser exibido (filtrado ou mais recente)
    progresso_exibicao = progresso_filtrado if progresso_filtrado else progresso_recente
    
    # Lista de datas disponíveis para o filtro
    datas_disponiveis = progressos.values_list('data_entrada', flat=True).distinct()
    
    # Formulário para novo progresso
    if request.method == 'POST':
        form = ProgressoForm(request.POST)
        if form.is_valid():
            novo_progresso = form.save(commit=False)
            novo_progresso.usuario = aluno.user
            novo_progresso.save()
            messages.success(request, 'Progresso adicionado com sucesso!')
            return redirect('progresso_aluno', aluno_id=aluno_id)
    else:
        form = ProgressoForm()
    
    context = {
        'aluno': aluno,
        'progresso': progresso_exibicao,
        'progressos': progressos,
        'datas_disponiveis': datas_disponiveis,
        'data_selecionada': data_selecionada,
        'form': form,
    }
    return render(request, 'PagsProfessor/progresso_aluno.html', context)

@login_required
def adicionar_progresso(request, aluno_id):
    try:
        aluno = Aluno.objects.get(id=aluno_id)
    except Aluno.DoesNotExist:
        messages.error(request, 'Aluno não encontrado.')
        return redirect('gerenciar_alunos')
    
    if request.method == 'POST':
        form = ProgressoForm(request.POST)
        if form.is_valid():
            novo_progresso = form.save(commit=False)
            novo_progresso.usuario = aluno.user
            # A data será automaticamente definida pelo default=date.today() do modelo
            # Ou explicitamente: novo_progresso.data_entrada = date.today()
            novo_progresso.save()
            messages.success(request, 'Progresso adicionado com sucesso!')
            return redirect('progresso_aluno', aluno_id=aluno_id)
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ProgressoForm()
    
    context = {
        'aluno': aluno,
        'form': form,
    }
    return render(request, 'PagsProfessor/adicionar_progresso.html', context)


@login_required
def editar_progresso(request, aluno_id, progresso_id):
    try:
        aluno = Aluno.objects.get(id=aluno_id)
        progresso = Progresso.objects.get(id=progresso_id, usuario=aluno.user)
    except (Aluno.DoesNotExist, Progresso.DoesNotExist):
        messages.error(request, 'Progresso não encontrado.')
        return redirect('progresso_aluno', aluno_id=aluno_id)
    
    if request.method == 'POST':
        form = ProgressoForm(request.POST, instance=progresso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Progresso atualizado com sucesso!')
            return redirect('progresso_aluno', aluno_id=aluno_id)
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ProgressoForm(instance=progresso)
    
    context = {
        'aluno': aluno,
        'progresso': progresso,
        'form': form,
        'titulo': 'Editar Progresso',
    }
    return render(request, 'PagsProfessor/editar_progresso.html', context)