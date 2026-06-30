from django.shortcuts import render, redirect
from habitusapp.forms import AlunoForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User, Group
from django.conf import settings
import os
from django.contrib.auth.decorators import login_required
from habitusapp.forms import NoticiaForm, ProgressoForm
from habitusapp.models import Noticia, Aluno, Professor, Admin 
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Sum
from habitusapp.models import Treino, TreinoExercicio, Exercicio, Notificacao, Progresso
from django.utils import timezone
from datetime import datetime
from django.http import JsonResponse
from django.contrib import messages
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from habitusapp.forms import TreinoFormEdit, TreinoExercicioFormSet
from django.shortcuts import redirect, get_object_or_404
from habitusapp.models import TreinoExercicio
from habitusapp.models import Progresso
from django.views.decorators.http import require_POST

from django.views.decorators.csrf import csrf_protect
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta


@csrf_protect
@require_POST
def logout_view(request):
    """View customizada de logout com proteção CSRF"""
    auth_logout(request)
    messages.success(request, 'Você saiu com sucesso!')
    return redirect('login')


@csrf_protect
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        # Verifica se existe usuário com o e-mail informado
        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'Usuário com este e-mail não existe!')
            return render(request, 'PagsUsuario/login.html')

        # ➤ Se o usuário existe mas está inativo, avisar antes mesmo de autenticar
        if not user_obj.is_active:
            messages.error(request, 'Sua conta está inativa. Entre em contato com a administração.')
            return render(request, 'PagsUsuario/login.html')

        # Tentar autenticar
        user = authenticate(request, username=user_obj.username, password=senha)

        if user is not None:
            auth_login(request, user)
            messages.success(request, 'Login feito com sucesso!')
            return redirect('feed')

        else:
            messages.error(request, 'Senha incorreta! Tente novamente.')
            return render(request, 'PagsUsuario/login.html')

    return render(request, 'PagsUsuario/login.html')


@csrf_protect
def criar_conta(request):
    if request.method == 'POST':
        form = AlunoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('login')
    else:
        #messages.error(request, 'Dados incorretos ou erro no sistema. Tente mais tarde!')
        form = AlunoForm()
    
    return render(request, 'PagsUsuario/criar_conta.html', {'form': form})

#@csrf_exempt
#@csrf_protect
@login_required
def feed(request):
    tem_notificacao = False
    if request.user.is_authenticated:
        tem_notificacao = Notificacao.objects.filter(usuario=request.user, lida=False).exists()
    noticias = Noticia.objects.all().order_by('-data_publicacao')
    
    nome = None
    if hasattr(request.user, 'aluno'):
        nome = request.user.aluno.nome
    elif hasattr(request.user, 'professor'):
        nome = request.user.professor.nome
    elif hasattr(request.user, 'admin'):
        nome = request.user.admin.nome
    else:
        nome = request.user.username  # fallback

    # --- Treino do dia ---
    treino_do_dia = None
    treinos_usuario = Treino.objects.filter(usuario=request.user).order_by('id')
    if treinos_usuario.exists():
        # CORREÇÃO: Usar first() em vez de get_or_create()
        progresso_obj = Progresso.objects.filter(usuario=request.user).first()
        ultimo_id = getattr(progresso_obj, 'ultimo_treino_id', None) if progresso_obj else None

        if ultimo_id:
            # acha índice do último treino
            try:
                idx = list(treinos_usuario.values_list('id', flat=True)).index(ultimo_id)
                # próximo treino é o seguinte, ou volta para o primeiro
                proximo_idx = (idx + 1) % treinos_usuario.count()
                treino_do_dia = treinos_usuario[proximo_idx]
            except ValueError:
                treino_do_dia = treinos_usuario.first()
        else:
            treino_do_dia = treinos_usuario.first()

    return render(request, 'PagsUsuario/feed.html', {
        'noticias': noticias,
        'nome_usuario': nome,
        'tem_notificacao': tem_notificacao,
        'treino_do_dia': treino_do_dia,
    })


##@csrf_exempt
#@csrf_protect
@login_required
def treinos(request):
    # Recalcula o total
    progresso_total = calcular_progresso(request.user)

    # CORREÇÃO: Usar first() em vez de filter().first()
    progresso_obj = Progresso.objects.filter(usuario=request.user).first()
    concluidos = progresso_obj.concluidos if progresso_obj else 0
    faltando = progresso_total - concluidos if progresso_total > concluidos else 0

    tem_notificacao = False
    if request.user.is_authenticated:
        tem_notificacao = Notificacao.objects.filter(
            usuario=request.user, lida=False
        ).exists()

    treinos_usuario = Treino.objects.filter(usuario=request.user,arquivado=False).order_by('-id')
    

    return render(request, 'PagsUsuario/treinos.html', {
        'treinos_usuario': treinos_usuario,
        'tem_notificacao': tem_notificacao,
        'total': progresso_total,
        'concluidos': concluidos,
        'faltando': faltando,
    })



# views.py
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from habitusapp.models import Treino, TreinoExercicio

def detalhes_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id)

    # nome de quem montou (usuário criador)
    montador = treino.usuario.get_full_name() or treino.usuario.username  

    # professor pode não existir
    professor = treino.professor.nome if treino.professor else None  

    # pega todos os exercícios vinculados ao treino
    exercicios = []
    for te in TreinoExercicio.objects.filter(treino=treino).select_related("exercicio"):
        exercicios.append({
            "nome": te.exercicio.nome,
            "imagem": te.exercicio.imagem.url if getattr(te.exercicio, "imagem", None) else None,
            "series": te.series,
            "repeticoes": te.repeticoes,
            "carga": te.carga if te.carga else "-",
            "observacao": te.observacao if te.observacao else "",
        })

    data = {
        "montador": montador,  # agora vai o usuário criador
        "professor": professor,  # se quiser exibir em outro campo no futuro
        "data_inicio": treino.data_inicio.strftime("%d/%m/%Y"),
        "data_fim": treino.data_fim.strftime("%d/%m/%Y"),
        "objetivo": getattr(treino, "objetivo", "Não informado"),  
        "nivel": treino.get_nivel_display(),
        "exercicios": exercicios,
    }
    return JsonResponse(data)




##@csrf_exempt
#@csrf_protect
@login_required
def meus_dados(request):
    perfil = None

    if hasattr(request.user, 'aluno'):
        perfil = request.user.aluno
    elif hasattr(request.user, 'professor'):
        perfil = request.user.professor
    elif hasattr(request.user, 'admin'):
        perfil = request.user.admin

    return render(request, 'PagsUsuario/meus_dados.html', {'perfil': perfil})

##@csrf_exempt
#@csrf_protect
@login_required
def perfil(request):
    tem_notificacao = False
    if request.user.is_authenticated:
        tem_notificacao = Notificacao.objects.filter(usuario=request.user, lida=False).exists()
    perfil = None

    if hasattr(request.user, 'aluno'):
        perfil = request.user.aluno
    elif hasattr(request.user, 'professor'):
        perfil = request.user.professor
    elif hasattr(request.user, 'admin'):
        perfil = request.user.admin

    return render(request, 'PagsUsuario/perfil.html', {
        'perfil': perfil,
        'tem_notificacao': tem_notificacao
        })


from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from habitusapp.models import Aluno, Professor, Admin, ConfirmacaoSenha


@login_required
def editar_perfil(request):
    user = request.user

    # Verifica QUAL modelo pertence ao usuário
    if hasattr(user, "aluno"):
        perfil = user.aluno
    elif hasattr(user, "professor"):
        perfil = user.professor
    elif hasattr(user, "admin"):
        perfil = user.admin
    else:
        messages.error(request, "Perfil não encontrado")
        return redirect("meus_dados")

    if request.method == "POST":
        nome = request.POST.get("nome")
        username = request.POST.get("username")
        email = request.POST.get("email")
        data_nasc = request.POST.get("data_nasc")
        telefone = request.POST.get("telefone")
        nova_senha = request.POST.get("new_password")

        # Atualiza User
        user.username = username
        user.email = email
        user.save()

        # Atualiza perfil
        perfil.nome = nome
        perfil.data_nasc = data_nasc
        perfil.telefone = telefone
        perfil.save()

        messages.success(request, "Dados atualizados com sucesso!")

        # Se há nova senha, gera token de confirmação e envia email
        if nova_senha and len(nova_senha) >= 8:
            try:
                # Remove confirmação anterior se existir
                ConfirmacaoSenha.objects.filter(user=user).delete()
                
                # Cria nova confirmação com a senha em texto plano
                confirmacao = ConfirmacaoSenha.objects.create(
                    user=user,
                    nova_senha=nova_senha  # Armazena a senha em texto plano temporariamente
                )
                
                # Gera link de confirmação
                token = confirmacao.token
                confirmation_url = request.build_absolute_uri(
                    reverse('confirmar_senha', args=[token])
                )
                
                # Envia email
                assunto = "Confirme a alteração de sua senha - Habitus"
                mensagem = f"""
                Olá {user.first_name or user.username},

                Você solicitou a alteração de sua senha no Habitus.

                Para confirmar a alteração, clique no link abaixo:
                {confirmation_url}

                Este link expira em 24 horas.

                Se você não solicitou essa alteração, ignore este email.

                Atenciosamente,
                Equipe Habitus
                """
                
                send_mail(
                    assunto,
                    mensagem,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                messages.info(request, "Um email de confirmação foi enviado para sua caixa de entrada. Verifique para confirmar a alteração de senha.")
            except Exception as e:
                messages.error(request, f"Erro ao enviar email de confirmação: {str(e)}")
                # Remove a confirmação em caso de erro
                ConfirmacaoSenha.objects.filter(user=user).delete()
        
        return redirect("meus_dados")

    return render(request, "PagsUsuario/editar_perfil.html", {"perfil": perfil})


@login_required
def confirmar_senha(request, token):
    """
    View para confirmar a alteração de senha via email
    """
    try:
        confirmacao = ConfirmacaoSenha.objects.get(token=token, user=request.user)
        
        # Verifica se o token expirou
        if confirmacao.expirado:
            messages.error(request, "Link de confirmação expirado. Solicite uma nova alteração de senha.")
            confirmacao.delete()
            return redirect("editar_perfil")
        
        # Atualiza a senha
        user = request.user
        user.set_password(confirmacao.nova_senha)
        user.save()
        
        # Marca como confirmado e deleta
        confirmacao.delete()
        
        messages.success(request, "Senha alterada com sucesso!")
        return redirect("meus_dados")
    
    except ConfirmacaoSenha.DoesNotExist:
        messages.error(request, "Link de confirmação inválido.")
        return redirect("editar_perfil")



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
import os
from habitusapp.models import Notificacao

@login_required
def editar_foto(request):
    perfil = None

    # Verifica qual tipo de perfil possui o usuário logado
    if hasattr(request.user, 'aluno'):
        perfil = request.user.aluno
    elif hasattr(request.user, 'professor'):
        perfil = request.user.professor
    elif hasattr(request.user, 'admin'):
        perfil = request.user.admin

    if request.method == 'POST':
        # Caso o usuário tenha escolhido usar a foto padrão
        if 'usar_foto_padrao' in request.POST:
            if perfil.foto_perfil and os.path.isfile(perfil.foto_perfil.path):
                os.remove(perfil.foto_perfil.path)  # Apaga foto antiga
            perfil.foto_perfil = None  # Seta como NULL no banco
            perfil.save()
            Notificacao.objects.create(usuario=request.user, conteudo="Você alterou sua foto de perfil para a padrão")
            return redirect('perfil')

        # Upload de nova foto
        elif 'nova_foto' in request.FILES:
            # 1. Se existir uma foto antiga, tenta apagá-la fisicamente do disco
            if perfil.foto_perfil:
                try:
                    if os.path.isfile(perfil.foto_perfil.path):
                        os.remove(perfil.foto_perfil.path)
                except (ValueError, FileNotFoundError):
                    pass # Ignora o erro se o arquivo já tiver sumido da pasta media
            
            # 2. CORREÇÃO AQUI: Estas linhas ficam FORA do "if perfil.foto_perfil:"
            # Desta forma, são executadas para QUALQUER upload.
            perfil.foto_perfil = request.FILES['nova_foto']
            perfil.save()
            
            Notificacao.objects.create(usuario=request.user, conteudo="Você alterou sua foto de perfil")
            return redirect('perfil')

    return render(request, 'PagsUsuario/perfil.html', {'perfil': perfil})



from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from habitusapp.models import Treino, Exercicio, TreinoExercicio, Notificacao


@csrf_protect
@login_required
def novo_treino(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        nivel = request.POST.get('nivel')

        exercicios_ids = request.POST.getlist('exercicios')
        series = request.POST.getlist('series')
        repeticoes = request.POST.getlist('repeticoes')
        carga = request.POST.getlist('carga')
        observacoes = request.POST.getlist('observacoes')

        # valida se tem ao menos 1 exercício
        if not exercicios_ids:
            messages.error(request, "Você precisa adicionar pelo menos um exercício ao treino.")
            return redirect('novo_treino')

        # valida se todos os exercícios têm séries, repetições e carga
        for i in range(len(exercicios_ids)):
            if not series[i] or int(series[i]) <= 0:
                messages.error(request, f"O(s) exercício(s) precisa ter número de séries maior que 0.")
                return redirect('novo_treino')

            if not repeticoes[i] or int(repeticoes[i]) <= 0:
                messages.error(request, f"O(s) exercício(s) precisa ter número de repetições maior que 0.")
                return redirect('novo_treino')

            if not carga[i] or carga[i].strip() == "":
                messages.error(request, f"O(s) exercício(s) precisa ter carga definida.")
                return redirect('novo_treino')

        # Conversão das datas
        data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()


        # cria treino
        treino = Treino.objects.create(
            nome=nome,
            data_inicio=data_inicio,
            data_fim=data_fim,
            nivel=nivel,
            usuario=request.user
        )

        # cria notificação
        Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você criou um novo treino."
        )

        # salva exercícios
        for i in range(len(exercicios_ids)):
            TreinoExercicio.objects.create(
                treino=treino,
                exercicio_id=exercicios_ids[i],
                series=int(series[i]),
                repeticoes=int(repeticoes[i]),
                carga=carga[i],
                observacao=observacoes[i] if observacoes else None
            )

        messages.success(request, 'Novo treino adicionado com sucesso!')
        return redirect('treinos')

    exercicios = Exercicio.objects.all()
    return render(request, 'PagsUsuario/novo_treino.html', {'exercicios': exercicios})


##@csrf_exempt
#@csrf_protect
def buscar_exercicios(request):
    termo = request.GET.get("q", "").strip().lower()
    grupo = request.GET.get("grupo", "").strip()
    excluidos = request.GET.get("excluidos", "")
    excluidos_ids = [int(x) for x in excluidos.split(",") if x.isdigit()]

    exercicios = Exercicio.objects.all()

    if termo:
        exercicios = exercicios.filter(nome__icontains=termo)

    if grupo:
        exercicios = exercicios.filter(grupo_muscular__iexact=grupo)

    if excluidos_ids:
        exercicios = exercicios.exclude(id__in=excluidos_ids)

    exercicios = exercicios.distinct()[:10]  # evita duplicações

    data = []
    for e in exercicios:
        data.append({
            "id": e.id,
            "nome": e.nome,
            "grupo_muscular": e.grupo_muscular,
            "video_url": e.video.url if e.video else None
        })
    return JsonResponse(data, safe=False)

from datetime import timedelta
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils.dateparse import parse_date
from datetime import date

@login_required
def notificacoes(request):
    hoje = date.today()

    data_inicio = request.GET.get('data_inicio', hoje.strftime("%Y-%m-%d"))
    data_fim = request.GET.get('data_fim', hoje.strftime("%Y-%m-%d"))

    notificacoes = Notificacao.objects.filter(usuario=request.user)

    di = parse_date(data_inicio)
    df = parse_date(data_fim)
    if di and df:
        notificacoes = notificacoes.filter(data__date__range=[di, df])

    # ✅ REGRA 1 — MARCAR TODAS COMO LIDAS AO ABRIR A PÁGINA
    Notificacao.objects.filter(
        usuario=request.user,
        lida=False
    ).update(lida=True)

    # ✅ REGRA 2 — GARANTIA: +24H TAMBÉM FICA LIDA
    limite = now() - timedelta(hours=24)
    Notificacao.objects.filter(
        usuario=request.user,
        lida=False,
        data__lte=limite
    ).update(lida=True)

    notificacoes = notificacoes.order_by("-data")

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        html = render_to_string(
            "PagsUsuario/partials/notificacoes_lista.html",
            {"notificacoes": notificacoes},
            request=request
        )
        return JsonResponse({"html": html})

    return render(request, "PagsUsuario/notificacoes.html", {
        "notificacoes": notificacoes,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
    })


@csrf_protect
@login_required
def editar_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    if request.method == "POST":
        form = TreinoFormEdit(request.POST, instance=treino)
        formset = TreinoExercicioFormSet(request.POST, instance=treino)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Treino atualizado com sucesso!")
            Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você editou seu treino com sucesso"
            )
            return redirect("treinos")
    else:
        form = TreinoFormEdit(instance=treino)
        formset = TreinoExercicioFormSet(instance=treino)

    return render(request, "PagsUsuario/editar_treino.html", {
        "form": form,
        "formset": formset,
        "treino": treino
    })


@csrf_protect
@login_required
def excluir_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    if request.method == "POST":
        treino.delete()
        messages.success(request, "Treino excluído com sucesso!")
        Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você excluiu seu treino com sucesso"
            )
        return redirect("treinos")

    # Se não for POST, redireciona de volta sem apagar
    return redirect("treinos")

#@csrf_exempt
#@csrf_protect
def editar_detalhes(request):
    if request.method == "POST":
        exercicio_id = request.POST.get("id")
        exercicio = get_object_or_404(TreinoExercicio, id=exercicio_id)

        exercicio.series = request.POST.get("series")
        exercicio.repeticoes = request.POST.get("repeticoes")
        exercicio.carga = request.POST.get("carga")
        exercicio.observacao = request.POST.get("observacao")
        exercicio.save()

        messages.success(request, "Exercício atualizado com sucesso!")
        next_url = request.POST.get("next", "/")
        return redirect(next_url)



def desenvolvedores(request):
    return render(request, 'PagsUsuario/desenvolvedores.html')

def politica_de_privacidade(request):
    return render(request, 'PagsUsuario/politica_de_privacidade.html')
def termos_de_uso(request):
    return render(request, 'PagsUsuario/termos_de_uso.html')

def sobre_habitus(request):
    return render(request, 'PagsUsuario/sobre_habitus.html')

def configuracoes(request):
    progresso_total = calcular_progresso(request.user)

    # CORREÇÃO: Usar first()
    progresso_obj = Progresso.objects.filter(usuario=request.user).first()
    concluidos = progresso_obj.concluidos if progresso_obj else 0
    faltando = progresso_total - concluidos if progresso_total > concluidos else 0

    treinos_usuario = Treino.objects.filter(usuario=request.user).order_by('-id')
    total_treinos = treinos_usuario.count()

    return render(request, 'PagsUsuario/configuracoes.html', {
        'treinos_usuario': treinos_usuario,
        'total': progresso_total,
        'concluidos': concluidos,
        'faltando': faltando,
        'total_treinos':total_treinos,
    })


@csrf_protect
@login_required
def apagar_todos_treinos(request):
    if request.method == "POST":
        request.user.treino_set.all().delete() 
        messages.success(request, "Todos os seus treinos foram apagados com sucesso.")
        return redirect("configuracoes") 
    return redirect("configuracoes")



@csrf_protect
@login_required
def zerar_progresso(request):
    if request.method == "POST":
        progresso, _ = Progresso.objects.get_or_create(usuario=request.user)
        progresso.progresso_valor = 0
        progresso.concluidos = 0
        progresso.save()

        messages.success(request, "Seu progresso foi zerado com sucesso!")
        return redirect("configuracoes")  # ou onde quiser mandar o usuário
    return redirect("configuracoes")


@csrf_protect
@login_required
def comecar_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)
    exercicios = list(treino.exercicios_treino.all())
    
    index = int(request.GET.get('ex', 0))  # pega o index atual
    
    # se passou do último → redireciona de volta para a página do treino
    if index >= len(exercicios):
        return redirect(reverse('treino', args=[treino.id]))

    exercicio_atual = exercicios[index]

    # só define proximo_exercicio se não for o último
    proximo_exercicio = None
    if index + 1 < len(exercicios):
        proximo_exercicio = exercicios[index + 1]

    return render(request, 'PagsUsuario/treino.html', {
        'treino': treino,
        'exercicio_atual': exercicio_atual,
        'proximo_exercicio': proximo_exercicio, 
        'exercicio_index': index,
        'proximo_index': index + 1,
        'anterior_index': index - 1 if index > 0 else None,
        'total': len(exercicios)
    })


#@csrf_exempt
#@csrf_protect
@require_POST
@login_required
def marcar_concluido(request, exercicio_id):
    exercicio = get_object_or_404(TreinoExercicio, id=exercicio_id, treino__usuario=request.user)
    exercicio.concluido = True
    messages.success(request, "Exercício marcado como concluído!")
    exercicio.save()
    return redirect(request.META.get('HTTP_REFERER', 'treino'))

#@csrf_exempt
#@csrf_protect
@login_required
def finalizar_treino(request, treino_id):
    treino = get_object_or_404(Treino, id=treino_id, usuario=request.user)

    # Zera os concluídos desse treino (como você já fazia)
    treino.exercicios_treino.update(concluido=False)

    # CORREÇÃO: Usar first() e criar se não existir
    progresso_obj = Progresso.objects.filter(usuario=request.user).first()
    if not progresso_obj:
        progresso_obj = Progresso.objects.create(usuario=request.user)

    if progresso_obj.concluidos < (progresso_obj.progresso_valor or 0):
        progresso_obj.concluidos += 1
        progresso_obj.ultimo_treino_id = treino.id
        progresso_obj.save()
        messages.success(request, "Treino finalizado com sucesso!")
        Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você finalizou seu treino!"
            )

        # --- registra data + info do treino no JSONField ---
        hoje_str = timezone.now().date().isoformat()  # "YYYY-MM-DD"
        nome_treino = getattr(treino, 'nome', None) or getattr(treino, 'titulo', None) or f"Treino {treino.id}"

        # entrada a ser armazenada (serializável em JSON)
        entry = {"date": hoje_str, "treino_id": treino.id, "nome": nome_treino}

        raw = progresso_obj.dias_treinados or []

        # normaliza entradas antigas (strings) e mantém dicts como estão
        normalized = []
        for e in raw:
            if isinstance(e, str):
                normalized.append({"date": e, "treino_id": None, "nome": None})
            elif isinstance(e, dict):
                normalized.append(e)
            else:
                # ignora tipos estranhos
                continue

        # evita duplicata do mesmo treino no mesmo dia
        exists = any((d.get('date') == hoje_str and d.get('treino_id') == treino.id) for d in normalized)
        if not exists:
            normalized.append(entry)
            progresso_obj.dias_treinados = normalized
            progresso_obj.save()

    return HttpResponseRedirect(reverse('treinos'))



#@csrf_exempt
#@csrf_protect
def calcular_progresso(usuario):
    treinos = Treino.objects.filter(usuario=usuario)
    total_treinos = treinos.count()

    if total_treinos == 0:
        progresso_total = 0
    else:
        soma_dias = 0
        for treino in treinos:
            dias = (treino.data_fim - treino.data_inicio).days
            soma_dias += dias

        progresso_total = round(soma_dias / total_treinos)

    # CORREÇÃO: Usar first() em vez de get_or_create() para evitar MultipleObjectsReturned
    progresso_obj = Progresso.objects.filter(usuario=usuario).first()
    
    if progresso_obj:
        progresso_obj.progresso_valor = progresso_total
        progresso_obj.save()
    else:
        # Se não existir, cria um novo
        progresso_obj = Progresso.objects.create(
            usuario=usuario,
            progresso_valor=progresso_total
        )

    return progresso_total



from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from habitusapp.models import SolicitacaoDeTreino
from habitusapp.forms import SolicitacaoDeTreinoForm
from habitusapp.models import Professor  # professor já existe no seu app

from habitusapp.models import SolicitacaoDeTreino, Professor, Notificacao
from django.urls import reverse

from habitusapp.models import SolicitacaoDeTreino

from django.utils import timezone
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from habitusapp.models import SolicitacaoDeTreino
from habitusapp.forms import SolicitacaoDeTreinoForm
from habitusapp.models import Professor
from django.utils import timezone
from datetime import datetime

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from habitusapp.models import SolicitacaoDeTreino
from habitusapp.forms import SolicitacaoDeTreinoForm
from habitusapp.models import Professor
from django.utils import timezone
from datetime import datetime, date

def solicitar_novo_treino(request, professor_id=None):
    user = request.user
    
    # Determinar qual aba está ativa
    aba_ativa = request.GET.get('aba', 'professores')
    
    # Filtros para minhas solicitações (aluno)
    minhas_solicitacoes = SolicitacaoDeTreino.objects.filter(usuario=user)
    
    # Filtros para solicitações de alunos (professor)
    solicitacoes_alunos = None
    
    # Data atual para preenchimento padrão
    data_atual = date.today().isoformat()
    
    # Inicializar variáveis com valores padrão
    data_inicio = data_atual
    data_fim = data_atual
    situacao = 'A'
    data_inicio_alunos = data_atual
    data_fim_alunos = data_atual
    situacao_alunos = 'A'
    
    # Aplicar filtros baseado na aba ativa
    if aba_ativa == 'solicitacoes':
        # Filtros para "Minhas Solicitações"
        data_inicio = request.GET.get('data_inicio', data_atual)
        data_fim = request.GET.get('data_fim', data_atual)
        situacao = request.GET.get('situacao', 'A')
        
        # Aplicar filtros de data
        if data_inicio:
            try:
                data_inicio_obj = datetime.strptime(data_inicio, '%Y-%m-%d').date()
                minhas_solicitacoes = minhas_solicitacoes.filter(criado_em__date__gte=data_inicio_obj)
            except ValueError:
                pass
        
        if data_fim:
            try:
                data_fim_obj = datetime.strptime(data_fim, '%Y-%m-%d').date()
                minhas_solicitacoes = minhas_solicitacoes.filter(criado_em__date__lte=data_fim_obj)
            except ValueError:
                pass
        
        # Aplicar filtro de situação
        if situacao and situacao in ['A', 'C', 'R']:
            minhas_solicitacoes = minhas_solicitacoes.filter(status=situacao)
        
        minhas_solicitacoes = minhas_solicitacoes.order_by('-criado_em')
        
    elif aba_ativa == 'solicitacoes-alunos' and user.is_authenticated and user.groups.filter(name="Professor").exists():
        # Filtros para "Solicitações de Alunos"
        data_inicio_alunos = request.GET.get('data_inicio_alunos', data_atual)
        data_fim_alunos = request.GET.get('data_fim_alunos', data_atual)
        situacao_alunos = request.GET.get('situacao_alunos', 'A')
        
        try:
            professor_logado = Professor.objects.get(user=user)
            solicitacoes_alunos = SolicitacaoDeTreino.objects.filter(professor=professor_logado)
            
            # Aplicar filtros de data
            if data_inicio_alunos:
                try:
                    data_inicio_obj = datetime.strptime(data_inicio_alunos, '%Y-%m-%d').date()
                    solicitacoes_alunos = solicitacoes_alunos.filter(criado_em__date__gte=data_inicio_obj)
                except ValueError:
                    pass
            
            if data_fim_alunos:
                try:
                    data_fim_obj = datetime.strptime(data_fim_alunos, '%Y-%m-%d').date()
                    solicitacoes_alunos = solicitacoes_alunos.filter(criado_em__date__lte=data_fim_obj)
                except ValueError:
                    pass
            
            # Aplicar filtro de situação
            if situacao_alunos and situacao_alunos in ['A', 'C', 'R']:
                solicitacoes_alunos = solicitacoes_alunos.filter(status=situacao_alunos)
            
            solicitacoes_alunos = solicitacoes_alunos.order_by('-criado_em')
            
        except Professor.DoesNotExist:
            solicitacoes_alunos = None

    # Listagem de professores
    professores = Professor.objects.all().order_by('nome')
    
    context = {
        'professores': professores,
        'solicitacoes': minhas_solicitacoes,
        'solicitacoes_alunos': solicitacoes_alunos,
        'aba_ativa': aba_ativa,
        'data_inicio_selecionada': data_inicio,
        'data_fim_selecionada': data_fim,
        'situacao_selecionada': situacao,
        'data_inicio_selecionada_alunos': data_inicio_alunos,
        'data_fim_selecionada_alunos': data_fim_alunos,
        'situacao_selecionada_alunos': situacao_alunos,
        'data_atual': data_atual,
    }
    
    if professor_id is None:
        return render(request, 'PagsUsuario/solicitar_novo_treino.html', context)
    
    # Restante do código para quando há professor_id...
    professor = get_object_or_404(Professor, pk=professor_id)
    if request.method == 'POST':
        if not user.is_authenticated:
            messages.error(request, "Você precisa estar logado para enviar uma solicitação.")
            return redirect('login')
        form = SolicitacaoDeTreinoForm(request.POST)
        if form.is_valid():
            solicitacao = form.save(commit=False)
            solicitacao.usuario = user
            solicitacao.professor = professor
            solicitacao.save()
            messages.success(request, "Solicitação enviada com sucesso!")
            return redirect('solicitar_novo_treino')
    else:
        form = SolicitacaoDeTreinoForm()
    
    context['professor'] = professor
    context['form'] = form
    return render(request, 'PagsUsuario/professor_escolhido.html', context)


from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

@login_required
def aceitar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoDeTreino, id=solicitacao_id)

    if request.user != solicitacao.professor.user:
        messages.error(request, "Você não tem permissão para essa ação.")
        return redirect('solicitar_novo_treino')

    solicitacao.status = 'C'  # Concluída
    solicitacao.save()
    messages.success(request, "Solicitação marcada como concluída.")
    return redirect('solicitar_novo_treino')


@login_required
def recusar_solicitacao(request, solicitacao_id):
    solicitacao = get_object_or_404(SolicitacaoDeTreino, id=solicitacao_id)

    if request.user != solicitacao.professor.user:
        messages.error(request, "Você não tem permissão para essa ação.")
        return redirect('solicitar_novo_treino')

    solicitacao.status = 'R'  # Recusada
    solicitacao.save()
    messages.success(request, "Solicitação recusada.")
    return redirect('solicitar_novo_treino')

@login_required
def redirecionar_treinos_por_usuario(request, user_id):
    from habitusapp.models import Aluno, Professor  # importe conforme seu projeto

    # Tenta localizar como Aluno
    aluno = Aluno.objects.filter(user_id=user_id).first()
    if aluno:
        return redirect('gerenciar_treinos', aluno_id=aluno.id)

    # Tenta localizar como Professor
    professor = Professor.objects.filter(user_id=user_id).first()
    if professor:
        return redirect('gerenciar_treinos', professor_id=professor.id)

    # Caso seja admin ou outro tipo, redireciona para uma página padrão
    messages.error(request, "Não foi possível encontrar treinos associados a este usuário.")
    return redirect('feed')


from django.shortcuts import render
from habitusapp.models import Treino

def historico(request):
    if request.user.is_authenticated:
        treinos_arquivados = Treino.objects.filter(usuario=request.user, arquivado=True).order_by('-data_fim')
    else:
        treinos_arquivados = None

    return render(request, 'PagsUsuario/historico.html', {'treinos': treinos_arquivados})


#@csrf_exempt
#@csrf_protect
def reportar_erro(request):
    return render(request, 'PagsUsuario/reportar_erro.html')

#@csrf_exempt
#@csrf_protect
def recuperar_senha(request):
    return render(request, 'PagsUsuario/recuperar_senha.html')
#@csrf_exempt
#@csrf_protect
def entrar_pelo_suap(request):
    return render(request, 'PagsUsuario/entrar_pelo_suap.html')

#@csrf_exempt
#@csrf_protect
@login_required
def meu_progresso(request):
    progresso_total = calcular_progresso(request.user)
    hoje = timezone.now().date()

    # início e fim da semana
    inicio_semana = hoje - timedelta(days=hoje.weekday() + 1)
    fim_semana = inicio_semana + timedelta(days=6)

    progresso_obj = Progresso.objects.filter(usuario=request.user).first()
    raw = progresso_obj.dias_treinados if progresso_obj else []

    # normaliza todas as entradas para dicionários {date, treino_id, nome}
    normalized = []
    for e in raw:
        if isinstance(e, str):
            normalized.append({"date": e, "treino_id": None, "nome": None})
        elif isinstance(e, dict):
            normalized.append(e)
        else:
            continue

    # conjunto de datas que têm treino (strings "YYYY-MM-DD")
    dates_with_training = {d.get('date') for d in normalized if d.get('date')}

    nomes = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"]
    dias_semana = []
    for i in range(7):
        dia = inicio_semana + timedelta(days=i)
        dia_str = dia.isoformat()
        dias_semana.append({
            "nome": nomes[i],
            "data": dia.day,
            "treinou": dia_str in dates_with_training
        })

    # agrupa entradas por data (apenas da semana atual)
    map_date = {}
    for e in normalized:
        d = e.get('date')
        if not d:
            continue
        try:
            d_obj = datetime.fromisoformat(d).date()
        except Exception:
            continue
        if inicio_semana <= d_obj <= fim_semana:
            map_date.setdefault(d, []).append(e)

    # prepara lista para template: ordenada por data asc
    treinos_por_dia = []
    for date_str, entries in map_date.items():
        date_obj = datetime.fromisoformat(date_str).date()
        resolved = []
        for e in entries:
            nome = e.get('nome')
            if not nome and e.get('treino_id'):
                t = Treino.objects.filter(id=e.get('treino_id')).first()
                if t:
                    nome = getattr(t, 'nome', None) or getattr(t, 'titulo', None) or f"Treino {t.id}"
            if not nome:
                nome = "Treino finalizado"
            resolved.append({'nome': nome})
        treinos_por_dia.append({
            'date': date_obj,
            'entries': resolved,
            'count': len(resolved)
        })
    treinos_por_dia.sort(key=lambda x: x['date'])

    concluidos = progresso_obj.concluidos if progresso_obj else 0

    # Parte 2: progresso físico (peso, medidas etc)
    progressos = Progresso.objects.filter(usuario=request.user).order_by('-data_entrada')
    progresso_recente = progressos.first() if progressos else None

    data_selecionada = request.GET.get('data')
    progresso_filtrado = None
    if data_selecionada:
        try:
            progresso_filtrado = progressos.filter(data_entrada=data_selecionada).first()
        except:
            progresso_filtrado = None

    progresso_exibicao = progresso_filtrado if progresso_filtrado else progresso_recente
    datas_disponiveis = progressos.values_list('data_entrada', flat=True).distinct()

    return render(request, "PagsUsuario/meu_progresso.html", {
        "dias_semana": dias_semana,
        "total": progresso_total,
        "concluidos": concluidos,
        "treinos_por_dia": treinos_por_dia,
        "progresso": progresso_exibicao,
        "progressos": progressos,
        "datas_disponiveis": datas_disponiveis,
        "data_selecionada": data_selecionada,
    })


@login_required
def adicionar_meu_progresso(request):
    if request.method == 'POST':
        form = ProgressoForm(request.POST)
        if form.is_valid():
            novo_progresso = form.save(commit=False)
            novo_progresso.usuario = request.user
            novo_progresso.save()
            messages.success(request, 'Progresso adicionado com sucesso!')
            Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você adicionou um novo progresso!"
            )
            return redirect('meu_progresso')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ProgressoForm()
    
    context = {
        'form': form,
        'titulo': 'Adicionar Meu Progresso',
    }
    return render(request, 'PagsUsuario/adicionar_meu_progresso.html', context)

@login_required
def editar_meu_progresso(request, progresso_id):
    try:
        progresso = Progresso.objects.get(id=progresso_id, usuario=request.user)
    except Progresso.DoesNotExist:
        messages.error(request, 'Progresso não encontrado.')
        return redirect('meu_progresso')
    
    if request.method == 'POST':
        form = ProgressoForm(request.POST, instance=progresso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Progresso atualizado com sucesso!')
            Notificacao.objects.create(
            usuario=request.user,
            conteudo="Você editou seu progresso!"
            )
            return redirect('meu_progresso')
        else:
            messages.error(request, 'Por favor, corrija os erros no formulário.')
    else:
        form = ProgressoForm(instance=progresso)
    
    context = {
        'progresso': progresso,
        'form': form,
        'titulo': 'Editar Meu Progresso',
    }
    return render(request, 'PagsUsuario/editar_meu_progresso.html', context)

def get_or_create_progresso(usuario):
    """Função segura para obter ou criar Progresso, evitando MultipleObjectsReturned"""
    progresso = Progresso.objects.filter(usuario=usuario).first()
    if progresso:
        return progresso, False
    else:
        progresso = Progresso.objects.create(usuario=usuario)
        return progresso, True