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
    # Disponibiliza o projeto ativo e os rótulos adequados ao segmento.
    contexto = {
        'projeto_ativo_global': None,
        'pessoa_label': 'pessoa atendida',
        'pessoas_label': 'Pessoas atendidas',
        'pessoa_label_capitalizada': 'Pessoa atendida',
    }
    if not request.user.is_authenticated:
        return contexto
    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return contexto
    try:
        from projetos.models import Projeto, MembroProjeto
        projeto = Projeto.objects.get(id=projeto_id, ativo=True)
        if not MembroProjeto.objects.filter(
            projeto=projeto, usuario=request.user, ativo=True
        ).exists():
            return contexto
        rotulos = {
            'clinica': ('paciente', 'Pacientes'),
            'consultorio': ('paciente', 'Pacientes'),
            'academia': ('aluno', 'Alunos'),
            'escola': ('aluno', 'Alunos'),
            'time': ('atleta', 'Atletas'),
            'projeto_social': ('participante', 'Participantes'),
            'outro': ('pessoa atendida', 'Pessoas atendidas'),
        }
        singular, plural = rotulos.get(
            projeto.tipo, ('pessoa atendida', 'Pessoas atendidas')
        )
        contexto.update({
            'projeto_ativo_global': projeto,
            'pessoa_label': singular,
            'pessoas_label': plural,
            'pessoa_label_capitalizada': singular[:1].upper() + singular[1:],
        })
    except Exception:
        pass
    return contexto


def analytics_context(request):
    from django.conf import settings
    return {
        'GA4_MEASUREMENT_ID': getattr(settings, 'GA4_MEASUREMENT_ID', ''),
        'MICROSOFT_CLARITY_ID': getattr(settings, 'MICROSOFT_CLARITY_ID', ''),
    }
