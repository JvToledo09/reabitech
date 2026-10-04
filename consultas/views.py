# ==============================================================================
# REABITECH — VIEWS DO APP CONSULTAS
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import calendar as cal

from usuarios.decorators import perfil_required
from usuarios.models import Atleta
from projetos.models import Projeto
from .models import Consulta
from .forms import ConsultaForm, CancelamentoForm


# ==============================================================================
# HELPERS
# ==============================================================================

def _get_projeto_ativo(request):
    """Recupera o projeto ativo da sessão."""
    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return None
    try:
        return Projeto.objects.get(id=projeto_id, ativo=True)
    except Projeto.DoesNotExist:
        return None


def _pode_gerenciar(user):
    """Só coordenador, fisio e psicólogo podem criar/editar/cancelar."""
    if not hasattr(user, 'perfil'):
        return False
    return user.perfil.tipo in ('coordenador', 'fisioterapeuta', 'psicologo')


def _consultas_visiveis(user, projeto):
    """Retorna queryset base de consultas conforme o perfil do usuário."""
    qs = Consulta.objects.filter(projeto=projeto).select_related(
        'atleta__usuario', 'profissional', 'criado_por'
    )

    if not hasattr(user, 'perfil'):
        return qs.none()

    tipo = user.perfil.tipo

    # Atleta só vê as próprias
    if tipo == 'atleta':
        try:
            atleta = Atleta.objects.get(usuario=user)
            return qs.filter(atleta=atleta)
        except Atleta.DoesNotExist:
            return qs.none()

    # Coordenador, fisio, psicólogo, técnico veem todas do projeto
    return qs


# ==============================================================================
# DASHBOARD / LISTA
# ==============================================================================

@login_required
def dashboard_consultas(request):
    """Visão geral da agenda."""
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    qs = _consultas_visiveis(request.user, projeto)
    hoje = timezone.localdate()
    proxima_semana = hoje + timedelta(days=7)

    consultas_hoje = qs.filter(data=hoje).order_by('hora_inicio')
    consultas_semana = qs.filter(data__gt=hoje, data__lte=proxima_semana).order_by('data', 'hora_inicio')
    pendentes = qs.filter(status__in=['agendada', 'confirmada', 'remarcada'], data__gte=hoje)

    stats = {
        'hoje': consultas_hoje.count(),
        'semana': consultas_semana.count(),
        'pendentes': pendentes.count(),
        'realizadas_mes': qs.filter(
            status='realizada',
            data__year=hoje.year, data__month=hoje.month
        ).count(),
        'canceladas_mes': qs.filter(
            status__in=['cancelada', 'faltou'],
            data__year=hoje.year, data__month=hoje.month
        ).count(),
    }

    context = {
        'projeto': projeto,
        'consultas_hoje': consultas_hoje,
        'consultas_semana': consultas_semana[:10],
        'stats': stats,
        'hoje': hoje,
        'pode_gerenciar': _pode_gerenciar(request.user),
    }
    return render(request, 'consultas/dashboard.html', context)


@login_required
def lista_consultas(request):
    """Lista de consultas com filtros."""
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    qs = _consultas_visiveis(request.user, projeto)

    # Filtros (querystring)
    status_f = request.GET.get('status')
    tipo_f = request.GET.get('tipo')
    atleta_f = request.GET.get('atleta')
    profissional_f = request.GET.get('profissional')
    periodo = request.GET.get('periodo', 'todas')

    if status_f:
        qs = qs.filter(status=status_f)
    if tipo_f:
        qs = qs.filter(tipo=tipo_f)
    if atleta_f:
        qs = qs.filter(atleta_id=atleta_f)
    if profissional_f:
        qs = qs.filter(profissional_id=profissional_f)

    hoje = timezone.localdate()
    if periodo == 'hoje':
        qs = qs.filter(data=hoje)
    elif periodo == 'semana':
        qs = qs.filter(data__gte=hoje, data__lte=hoje + timedelta(days=7))
    elif periodo == 'mes':
        qs = qs.filter(data__year=hoje.year, data__month=hoje.month)
    elif periodo == 'passadas':
        qs = qs.filter(data__lt=hoje)
    elif periodo == 'futuras':
        qs = qs.filter(data__gte=hoje)

    qs = qs.order_by('-data', '-hora_inicio')

    context = {
        'projeto': projeto,
        'consultas': qs[:200],
        'total': qs.count(),
        'status_choices': Consulta.STATUS_CHOICES,
        'tipo_choices': Consulta.TIPO_CHOICES,
        'atletas': Atleta.objects.filter(
    usuario__membros_projeto__projeto=projeto,
    usuario__membros_projeto__ativo=True,
    usuario__membros_projeto__tipo='atleta',
).distinct(), 
        'profissionais': projeto.membros.filter(
            tipo__in=['fisioterapeuta', 'psicologo', 'coordenador'], ativo=True
        ).select_related('usuario'),
        'filtros': {
            'status': status_f or '',
            'tipo': tipo_f or '',
            'atleta': atleta_f or '',
            'profissional': profissional_f or '',
            'periodo': periodo,
        },
        'pode_gerenciar': _pode_gerenciar(request.user),
        'hoje': hoje,
    }
    return render(request, 'consultas/lista.html', context)


# ==============================================================================
# CRUD
# ==============================================================================

@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def criar_consulta(request):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = ConsultaForm(request.POST, projeto=projeto)
        if form.is_valid():
            consulta = form.save(commit=False)
            consulta.projeto = projeto
            consulta.criado_por = request.user
            consulta.save()
            messages.success(request, 'Consulta agendada com sucesso.')
            return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)
    else:
        form = ConsultaForm(projeto=projeto, initial={'data': timezone.localdate()})

    return render(request, 'consultas/form.html', {
        'form': form,
        'titulo': 'Nova Consulta',
        'projeto': projeto,
        'consulta': None,
    })


@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def editar_consulta(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        return redirect('dashboard:dashboard')

    consulta = get_object_or_404(Consulta, id=consulta_id, projeto=projeto)
    if not consulta.pode_editar:
        messages.error(request, 'Esta consulta não pode mais ser editada.')
        return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)

    if request.method == 'POST':
        form = ConsultaForm(request.POST, instance=consulta, projeto=projeto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Consulta atualizada.')
            return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)
    else:
        form = ConsultaForm(instance=consulta, projeto=projeto)

    return render(request, 'consultas/form.html', {
        'form': form,
        'titulo': 'Editar Consulta',
        'projeto': projeto,
        'consulta': consulta,
    })


@login_required
def detalhes_consulta(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        return redirect('dashboard:dashboard')

    consulta = get_object_or_404(
        Consulta.objects.select_related('atleta__usuario', 'profissional', 'criado_por'),
        id=consulta_id, projeto=projeto
    )

    # Verifica visibilidade
    if not _consultas_visiveis(request.user, projeto).filter(id=consulta.id).exists():
        messages.error(request, 'Você não tem acesso a esta consulta.')
        return redirect('consultas:lista_consultas')

    return render(request, 'consultas/detalhes.html', {
        'consulta': consulta,
        'projeto': projeto,
        'pode_gerenciar': _pode_gerenciar(request.user),
    })


# ==============================================================================
# AÇÕES DE STATUS
# ==============================================================================

@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def confirmar_consulta(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, projeto=projeto)
    if request.method == 'POST':
        consulta.confirmar(por_usuario=request.user)
        messages.success(request, 'Consulta confirmada.')
    return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)


@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def marcar_realizada(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, projeto=projeto)
    if request.method == 'POST':
        consulta.marcar_realizada(por_usuario=request.user)
        messages.success(request, 'Consulta marcada como realizada.')
    return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)


@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def marcar_falta(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, projeto=projeto)
    if request.method == 'POST':
        consulta.marcar_falta(por_usuario=request.user)
        messages.warning(request, 'Falta registrada.')
    return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)


@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo')
def cancelar_consulta(request, consulta_id):
    projeto = _get_projeto_ativo(request)
    consulta = get_object_or_404(Consulta, id=consulta_id, projeto=projeto)

    if request.method == 'POST':
        form = CancelamentoForm(request.POST)
        if form.is_valid():
            consulta.cancelar(motivo=form.cleaned_data.get('motivo', ''))
            messages.warning(request, 'Consulta cancelada.')
            return redirect('consultas:detalhes_consulta', consulta_id=consulta.id)
    else:
        form = CancelamentoForm()

    return render(request, 'consultas/cancelar.html', {
        'consulta': consulta,
        'form': form,
        'projeto': projeto,
    })


# ==============================================================================
# CALENDÁRIO
# ==============================================================================

@login_required
def calendario_consultas(request):
    """Visão mensal de calendário."""
    projeto = _get_projeto_ativo(request)
    if not projeto:
        return redirect('dashboard:dashboard')

    hoje = timezone.localdate()
    try:
        ano = int(request.GET.get('ano', hoje.year))
        mes = int(request.GET.get('mes', hoje.month))
    except (TypeError, ValueError):
        ano, mes = hoje.year, hoje.month

    if mes < 1:
        mes, ano = 12, ano - 1
    if mes > 12:
        mes, ano = 1, ano + 1

    qs = _consultas_visiveis(request.user, projeto).filter(
        data__year=ano, data__month=mes
    ).order_by('data', 'hora_inicio')

    # Agrupa por dia (chave = int do dia)
    por_dia = {}
    for c in qs:
        por_dia.setdefault(c.data.day, []).append(c)

    # Calendário
    cal_obj = cal.Calendar(firstweekday=6)  # 6 = domingo
    semanas = []
    for semana in cal_obj.monthdatescalendar(ano, mes):
        linha = []
        for dia in semana:
            lista = por_dia.get(dia.day, []) if dia.month == mes else []
            linha.append((dia, lista))
        semanas.append(linha)

    # Navegação
    mes_anterior = (mes - 1) if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = (mes + 1) if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1

    context = {
        'projeto': projeto,
        'semanas': semanas,
        'ano': ano,
        'mes': mes,
        'mes_nome': cal.month_name[mes],
        'hoje': hoje,
        'mes_anterior': mes_anterior,
        'ano_anterior': ano_anterior,
        'mes_proximo': mes_proximo,
        'ano_proximo': ano_proximo,
        'pode_gerenciar': _pode_gerenciar(request.user),
    }
    return render(request, 'consultas/calendario.html', context)