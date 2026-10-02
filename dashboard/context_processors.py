# ==============================================================================
# REABITECH — CONTEXT PROCESSORS
# Disponibiliza variáveis globais em todos os templates
# ==============================================================================

from usuarios.models import Notificacao


def notificacoes_context(request):
    """Fornece notificações não lidas para o dropdown."""
    if request.user.is_authenticated:
        notificacoes_nao_lidas = request.user.notificacoes.filter(
            lida=False
        ).order_by('-criada_em')[:5]
        total_nao_lidas = request.user.notificacoes.filter(lida=False).count()
        return {
            'notificacoes_dropdown': notificacoes_nao_lidas,
            'total_notificacoes': total_nao_lidas,
        }
    return {
        'notificacoes_dropdown': [],
        'total_notificacoes': 0,
    }


def projeto_ativo_context(request):
    """
    Fornece o projeto ativo em todos os templates.
    Assim qualquer template pode usar {{ projeto_ativo_global }}.
    """
    if not request.user.is_authenticated:
        return {'projeto_ativo_global': None}

    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return {'projeto_ativo_global': None}

    try:
        from projetos.models import Projeto, MembroProjeto
        projeto = Projeto.objects.get(id=projeto_id, ativo=True)

        # Confirma que o usuário é membro
        if MembroProjeto.objects.filter(
            projeto=projeto, usuario=request.user, ativo=True
        ).exists():
            return {'projeto_ativo_global': projeto}
    except Exception:
        pass

    return {'projeto_ativo_global': None}