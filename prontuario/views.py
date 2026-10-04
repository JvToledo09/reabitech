# ==============================================================================
# REABITECH — APP PRONTUÁRIO
# Views (CRUD completo + geração de PDF + compartilhamento com técnico)
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import FileResponse, HttpResponseForbidden
from datetime import date
from functools import wraps

from usuarios.models import Atleta, Notificacao, Alerta
from usuarios.decorators import perfil_required
from projetos.models import Projeto, MembroProjeto

from .models import (
    Prontuario, Triagem, Objetivo, Medicamento,
    AvaliacaoCIF, AvaliacaoCardiorrespiratoria,
    EscalaRisco, RelatorioDiario, EncaminhamentoMedico,
    Exame, EvolucaoFisioterapeutica,
    CompartilhamentoProntuario, ObservacaoTecnico,
)
from .forms import (
    ProntuarioForm, TriagemForm, ObjetivoForm, MedicamentoForm,
    AvaliacaoCIFForm, AvaliacaoCardiorrespiratoriaForm,
    EscalaRiscoForm, RelatorioDiarioForm, EncaminhamentoMedicoForm,
    ExameForm, EvolucaoFisioterapeuticaForm
)
from .pdf_utils import gerar_pdf_prontuario, gerar_pdf_relatorio_consolidado
# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def get_projeto_ativo(request):
    """Retorna o projeto ativo da sessão."""
    projeto_id = request.session.get('projeto_id')
    if projeto_id:
        try:
            projeto = Projeto.objects.get(id=projeto_id, ativo=True)
            if MembroProjeto.objects.filter(
                projeto=projeto, usuario=request.user, ativo=True
            ).exists():
                return projeto
        except Projeto.DoesNotExist:
            pass
    return None


def get_prontuario_ativo(request, prontuario_id):
    """Retorna um prontuário específico do projeto ativo."""
    projeto = get_projeto_ativo(request)
    if not projeto:
        return None
    return get_object_or_404(
        Prontuario,
        id=prontuario_id,
        projeto=projeto
    )


# ==============================================================================
# DASHBOARD DO PRONTUÁRIO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def dashboard_prontuario(request, prontuario_id):
    """Dashboard geral do prontuário — visão consolidada do paciente."""
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        messages.error(request, 'Prontuário não encontrado.')
        return redirect('dashboard:dashboard')

    prontuario.registrar_movimentacao()

    # 🔥 Bloqueio: técnico só acessa se houver compartilhamento ativo
    if request.user.perfil.tipo == 'tecnico':
        tem_acesso = CompartilhamentoProntuario.objects.filter(
            prontuario=prontuario, tecnico=request.user, ativo=True
        ).exists()
        if not tem_acesso:
            return HttpResponseForbidden(
                '<div style="font-family: sans-serif; padding: 60px; text-align: center;">'
                '<h1>🔒 Acesso Restrito</h1>'
                '<p>Este prontuário não foi compartilhado com você.</p>'
                '<a href="/dashboard/tecnico/" style="color: #2BA181;">← Voltar</a></div>'
            )

    ultima_triagem = prontuario.triagens.first()
    ultima_cif = prontuario.avaliacoes_cif.first()
    ultima_cardio = prontuario.avaliacoes_cardiorrespiratorias.first()
    ultimo_relatorio = prontuario.relatorios_diarios.first()
    ultima_evolucao = prontuario.evolucoes_fisioterapeuticas.first()

    total_triagens = prontuario.triagens.count()
    total_objetivos = prontuario.objetivos.count()
    objetivos_alcancados = prontuario.objetivos.filter(status='alcancado').count()
    total_medicamentos = prontuario.medicamentos.filter(status='ativo').count()
    total_avaliacoes_cif = prontuario.avaliacoes_cif.count()
    total_cardio = prontuario.avaliacoes_cardiorrespiratorias.count()
    total_escalas = prontuario.escalas_risco.count()
    total_relatorios = prontuario.relatorios_diarios.count()
    total_encaminhamentos = prontuario.encaminhamentos.count()
    total_exames = prontuario.exames.count()
    total_evolucoes = prontuario.evolucoes_fisioterapeuticas.count()

    tem_alerta_risco_alto = prontuario.escalas_risco.filter(
        nivel_risco__in=['alto', 'critico']
    ).exists()

    tem_alerta_cardio = prontuario.avaliacoes_cardiorrespiratorias.filter(
        frequencia_dispneia__gte=3
    ).exists()

    context = {
        'prontuario': prontuario,
        'atleta': prontuario.atleta,
        'ultima_triagem': ultima_triagem,
        'ultima_cif': ultima_cif,
        'ultima_cardio': ultima_cardio,
        'ultimo_relatorio': ultimo_relatorio,
        'ultima_evolucao': ultima_evolucao,
        'total_triagens': total_triagens,
        'total_objetivos': total_objetivos,
        'objetivos_alcancados': objetivos_alcancados,
        'total_medicamentos': total_medicamentos,
        'total_avaliacoes_cif': total_avaliacoes_cif,
        'total_cardio': total_cardio,
        'total_escalas': total_escalas,
        'total_relatorios': total_relatorios,
        'total_encaminhamentos': total_encaminhamentos,
        'total_exames': total_exames,
        'total_evolucoes': total_evolucoes,
        'tem_alerta_risco_alto': tem_alerta_risco_alto,
        'tem_alerta_cardio': tem_alerta_cardio,
        'objetivos_recentes': prontuario.objetivos.all()[:5],
        'ultimos_relatorios': prontuario.relatorios_diarios.all()[:5],
    }
    return render(request, 'prontuario/dashboard.html', context)


# ==============================================================================
# LISTA DE PRONTUÁRIOS
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_prontuarios(request):
    """Lista todos os prontuários do projeto com filtros avançados."""
    from datetime import timedelta
    from django.utils import timezone

    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    prontuarios = Prontuario.objects.filter(
        projeto=projeto
    ).select_related('atleta', 'atleta__usuario', 'fisioterapeuta_responsavel')

        # 🔥 Técnico vê somente prontuários compartilhados com ele
    if request.user.perfil.tipo == 'tecnico':
        prontuarios_ids = CompartilhamentoProntuario.objects.filter(
            tecnico=request.user, ativo=True
        ).values_list('prontuario_id', flat=True)
        prontuarios = prontuarios.filter(id__in=prontuarios_ids)

    # Filtros
    status_filtro = request.GET.get('status', '')
    busca = request.GET.get('q', '')
    periodo = request.GET.get('periodo', '')
    data_ini = request.GET.get('data_ini', '')
    data_fim = request.GET.get('data_fim', '')

    if status_filtro:
        prontuarios = prontuarios.filter(status=status_filtro)

    if busca:
        prontuarios = prontuarios.filter(
            Q(numero_prontuario__icontains=busca) |
            Q(atleta__usuario__first_name__icontains=busca) |
            Q(atleta__usuario__last_name__icontains=busca) |
            Q(atleta__rm__icontains=busca)
        )

    # Filtro por período
    hoje = timezone.now()
    if periodo == '7d':
        prontuarios = prontuarios.filter(criado_em__gte=hoje - timedelta(days=7))
    elif periodo == '30d':
        prontuarios = prontuarios.filter(criado_em__gte=hoje - timedelta(days=30))
    elif periodo == '90d':
        prontuarios = prontuarios.filter(criado_em__gte=hoje - timedelta(days=90))
    elif periodo == 'ano':
        prontuarios = prontuarios.filter(criado_em__year=hoje.year)
    elif data_ini and data_fim:
        prontuarios = prontuarios.filter(criado_em__date__range=[data_ini, data_fim])

    prontuarios = prontuarios.order_by('-criado_em')

    paginator = Paginator(prontuarios, 20)
    page = request.GET.get('page', 1)
    prontuarios_paginados = paginator.get_page(page)

    context = {
        'projeto': projeto,
        'prontuarios': prontuarios_paginados,
        'status_filtro': status_filtro,
        'busca': busca,
        'periodo': periodo,
        'data_ini': data_ini,
        'data_fim': data_fim,
        'status_choices': Prontuario.STATUS_CHOICES,
        'total': paginator.count,
    }
    return render(request, 'prontuario/lista.html', context)


# ==============================================================================
# SELECIONAR ATLETA PARA PRONTUÁRIO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def selecionar_atleta_prontuario(request):
    """Lista atletas do projeto para selecionar qual abrir prontuário."""
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)

    atletas = Atleta.objects.filter(
        usuario__in=membros_usuario_ids
    ).select_related('usuario', 'modalidade').distinct()

    atletas_sem_prontuario = []
    atletas_com_prontuario = []

    for atleta in atletas:
        if hasattr(atleta, 'prontuario'):
            atletas_com_prontuario.append(atleta)
        else:
            atletas_sem_prontuario.append(atleta)

    context = {
        'projeto': projeto,
        'atletas_sem_prontuario': atletas_sem_prontuario,
        'atletas_com_prontuario': atletas_com_prontuario,
    }
    return render(request, 'prontuario/selecionar_atleta.html', context)


# ==============================================================================
# CRIAR PRONTUÁRIO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_prontuario(request, atleta_id):
    """Cria um novo prontuário para um atleta."""
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    atleta = get_object_or_404(Atleta, id=atleta_id)

    if hasattr(atleta, 'prontuario'):
        messages.info(request, 'Este atleta já possui prontuário. Redirecionando...')
        return redirect('prontuario:dashboard_prontuario', prontuario_id=atleta.prontuario.id)

    if request.method == 'POST':
        form = ProntuarioForm(request.POST)
        if form.is_valid():
            prontuario = form.save(commit=False)
            prontuario.atleta = atleta
            prontuario.projeto = projeto
            prontuario.save()
            form.save_m2m()

            messages.success(
                request,
                f'Prontuário {prontuario.numero_prontuario} criado com sucesso!'
            )
            return redirect('prontuario:dashboard_prontuario', prontuario_id=prontuario.id)
        else:
            messages.error(request, 'Erro ao criar prontuário. Verifique os campos.')
    else:
        form = ProntuarioForm(initial={
            'fisioterapeuta_responsavel': request.user,
        })

    context = {
        'form': form,
        'atleta': atleta,
        'projeto': projeto,
    }
    return render(request, 'prontuario/criar.html', context)


# ==============================================================================
# TRIAGEM
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_triagem(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        messages.error(request, 'Prontuário não encontrado.')
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = TriagemForm(request.POST)
        if form.is_valid():
            triagem = form.save(commit=False)
            triagem.prontuario = prontuario
            triagem.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Triagem registrada com sucesso!')
            return redirect('prontuario:dashboard_prontuario', prontuario_id=prontuario.id)
    else:
        form = TriagemForm()

    return render(request, 'prontuario/triagem/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Triagem',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_triagem(request, triagem_id):
    triagem = get_object_or_404(Triagem, id=triagem_id)
    prontuario = triagem.prontuario

    if request.method == 'POST':
        form = TriagemForm(request.POST, instance=triagem)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Triagem atualizada com sucesso!')
            return redirect('prontuario:dashboard_prontuario', prontuario_id=prontuario.id)
    else:
        form = TriagemForm(instance=triagem)

    return render(request, 'prontuario/triagem/form.html', {
        'form': form,
        'prontuario': prontuario,
        'triagem': triagem,
        'titulo': 'Editar Triagem',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def lista_triagens(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    triagens = prontuario.triagens.all().order_by('-data_triagem')

    return render(request, 'prontuario/triagem/lista.html', {
        'prontuario': prontuario,
        'triagens': triagens,
    })


# ==============================================================================
# OBJETIVOS
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def criar_objetivo(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = ObjetivoForm(request.POST)
        if form.is_valid():
            objetivo = form.save(commit=False)
            objetivo.prontuario = prontuario
            objetivo.criado_por = request.user
            objetivo.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Objetivo criado com sucesso!')
            return redirect('prontuario:lista_objetivos', prontuario_id=prontuario.id)
    else:
        form = ObjetivoForm()

    return render(request, 'prontuario/objetivo/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Objetivo',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def editar_objetivo(request, objetivo_id):
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    prontuario = objetivo.prontuario

    if request.method == 'POST':
        form = ObjetivoForm(request.POST, instance=objetivo)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Objetivo atualizado!')
            return redirect('prontuario:lista_objetivos', prontuario_id=prontuario.id)
    else:
        form = ObjetivoForm(instance=objetivo)

    return render(request, 'prontuario/objetivo/form.html', {
        'form': form,
        'prontuario': prontuario,
        'objetivo': objetivo,
        'titulo': 'Editar Objetivo',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_objetivos(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    objetivos_curto = prontuario.objetivos.filter(prazo='curto')
    objetivos_medio = prontuario.objetivos.filter(prazo='medio')
    objetivos_longo = prontuario.objetivos.filter(prazo='longo')

    return render(request, 'prontuario/objetivo/lista.html', {
        'prontuario': prontuario,
        'objetivos_curto': objetivos_curto,
        'objetivos_medio': objetivos_medio,
        'objetivos_longo': objetivos_longo,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def deletar_objetivo(request, objetivo_id):
    objetivo = get_object_or_404(Objetivo, id=objetivo_id)
    prontuario = objetivo.prontuario

    if request.method == 'POST':
        objetivo.delete()
        prontuario.registrar_movimentacao()
        messages.success(request, 'Objetivo removido.')
        return redirect('prontuario:lista_objetivos', prontuario_id=prontuario.id)

    return render(request, 'prontuario/confirmar_delete.html', {
        'objeto': objetivo,
        'prontuario': prontuario,
        'tipo': 'objetivo',
    })


# ==============================================================================
# MEDICAMENTOS
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_medicamento(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = MedicamentoForm(request.POST)
        if form.is_valid():
            med = form.save(commit=False)
            med.prontuario = prontuario
            med.registrado_por = request.user
            med.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Medicamento registrado!')
            return redirect('prontuario:lista_medicamentos', prontuario_id=prontuario.id)
    else:
        form = MedicamentoForm()

    return render(request, 'prontuario/medicamento/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Medicamento',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_medicamento(request, medicamento_id):
    med = get_object_or_404(Medicamento, id=medicamento_id)
    prontuario = med.prontuario

    if request.method == 'POST':
        form = MedicamentoForm(request.POST, instance=med)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Medicamento atualizado!')
            return redirect('prontuario:lista_medicamentos', prontuario_id=prontuario.id)
    else:
        form = MedicamentoForm(instance=med)

    return render(request, 'prontuario/medicamento/form.html', {
        'form': form,
        'prontuario': prontuario,
        'medicamento': med,
        'titulo': 'Editar Medicamento',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_medicamentos(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    medicamentos_ativos = prontuario.medicamentos.filter(status='ativo')
    medicamentos_encerrados = prontuario.medicamentos.exclude(status='ativo')

    return render(request, 'prontuario/medicamento/lista.html', {
        'prontuario': prontuario,
        'medicamentos_ativos': medicamentos_ativos,
        'medicamentos_encerrados': medicamentos_encerrados,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def deletar_medicamento(request, medicamento_id):
    med = get_object_or_404(Medicamento, id=medicamento_id)
    prontuario = med.prontuario

    if request.method == 'POST':
        med.delete()
        messages.success(request, 'Medicamento removido.')
        return redirect('prontuario:lista_medicamentos', prontuario_id=prontuario.id)

    return render(request, 'prontuario/confirmar_delete.html', {
        'objeto': med,
        'prontuario': prontuario,
        'tipo': 'medicamento',
    })


# ==============================================================================
# CIF
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_cif(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = AvaliacaoCIFForm(request.POST)
        if form.is_valid():
            cif = form.save(commit=False)
            cif.prontuario = prontuario
            cif.avaliador = request.user
            cif.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Avaliação CIF registrada com sucesso!')
            return redirect('prontuario:lista_cif', prontuario_id=prontuario.id)
    else:
        form = AvaliacaoCIFForm()

    return render(request, 'prontuario/cif/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Avaliação CIF',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_cif(request, cif_id):
    cif = get_object_or_404(AvaliacaoCIF, id=cif_id)
    prontuario = cif.prontuario

    if request.method == 'POST':
        form = AvaliacaoCIFForm(request.POST, instance=cif)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Avaliação CIF atualizada!')
            return redirect('prontuario:lista_cif', prontuario_id=prontuario.id)
    else:
        form = AvaliacaoCIFForm(instance=cif)

    return render(request, 'prontuario/cif/form.html', {
        'form': form,
        'prontuario': prontuario,
        'cif': cif,
        'titulo': 'Editar Avaliação CIF',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_cif(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    avaliacoes = prontuario.avaliacoes_cif.all().order_by('-data_avaliacao')

    return render(request, 'prontuario/cif/lista.html', {
        'prontuario': prontuario,
        'avaliacoes': avaliacoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_cif(request, cif_id):
    cif = get_object_or_404(AvaliacaoCIF, id=cif_id)
    prontuario = cif.prontuario

    return render(request, 'prontuario/cif/detalhes.html', {
        'cif': cif,
        'prontuario': prontuario,
    })


# ==============================================================================
# CARDIORRESPIRATÓRIO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_cardio(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = AvaliacaoCardiorrespiratoriaForm(request.POST)
        if form.is_valid():
            cardio = form.save(commit=False)
            cardio.prontuario = prontuario
            cardio.avaliador = request.user
            cardio.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Avaliação cardiorrespiratória registrada!')
            return redirect('prontuario:lista_cardio', prontuario_id=prontuario.id)
    else:
        form = AvaliacaoCardiorrespiratoriaForm()

    return render(request, 'prontuario/cardio/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Avaliação Cardiorrespiratória',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_cardio(request, cardio_id):
    cardio = get_object_or_404(AvaliacaoCardiorrespiratoria, id=cardio_id)
    prontuario = cardio.prontuario

    if request.method == 'POST':
        form = AvaliacaoCardiorrespiratoriaForm(request.POST, instance=cardio)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Avaliação atualizada!')
            return redirect('prontuario:lista_cardio', prontuario_id=prontuario.id)
    else:
        form = AvaliacaoCardiorrespiratoriaForm(instance=cardio)

    return render(request, 'prontuario/cardio/form.html', {
        'form': form,
        'prontuario': prontuario,
        'cardio': cardio,
        'titulo': 'Editar Avaliação Cardiorrespiratória',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_cardio(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    avaliacoes = prontuario.avaliacoes_cardiorrespiratorias.all().order_by('-data_avaliacao')

    return render(request, 'prontuario/cardio/lista.html', {
        'prontuario': prontuario,
        'avaliacoes': avaliacoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_cardio(request, cardio_id):
    cardio = get_object_or_404(AvaliacaoCardiorrespiratoria, id=cardio_id)
    return render(request, 'prontuario/cardio/detalhes.html', {
        'cardio': cardio,
        'prontuario': cardio.prontuario,
    })


# ==============================================================================
# ESCALAS DE RISCO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_escala(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = EscalaRiscoForm(request.POST)
        if form.is_valid():
            escala = form.save(commit=False)
            escala.prontuario = prontuario
            escala.aplicado_por = request.user
            escala.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Escala registrada!')
            return redirect('prontuario:lista_escalas', prontuario_id=prontuario.id)
    else:
        form = EscalaRiscoForm()

    return render(request, 'prontuario/escala/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Escala de Risco',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_escalas(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    escalas = prontuario.escalas_risco.all().order_by('-data_aplicacao')

    return render(request, 'prontuario/escala/lista.html', {
        'prontuario': prontuario,
        'escalas': escalas,
    })


# ==============================================================================
# RELATÓRIO DIÁRIO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_relatorio(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = RelatorioDiarioForm(request.POST)
        if form.is_valid():
            relatorio = form.save(commit=False)
            relatorio.prontuario = prontuario
            relatorio.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Relatório diário registrado!')
            return redirect('prontuario:lista_relatorios', prontuario_id=prontuario.id)
    else:
        form = RelatorioDiarioForm(initial={
            'data_sessao': date.today(),
            'fisioterapeuta': request.user,
        })

    return render(request, 'prontuario/relatorio/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Relatório Diário',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioDiario, id=relatorio_id)
    prontuario = relatorio.prontuario

    if request.method == 'POST':
        form = RelatorioDiarioForm(request.POST, instance=relatorio)
        if form.is_valid():
            form.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Relatório atualizado!')
            return redirect('prontuario:lista_relatorios', prontuario_id=prontuario.id)
    else:
        form = RelatorioDiarioForm(instance=relatorio)

    return render(request, 'prontuario/relatorio/form.html', {
        'form': form,
        'prontuario': prontuario,
        'relatorio': relatorio,
        'titulo': 'Editar Relatório Diário',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_relatorios(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    relatorios = prontuario.relatorios_diarios.all().order_by('-data_sessao')

    return render(request, 'prontuario/relatorio/lista.html', {
        'prontuario': prontuario,
        'relatorios': relatorios,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioDiario, id=relatorio_id)
    return render(request, 'prontuario/relatorio/detalhes.html', {
        'relatorio': relatorio,
        'prontuario': relatorio.prontuario,
    })


# ==============================================================================
# ENCAMINHAMENTO
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_encaminhamento(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = EncaminhamentoMedicoForm(request.POST)
        if form.is_valid():
            enc = form.save(commit=False)
            enc.prontuario = prontuario
            enc.encaminhado_por = request.user
            enc.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Encaminhamento registrado!')
            return redirect('prontuario:lista_encaminhamentos', prontuario_id=prontuario.id)
    else:
        form = EncaminhamentoMedicoForm()

    return render(request, 'prontuario/encaminhamento/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Encaminhamento Médico',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_encaminhamentos(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    encaminhamentos = prontuario.encaminhamentos.all().order_by('-data_encaminhamento')

    return render(request, 'prontuario/encaminhamento/lista.html', {
        'prontuario': prontuario,
        'encaminhamentos': encaminhamentos,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_encaminhamento(request, encaminhamento_id):
    enc = get_object_or_404(EncaminhamentoMedico, id=encaminhamento_id)
    prontuario = enc.prontuario

    if request.method == 'POST':
        form = EncaminhamentoMedicoForm(request.POST, instance=enc)
        if form.is_valid():
            form.save()
            messages.success(request, 'Encaminhamento atualizado!')
            return redirect('prontuario:lista_encaminhamentos', prontuario_id=prontuario.id)
    else:
        form = EncaminhamentoMedicoForm(instance=enc)

    return render(request, 'prontuario/encaminhamento/form.html', {
        'form': form,
        'prontuario': prontuario,
        'encaminhamento': enc,
        'titulo': 'Editar Encaminhamento',
    })


# ==============================================================================
# EXAMES
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_exame(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = ExameForm(request.POST, request.FILES)
        if form.is_valid():
            exame = form.save(commit=False)
            exame.prontuario = prontuario
            exame.solicitado_por = request.user
            exame.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Exame registrado!')
            return redirect('prontuario:lista_exames', prontuario_id=prontuario.id)
    else:
        form = ExameForm()

    return render(request, 'prontuario/exame/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Exame',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_exames(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    exames = prontuario.exames.all().order_by('-data_solicitacao')

    return render(request, 'prontuario/exame/lista.html', {
        'prontuario': prontuario,
        'exames': exames,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_exame(request, exame_id):
    exame = get_object_or_404(Exame, id=exame_id)
    prontuario = exame.prontuario

    if request.method == 'POST':
        form = ExameForm(request.POST, request.FILES, instance=exame)
        if form.is_valid():
            form.save()
            messages.success(request, 'Exame atualizado!')
            return redirect('prontuario:lista_exames', prontuario_id=prontuario.id)
    else:
        form = ExameForm(instance=exame)

    return render(request, 'prontuario/exame/form.html', {
        'form': form,
        'prontuario': prontuario,
        'exame': exame,
        'titulo': 'Editar Exame',
    })


# ==============================================================================
# EVOLUÇÃO FISIOTERAPÊUTICA
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_evolucao(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    if request.method == 'POST':
        form = EvolucaoFisioterapeuticaForm(request.POST)
        if form.is_valid():
            ev = form.save(commit=False)
            ev.prontuario = prontuario
            ev.save()
            prontuario.registrar_movimentacao()
            messages.success(request, 'Evolução registrada!')
            return redirect('prontuario:lista_evolucoes', prontuario_id=prontuario.id)
    else:
        form = EvolucaoFisioterapeuticaForm(initial={
            'fisioterapeuta': request.user,
        })

    return render(request, 'prontuario/evolucao/form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Evolução Fisioterapêutica',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_evolucao(request, evolucao_id):
    ev = get_object_or_404(EvolucaoFisioterapeutica, id=evolucao_id)
    prontuario = ev.prontuario

    if request.method == 'POST':
        form = EvolucaoFisioterapeuticaForm(request.POST, instance=ev)
        if form.is_valid():
            form.save()
            messages.success(request, 'Evolução atualizada!')
            return redirect('prontuario:lista_evolucoes', prontuario_id=prontuario.id)
    else:
        form = EvolucaoFisioterapeuticaForm(instance=ev)

    return render(request, 'prontuario/evolucao/form.html', {
        'form': form,
        'prontuario': prontuario,
        'evolucao': ev,
        'titulo': 'Editar Evolução',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_evolucoes(request, prontuario_id):
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    evolucoes = prontuario.evolucoes_fisioterapeuticas.all().order_by('-data')

    return render(request, 'prontuario/evolucao/lista.html', {
        'prontuario': prontuario,
        'evolucoes': evolucoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_evolucao(request, evolucao_id):
    ev = get_object_or_404(EvolucaoFisioterapeutica, id=evolucao_id)
    return render(request, 'prontuario/evolucao/detalhes.html', {
        'evolucao': ev,
        'prontuario': ev.prontuario,
    })


# ==============================================================================
# IMPRESSÃO (visualização em HTML)
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def imprimir_prontuario(request, prontuario_id):
    """Página de impressão do prontuário completo (visualização em HTML)."""
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    context = {
        'prontuario': prontuario,
        'atleta': prontuario.atleta,
        'triagens': prontuario.triagens.all(),
        'objetivos': prontuario.objetivos.all(),
        'medicamentos': prontuario.medicamentos.filter(status='ativo'),
        'avaliacoes_cif': prontuario.avaliacoes_cif.all(),
        'avaliacoes_cardio': prontuario.avaliacoes_cardiorrespiratorias.all(),
        'escalas': prontuario.escalas_risco.all(),
        'relatorios': prontuario.relatorios_diarios.all()[:20],
        'encaminhamentos': prontuario.encaminhamentos.all(),
        'exames': prontuario.exames.all(),
        'evolucoes': prontuario.evolucoes_fisioterapeuticas.all()[:20],
    }
    return render(request, 'prontuario/imprimir.html', context)


# ==============================================================================
# EXPORTAR PRONTUÁRIO EM PDF (download real com reportlab)
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def exportar_pdf_prontuario(request, prontuario_id):
    """Gera e faz download do PDF do prontuário completo."""
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        messages.error(request, 'Prontuário não encontrado.')
        return redirect('dashboard:dashboard')

    try:
        buffer = gerar_pdf_prontuario(prontuario)

        nome_arquivo = (
            f'prontuario-{prontuario.numero_prontuario}-'
            f'{prontuario.atleta.usuario.username}.pdf'
        )

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=nome_arquivo,
            content_type='application/pdf',
        )
    except Exception as e:
        messages.error(request, f'Erro ao gerar PDF: {e}')
        return redirect('prontuario:dashboard_prontuario', prontuario_id=prontuario.id)

    # ==============================================================================
# RELATÓRIO CONSOLIDADO — PDF COM TODOS OS PACIENTES
# ==============================================================================
from .pdf_utils import gerar_pdf_relatorio_consolidado


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def relatorio_consolidado_pdf(request):
    """Gera um PDF consolidado com todos os prontuários do projeto."""
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    # Pega todos os prontuários (ou filtra por status, se passado)
    status = request.GET.get('status', '')

    prontuarios = Prontuario.objects.filter(
        projeto=projeto
    ).select_related(
        'atleta', 'atleta__usuario', 'atleta__modalidade', 'fisioterapeuta_responsavel'
    ).order_by('atleta__usuario__first_name')

    if status:
        prontuarios = prontuarios.filter(status=status)

    if not prontuarios.exists():
        messages.warning(request, 'Nenhum prontuário encontrado para gerar o relatório.')
        return redirect('prontuario:lista_prontuarios')

    try:
        buffer = gerar_pdf_relatorio_consolidado(projeto, prontuarios)

        nome_arquivo = f'relatorio-consolidado-{projeto.slug}-{date.today().strftime("%Y%m%d")}.pdf'

        return FileResponse(
            buffer,
            as_attachment=True,
            filename=nome_arquivo,
            content_type='application/pdf',
        )
    except Exception as e:
        messages.error(request, f'Erro ao gerar relatório: {e}')
        return redirect('prontuario:lista_prontuarios')

    # ==============================================================================
# 🔥 COMPARTILHAMENTO DE PRONTUÁRIO COM O TÉCNICO
# ==============================================================================
def pode_acessar_prontuario(view_func):
    """
    Decorator que controla o acesso ao prontuário:
    - Fisio/Coordenador/Psicólogo: total
    - Técnico: somente com compartilhamento ativo
    - Outros: 403
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')

        tipo = getattr(request.user.perfil, 'tipo', None) if hasattr(request.user, 'perfil') else None

        if tipo in ('fisioterapeuta', 'coordenador', 'psicologo'):
            return view_func(request, *args, **kwargs)

        if tipo == 'tecnico':
            prontuario_id = kwargs.get('prontuario_id')
            if prontuario_id:
                tem = CompartilhamentoProntuario.objects.filter(
                    prontuario_id=prontuario_id, tecnico=request.user, ativo=True
                ).exists()
                if tem:
                    return view_func(request, *args, **kwargs)
            return HttpResponseForbidden(
                '<div style="font-family: sans-serif; padding: 60px; text-align: center;">'
                '<h1>🔒 Acesso Restrito</h1>'
                '<p>Este prontuário não foi compartilhado com você.</p>'
                '<a href="/dashboard/tecnico/" style="color: #2BA181;">← Voltar</a></div>'
            )

        return HttpResponseForbidden('Acesso negado.')

    return wrapper


@login_required
def tecnico_prontuarios_compartilhados(request):
    """Lista os prontuários compartilhados com o técnico logado."""
    if not hasattr(request.user, 'perfil') or request.user.perfil.tipo != 'tecnico':
        messages.error(request, 'Acesso restrito a técnicos.')
        return redirect('dashboard:dashboard')

    compartilhamentos = CompartilhamentoProntuario.objects.filter(
        tecnico=request.user, ativo=True
    ).select_related(
        'prontuario', 'prontuario__atleta', 'prontuario__atleta__usuario',
        'prontuario__atleta__modalidade', 'liberado_por'
    ).order_by('-liberado_em')

    return render(request, 'prontuario/tecnico/lista_compartilhados.html', {
        'compartilhamentos': compartilhamentos,
        'total': compartilhamentos.count(),
    })


@login_required
def tecnico_ver_prontuario(request, prontuario_id):
    """Técnico visualiza prontuário compartilhado (leitura + comentar)."""
    prontuario = get_object_or_404(Prontuario, id=prontuario_id)
    compartilhamento = get_object_or_404(
        CompartilhamentoProntuario,
        prontuario=prontuario, tecnico=request.user, ativo=True
    )

    return render(request, 'prontuario/tecnico/ver_prontuario.html', {
        'prontuario': prontuario,
        'compartilhamento': compartilhamento,
        'triagens': prontuario.triagens.all()[:5],
        'objetivos': prontuario.objetivos.all(),
        'medicamentos': prontuario.medicamentos.filter(status='ativo'),
        'relatorios': prontuario.relatorios_diarios.all()[:10],
        'evolucoes': prontuario.evolucoes_fisioterapeuticas.all()[:10],
        'observacoes': prontuario.observacoes_tecnico.select_related('tecnico').order_by('-criado_em'),
        'pode_comentar': compartilhamento.pode_comentar,
    })


@login_required
def tecnico_adicionar_observacao(request, prontuario_id):
    """Técnico registra observação de treino no prontuário compartilhado."""
    prontuario = get_object_or_404(Prontuario, id=prontuario_id)
    compartilhamento = get_object_or_404(
        CompartilhamentoProntuario,
        prontuario=prontuario, tecnico=request.user, ativo=True
    )

    if not compartilhamento.pode_comentar:
        messages.error(request, 'Você não tem permissão para adicionar observações neste prontuário.')
        return redirect('prontuario:tecnico_ver_prontuario', prontuario_id=prontuario.id)

    if request.method == 'POST':
        try:
            observacao = ObservacaoTecnico.objects.create(
                compartilhamento=compartilhamento,
                prontuario=prontuario,
                tecnico=request.user,
                tipo=request.POST.get('tipo', 'treino'),
                nivel_impacto=request.POST.get('nivel_impacto', 'neutro'),
                titulo=request.POST.get('titulo'),
                descricao=request.POST.get('descricao'),
                desempenho_treino=request.POST.get('desempenho_treino') or None,
                dor_relatada=request.POST.get('dor_relatada') or None,
                aderencia=request.POST.get('aderencia') or None,
            )

            if prontuario.fisioterapeuta_responsavel:
                Notificacao.objects.create(
                    usuario=prontuario.fisioterapeuta_responsavel,
                    titulo=f'Nova observação — {prontuario.atleta.usuario.get_full_name()}',
                    mensagem=f'{request.user.get_full_name()} registrou: {observacao.titulo}',
                    link=f'/prontuario/{prontuario.id}/observacoes-tecnico/'
                )

            if observacao.nivel_impacto in ('atencao', 'critico'):
                Alerta.objects.create(
                    atleta=prontuario.atleta,
                    tipo='avaliacao_pendente',
                    mensagem=f'Técnico reportou: {observacao.titulo} ({observacao.get_nivel_impacto_display()})',
                )

            prontuario.registrar_movimentacao()
            messages.success(request, 'Observação registrada! O fisioterapeuta foi notificado.')
            return redirect('prontuario:tecnico_ver_prontuario', prontuario_id=prontuario.id)
        except Exception as e:
            messages.error(request, f'Erro ao registrar observação: {e}')

    return render(request, 'prontuario/tecnico/adicionar_observacao.html', {
        'prontuario': prontuario, 'compartilhamento': compartilhamento,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def fisio_gerenciar_compartilhamento(request, prontuario_id):
    """Fisio libera/revoga acesso do técnico ao prontuário."""
    from django.contrib.auth.models import User as UserModel

    prontuario = get_object_or_404(Prontuario, id=prontuario_id)
    projeto = prontuario.projeto

    tecnicos = UserModel.objects.filter(
        membros_projeto__projeto=projeto,
        membros_projeto__tipo='tecnico',
        membros_projeto__ativo=True,
        perfil__tipo='tecnico'
    ).distinct()

    if request.method == 'POST':
        acao = request.POST.get('acao')
        tecnico_id = request.POST.get('tecnico_id')

        if acao == 'liberar' and tecnico_id:
            tecnico = get_object_or_404(UserModel, id=tecnico_id)
            CompartilhamentoProntuario.objects.update_or_create(
                prontuario=prontuario, tecnico=tecnico,
                defaults={
                    'liberado_por': request.user,
                    'pode_comentar': request.POST.get('pode_comentar') == 'on',
                    'observacao_liberacao': request.POST.get('observacao_liberacao', ''),
                    'ativo': True,
                }
            )
            Notificacao.objects.create(
                usuario=tecnico,
                titulo=f'Prontuário compartilhado — {prontuario.atleta.usuario.get_full_name()}',
                mensagem=f'{request.user.get_full_name()} compartilhou um prontuário com você.',
                link=f'/prontuario/tecnico/{prontuario.id}/'
            )
            messages.success(request, f'Prontuário liberado para {tecnico.get_full_name()}.')

        elif acao == 'revogar' and tecnico_id:
            CompartilhamentoProntuario.objects.filter(
                prontuario=prontuario, tecnico_id=tecnico_id
            ).update(ativo=False)
            messages.success(request, 'Acesso revogado.')

        return redirect('prontuario:fisio_gerenciar_compartilhamento', prontuario_id=prontuario.id)

    compartilhamentos = prontuario.compartilhamentos.select_related(
        'tecnico', 'liberado_por'
    ).filter(ativo=True)

    return render(request, 'prontuario/fisio/gerenciar_compartilhamento.html', {
        'prontuario': prontuario,
        'tecnicos': tecnicos,
        'compartilhamentos': compartilhamentos,
        'tecnicos_com_acesso': [c.tecnico_id for c in compartilhamentos],
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'psicologo')
def fisio_ver_observacoes_tecnico(request, prontuario_id):
    """Fisio vê todas as observações de treino registradas pelos técnicos."""
    prontuario = get_object_or_404(Prontuario, id=prontuario_id)
    observacoes = prontuario.observacoes_tecnico.select_related(
        'tecnico', 'compartilhamento'
    ).order_by('-criado_em')

    return render(request, 'prontuario/fisio/observacoes_tecnico.html', {
        'prontuario': prontuario,
        'observacoes': observacoes,
        'total': observacoes.count(),
        'positivas': observacoes.filter(nivel_impacto='positivo').count(),
        'atencao': observacoes.filter(nivel_impacto__in=['atencao', 'critico']).count(),
    })

# ==============================================================================
# 🔥 TIMELINE CLÍNICA UNIFICADA
# ==============================================================================

@login_required
def timeline_atleta(request, atleta_id):
    """Linha do tempo clínica completa de um atleta."""
    from .timeline_utils import (
        coletar_eventos, agrupar_por_mes, contagem_por_tipo, TIPOS_EVENTO,
    )
    from usuarios.models import Atleta

    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    atleta = get_object_or_404(
        Atleta.objects.select_related('usuario'),
        id=atleta_id,
    )

    # Verifica se o atleta é do projeto ativo
    if not atleta.usuario.membros_projeto.filter(projeto=projeto, ativo=True).exists():
        messages.error(request, 'Atleta não pertence ao projeto ativo.')
        return redirect('prontuario:lista_prontuarios')

    # Filtro por tipo (querystring: ?tipos=consulta,evolucao)
    tipos_filtro = request.GET.get('tipos', '').strip()
    tipos_desejados = [t.strip() for t in tipos_filtro.split(',') if t.strip()] if tipos_filtro else None

    eventos = coletar_eventos(atleta, projeto, tipos_desejados=tipos_desejados)
    grupos = agrupar_por_mes(eventos)
    contagens = contagem_por_tipo(coletar_eventos(atleta, projeto))

    context = {
        'projeto': projeto,
        'atleta': atleta,
        'grupos': grupos,
        'total_eventos': len(eventos),
        'contagens': contagens,
        'tipos_evento': TIPOS_EVENTO,
        'tipos_ativos': tipos_desejados or [],
        'tem_prontuario': hasattr(atleta, 'prontuario'),
    }
    return render(request, 'prontuario/timeline/atleta.html', context)


@login_required
@perfil_required('coordenador', 'fisioterapeuta', 'psicologo', 'tecnico')
def timeline_global(request):
    """Linha do tempo global do projeto — todos os atletas juntos.

    OTIMIZACAO: coleta eventos UMA vez por atleta e reaproveita para contagem.
    """
    from .timeline_utils import agrupar_por_mes, contagem_por_tipo, TIPOS_EVENTO, TODOS_COLETORES
    from usuarios.models import Atleta

    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    atletas = Atleta.objects.filter(
        usuario__membros_projeto__projeto=projeto,
        usuario__membros_projeto__ativo=True,
        usuario__membros_projeto__tipo='atleta',
    ).select_related('usuario').distinct()

    atleta_filtro = (request.GET.get('atleta') or '').strip()
    tipos_filtro = (request.GET.get('tipos') or '').strip()
    tipos_desejados = [t.strip() for t in tipos_filtro.split(',') if t.strip()] if tipos_filtro else None

    atletas_queryset = atletas
    if atleta_filtro:
        atletas_queryset = atletas.filter(id=atleta_filtro)

    # ---- Coleta UMA vez por atleta (reaproveita para contagem) ----
    eventos_todos = []
    for atleta in atletas_queryset[:30]:
        eventos_atleta = []
        for coletor in TODOS_COLETORES:
            try:
                coletor(eventos_atleta, atleta, projeto)
            except Exception as exc:
                import logging
                logging.getLogger(__name__).warning(f'Erro no coletor {coletor.__name__}: {exc}')
        eventos_todos.extend(eventos_atleta)

    # Contagem e' feita ANTES do filtro por tipo
    contagens = contagem_por_tipo(eventos_todos)

    # Filtro por tipo (em memoria, mais rapido que outra varredura)
    if tipos_desejados:
        eventos_todos = [e for e in eventos_todos if e['tipo'] in tipos_desejados]

    eventos_todos.sort(key=lambda x: x['data'], reverse=True)
    grupos = agrupar_por_mes(eventos_todos)

    context = {
        'projeto': projeto,
        'grupos': grupos,
        'total_eventos': len(eventos_todos),
        'contagens': contagens,
        'tipos_evento': TIPOS_EVENTO,
        'tipos_ativos': tipos_desejados or [],
        'atletas': atletas,
        'atleta_filtro': atleta_filtro,
    }
    return render(request, 'prontuario/timeline/global.html', context)
