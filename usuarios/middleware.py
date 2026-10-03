# ==============================================================================
# REABITECH — MIDDLEWARE
# Captura IP e User Agent para auditoria
# ==============================================================================

from .models import Auditoria


class AuditoriaMiddleware:
    """
    Middleware que captura IP e User Agent de cada requisição.
    Guarda na thread local para uso dos signals.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Captura IP do cliente (considerando proxy reverso)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')

        # Captura User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:300]

        # Guarda no request para uso nos signals
        request.auditoria_ip = ip
        request.auditoria_user_agent = user_agent

        response = self.get_response(request)
        return response


# ==============================================================================
# Função auxiliar para registrar auditoria
# ==============================================================================
def registrar_auditoria(request, acao, modelo='', objeto_id=None, objeto_repr='', descricao=''):
    """Registra uma ação no log de auditoria."""
    if not request or not hasattr(request, 'user'):
        return

    ip = getattr(request, 'auditoria_ip', None)
    user_agent = getattr(request, 'auditoria_user_agent', '')

    # Pega o projeto ativo se houver
    projeto = None
    if hasattr(request, 'session'):
        projeto_id = request.session.get('projeto_id')
        if projeto_id:
            from projetos.models import Projeto
            try:
                projeto = Projeto.objects.get(id=projeto_id)
            except Projeto.DoesNotExist:
                pass

    Auditoria.objects.create(
        usuario=request.user if request.user.is_authenticated else None,
        acao=acao,
        modelo=modelo,
        objeto_id=objeto_id,
        objeto_repr=str(objeto_repr)[:300],
        descricao=descricao,
        ip=ip,
        user_agent=user_agent,
        projeto=projeto,
    )
    