from usuarios.models import Notificacao

def notificacoes_context(request):
    if request.user.is_authenticated:
        notificacoes_nao_lidas = request.user.notificacoes.filter(lida=False).order_by('-criada_em')[:5]
        total_nao_lidas = request.user.notificacoes.filter(lida=False).count()
        return {
            'notificacoes_dropdown': notificacoes_nao_lidas,
            'total_notificacoes': total_nao_lidas,
        }
    return {
        'notificacoes_dropdown': [],
        'total_notificacoes': 0,
    }