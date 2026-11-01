from django.db.models.signals import post_delete
from django.dispatch import receiver


def ajustar_progresso_ao_excluir_treino(treino_id, usuario_id, treino_nome=None):
    """
    Quando um treino específico é excluído, ajusta o progresso do usuário:
    - Remove os registros em dias_treinados associados a esse treino.
    - Subtrai da contagem de concluídos o número de sessões finalizadas desse treino.
    - Recalcula a contagem total de sessões baseada nos treinos restantes.
    - Se não houver treinos restantes, zera tanto a contagem de sessões quanto os concluídos.
    """
    if not usuario_id:
        return

    from habitusapp.models import Treino, Progresso

    try:
        progresso_objs = list(Progresso.objects.filter(usuario_id=usuario_id))
    except Exception:
        return

    if not progresso_objs:
        return

    treinos_restantes = Treino.objects.filter(usuario_id=usuario_id, arquivado=False).exclude(id=treino_id)
    total_restantes = treinos_restantes.count()

    if total_restantes > 0:
        soma_dias = sum(max(0, (t.data_fim - t.data_inicio).days) for t in treinos_restantes)
        novo_progresso_total = round(soma_dias / total_restantes)
    else:
        novo_progresso_total = 0

    for progresso_obj in progresso_objs:
        raw = progresso_obj.dias_treinados or []
        novos_dias = []
        concluidos_deste_treino = 0

        for e in raw:
            is_match = False
            if isinstance(e, dict):
                entry_id = e.get('treino_id')
                if entry_id is not None and str(entry_id) == str(treino_id):
                    is_match = True
                elif entry_id is None and treino_nome and e.get('nome') == treino_nome:
                    is_match = True

            if is_match:
                concluidos_deste_treino += 1
            else:
                novos_dias.append(e)

        progresso_obj.dias_treinados = novos_dias

        if total_restantes == 0:
            progresso_obj.concluidos = 0
            progresso_obj.progresso_valor = 0
            progresso_obj.dias_treinados = []
        else:
            progresso_obj.progresso_valor = novo_progresso_total
            progresso_obj.concluidos = max(0, (progresso_obj.concluidos or 0) - concluidos_deste_treino)
            if len(novos_dias) == 0:
                progresso_obj.concluidos = 0
            elif novo_progresso_total > 0 and progresso_obj.concluidos > novo_progresso_total:
                progresso_obj.concluidos = novo_progresso_total

        if progresso_obj.ultimo_treino_id and str(progresso_obj.ultimo_treino_id) == str(treino_id):
            progresso_obj.ultimo_treino_id = None

        progresso_obj.save()


@receiver(post_delete, sender='habitusapp.Treino')
def treino_post_delete(sender, instance, **kwargs):
    if instance.usuario_id:
        ajustar_progresso_ao_excluir_treino(
            treino_id=instance.id,
            usuario_id=instance.usuario_id,
            treino_nome=instance.nome
        )
