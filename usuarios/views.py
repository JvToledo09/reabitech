# ==============================================================================
# REABITECH — VIEWS DE AUDITORIA
# ==============================================================================

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from .models import Auditoria
from .decorators import perfil_required


@login_required
@perfil_required('coordenador')
def auditoria_lista(request):
    """Lista todas as ações registradas no sistema."""
    # Pega o projeto ativo
    from projetos.models import Projeto, MembroProjeto
    projeto_id = request.session.get('projeto_id')
    projeto = None
    if projeto_id:
        try:
            projeto = Projeto.objects.get(id=projeto_id, ativo=True)
        except Projeto.DoesNotExist:
            pass

    # Query base
    auditorias = Auditoria.objects.select_related('usuario', 'projeto')

    # Filtra por projeto (se houver)
    if projeto:
        auditorias = auditorias.filter(
            Q(projeto=projeto) | Q(projeto__isnull=True)
        )

    # Filtros da URL
    busca = request.GET.get('q', '')
    acao_filtro = request.GET.get('acao', '')
    usuario_filtro = request.GET.get('usuario', '')
    modelo_filtro = request.GET.get('modelo', '')
    periodo = request.GET.get('periodo', '')

    if busca:
        auditorias = auditorias.filter(
            Q(descricao__icontains=busca) |
            Q(objeto_repr__icontains=busca)
        )

    if acao_filtro:
        auditorias = auditorias.filter(acao=acao_filtro)

    if usuario_filtro:
        auditorias = auditorias.filter(usuario_id=usuario_filtro)

    if modelo_filtro:
        auditorias = auditorias.filter(modelo=modelo_filtro)

    # Filtro por período
    agora = datetime.now()
    if periodo == '1h':
        auditorias = auditorias.filter(criado_em__gte=agora - timedelta(hours=1))
    elif periodo == '24h':
        auditorias = auditorias.filter(criado_em__gte=agora - timedelta(days=1))
    elif periodo == '7d':
        auditorias = auditorias.filter(criado_em__gte=agora - timedelta(days=7))
    elif periodo == '30d':
        auditorias = auditorias.filter(criado_em__gte=agora - timedelta(days=30))

    auditorias = auditorias.order_by('-criado_em')

    # Paginação
    paginator = Paginator(auditorias, 50)
    page = request.GET.get('page', 1)
    auditorias_paginadas = paginator.get_page(page)

    # Lista de usuários que têm auditorias (para o filtro)
    usuarios_com_auditoria = User.objects.filter(
        auditorias__isnull=False
    ).distinct()

    # Lista de modelos únicos
    modelos_unicos = Auditoria.objects.values_list(
        'modelo', flat=True
    ).distinct().order_by('modelo')

    context = {
        'auditorias': auditorias_paginadas,
        'total': paginator.count,
        'busca': busca,
        'acao_filtro': acao_filtro,
        'usuario_filtro': usuario_filtro,
        'modelo_filtro': modelo_filtro,
        'periodo': periodo,
        'usuarios': usuarios_com_auditoria,
        'modelos': modelos_unicos,
        'acoes_choices': Auditoria.ACAO_CHOICES,
        'projeto': projeto,
    }
    return render(request, 'usuarios/auditoria/lista.html', context)


@login_required
@perfil_required('coordenador')
def auditoria_detalhes(request, auditoria_id):
    """Detalhes de uma ação específica."""
    auditoria = get_object_or_404(Auditoria, id=auditoria_id)
    return render(request, 'usuarios/auditoria/detalhes.html', {
        'auditoria': auditoria,
    })


@login_required
@perfil_required('coordenador')
def auditoria_usuario(request, usuario_id):
    """Histórico de ações de um usuário específico."""
    usuario = get_object_or_404(User, id=usuario_id)
    auditorias = Auditoria.objects.filter(
        usuario=usuario
    ).order_by('-criado_em')

    paginator = Paginator(auditorias, 50)
    page = request.GET.get('page', 1)
    auditorias_paginadas = paginator.get_page(page)

    context = {
        'usuario_alvo': usuario,
        'auditorias': auditorias_paginadas,
        'total': paginator.count,
    }
    return render(request, 'usuarios/auditoria/por_usuario.html', context)