# ==============================================================================
# REABITECH — CONTEXT PROCESSOR DA MENSAGERIA
# Injeta contador global de mensagens não lidas em todos os templates
# ==============================================================================

def mensageria_context(request):
    """Adiciona 'total_mensagens_nao_lidas' ao contexto global."""
    if not request.user.is_authenticated:
        return {'total_mensagens_nao_lidas': 0}

    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return {'total_mensagens_nao_lidas': 0}

    try:
        from .models import ParticipanteConversa
        participacoes = ParticipanteConversa.objects.filter(
            usuario=request.user,
            conversa__projeto_id=projeto_id,
        ).select_related('conversa')

        total = 0
        for p in participacoes:
            total += p.conversa.total_nao_lidas_para(request.user)

        return {'total_mensagens_nao_lidas': total}
    except Exception:
        return {'total_mensagens_nao_lidas': 0}
