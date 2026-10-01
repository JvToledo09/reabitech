# ==============================================================================
# REABITECH — APP PRONTUÁRIO
# Views (CRUD completo de todos os modelos)
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count
from django.core.paginator import Paginator
from datetime import date, timedelta

from usuarios.models import Atleta, Perfil
from usuarios.decorators import perfil_required
from projetos.models import Projeto, MembroProjeto

from .models import (
    Prontuario, Triagem, Objetivo, Medicamento,
    AvaliacaoCIF, AvaliacaoCardiorrespiratoria,
    EscalaRisco, RelatorioDiario, EncaminhamentoMedico,
    Exame, EvolucaoFisioterapeutica
)
from .forms import (
    ProntuarioForm, TriagemForm, ObjetivoForm, MedicamentoForm,
    AvaliacaoCIFForm, AvaliacaoCardiorrespiratoriaForm,
    EscalaRiscoForm, RelatorioDiarioForm, EncaminhamentoMedicoForm,
    ExameForm, EvolucaoFisioterapeuticaForm
)


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

    # Última movimentação
    prontuario.registrar_movimentacao()

    # Coleta dados de cada seção
    ultima_triagem = prontuario.triagens.first()
    ultima_cif = prontuario.avaliacoes_cif.first()
    ultima_cardio = prontuario.avaliacoes_cardiorrespiratorias.first()
    ultimo_relatorio = prontuario.relatorios_diarios.first()
    ultima_evolucao = prontuario.evolucoes_fisioterapeuticas.first()

    # Contadores
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

    # Alertas
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
        # Contadores
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
        # Alertas
        'tem_alerta_risco_alto': tem_alerta_risco_alto,
        'tem_alerta_cardio': tem_alerta_cardio,
        # Objetivos em destaque
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
    """Lista todos os prontuários do projeto."""
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    prontuarios = Prontuario.objects.filter(
        projeto=projeto
    ).select_related('atleta', 'atleta__usuario', 'fisioterapeuta_responsavel')

    # Filtros
    status_filtro = request.GET.get('status', '')
    busca = request.GET.get('q', '')

    if status_filtro:
        prontuarios = prontuarios.filter(status=status_filtro)

    if busca:
        prontuarios = prontuarios.filter(
            Q(numero_prontuario__icontains=busca) |
            Q(atleta__usuario__first_name__icontains=busca) |
            Q(atleta__usuario__last_name__icontains=busca) |
            Q(atleta__rm__icontains=busca)
        )

    prontuarios = prontuarios.order_by('-criado_em')

    # Paginação
    paginator = Paginator(prontuarios, 20)
    page = request.GET.get('page', 1)
    prontuarios_paginados = paginator.get_page(page)

    context = {
        'projeto': projeto,
        'prontuarios': prontuarios_paginados,
        'status_filtro': status_filtro,
        'busca': busca,
        'status_choices': Prontuario.STATUS_CHOICES,
        'total': paginator.count,
    }
    return render(request, 'prontuario/lista.html', context)


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

    # Verifica se já existe prontuário
    if hasattr(atleta, 'prontuario'):
        messages.info(request, 'Este atleta já possui prontuário. Redirecionando...')
        return redirect('prontuario:dashboard_prontuario', prontuario_id=atleta.prontuario.id)

    if request.method == 'POST':
        form = ProntuarioForm(request.POST)
        if form.is_valid():
            prontuario = form.save(commit=False)
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
            'atleta': atleta,
            'projeto': projeto,
        })
        form.fields['atleta'].widget = forms.HiddenInput()
        form.fields['projeto'].widget = forms.HiddenInput()

    context = {
        'form': form,
        'atleta': atleta,
        'projeto': projeto,
    }
    return render(request, 'prontuario/criar.html', context)


# ==============================================================================
# TRIAGEM — Criar/Editar
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def criar_triagem(request, prontuario_id):
    """Cria uma nova triagem."""
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

    context = {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Nova Triagem',
    }
    return render(request, 'prontuario/triagem_form.html', context)


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def editar_triagem(request, triagem_id):
    """Edita uma triagem existente."""
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

    context = {
        'form': form,
        'prontuario': prontuario,
        'triagem': triagem,
        'titulo': 'Editar Triagem',
    }
    return render(request, 'prontuario/triagem_form.html', context)


@login_required
@perfil_required('fisioterapeuta', 'coordenador')
def lista_triagens(request, prontuario_id):
    """Lista todas as triagens de um prontuário."""
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    triagens = prontuario.triagens.all().order_by('-data_triagem')

    return render(request, 'prontuario/triagens_lista.html', {
        'prontuario': prontuario,
        'triagens': triagens,
    })


# ==============================================================================
# OBJETIVOS — CRUD
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def criar_objetivo(request, prontuario_id):
    """Cria um novo objetivo."""
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

    return render(request, 'prontuario/objetivo_form.html', {
        'form': form,
        'prontuario': prontuario,
        'titulo': 'Novo Objetivo',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def editar_objetivo(request, objetivo_id):
    """Edita um objetivo existente."""
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

    return render(request, 'prontuario/objetivo_form.html', {
        'form': form,
        'prontuario': prontuario,
        'objetivo': objetivo,
        'titulo': 'Editar Objetivo',
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def lista_objetivos(request, prontuario_id):
    """Lista todos os objetivos do prontuário."""
    prontuario = get_prontuario_ativo(request, prontuario_id)
    if not prontuario:
        return redirect('dashboard:dashboard')

    objetivos_curto = prontuario.objetivos.filter(prazo='curto')
    objetivos_medio = prontuario.objetivos.filter(prazo='medio')
    objetivos_longo = prontuario.objetivos.filter(prazo='longo')

    return render(request, 'prontuario/objetivos_lista.html', {
        'prontuario': prontuario,
        'objetivos_curto': objetivos_curto,
        'objetivos_medio': objetivos_medio,
        'objetivos_longo': objetivos_longo,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def deletar_objetivo(request, objetivo_id):
    """Remove um objetivo."""
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
# MEDICAMENTOS — CRUD
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

    return render(request, 'prontuario/medicamento_form.html', {
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

    return render(request, 'prontuario/medicamento_form.html', {
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

    return render(request, 'prontuario/medicamentos_lista.html', {
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
# CIF — CRUD
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

    return render(request, 'prontuario/cif_form.html', {
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

    return render(request, 'prontuario/cif_form.html', {
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

    return render(request, 'prontuario/cif_lista.html', {
        'prontuario': prontuario,
        'avaliacoes': avaliacoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_cif(request, cif_id):
    cif = get_object_or_404(AvaliacaoCIF, id=cif_id)
    prontuario = cif.prontuario

    return render(request, 'prontuario/cif_detalhes.html', {
        'cif': cif,
        'prontuario': prontuario,
    })


# ==============================================================================
# CARDIORRESPIRATÓRIO — CRUD
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

    return render(request, 'prontuario/cardio_form.html', {
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

    return render(request, 'prontuario/cardio_form.html', {
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

    return render(request, 'prontuario/cardio_lista.html', {
        'prontuario': prontuario,
        'avaliacoes': avaliacoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_cardio(request, cardio_id):
    cardio = get_object_or_404(AvaliacaoCardiorrespiratoria, id=cardio_id)
    return render(request, 'prontuario/cardio_detalhes.html', {
        'cardio': cardio,
        'prontuario': cardio.prontuario,
    })


# ==============================================================================
# ESCALAS DE RISCO — CRUD
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

    return render(request, 'prontuario/escala_form.html', {
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

    return render(request, 'prontuario/escalas_lista.html', {
        'prontuario': prontuario,
        'escalas': escalas,
    })


# ==============================================================================
# RELATÓRIO DIÁRIO — CRUD
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

    return render(request, 'prontuario/relatorio_form.html', {
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

    return render(request, 'prontuario/relatorio_form.html', {
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

    return render(request, 'prontuario/relatorios_lista.html', {
        'prontuario': prontuario,
        'relatorios': relatorios,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_relatorio(request, relatorio_id):
    relatorio = get_object_or_404(RelatorioDiario, id=relatorio_id)
    return render(request, 'prontuario/relatorio_detalhes.html', {
        'relatorio': relatorio,
        'prontuario': relatorio.prontuario,
    })


# ==============================================================================
# ENCAMINHAMENTO — CRUD
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

    return render(request, 'prontuario/encaminhamento_form.html', {
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

    return render(request, 'prontuario/encaminhamentos_lista.html', {
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

    return render(request, 'prontuario/encaminhamento_form.html', {
        'form': form,
        'prontuario': prontuario,
        'encaminhamento': enc,
        'titulo': 'Editar Encaminhamento',
    })


# ==============================================================================
# EXAMES — CRUD
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

    return render(request, 'prontuario/exame_form.html', {
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

    return render(request, 'prontuario/exames_lista.html', {
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

    return render(request, 'prontuario/exame_form.html', {
        'form': form,
        'prontuario': prontuario,
        'exame': exame,
        'titulo': 'Editar Exame',
    })


# ==============================================================================
# EVOLUÇÃO FISIOTERAPÊUTICA — CRUD
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

    return render(request, 'prontuario/evolucao_form.html', {
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

    return render(request, 'prontuario/evolucao_form.html', {
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

    return render(request, 'prontuario/evolucoes_lista.html', {
        'prontuario': prontuario,
        'evolucoes': evolucoes,
    })


@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def detalhes_evolucao(request, evolucao_id):
    ev = get_object_or_404(EvolucaoFisioterapeutica, id=evolucao_id)
    return render(request, 'prontuario/evolucao_detalhes.html', {
        'evolucao': ev,
        'prontuario': ev.prontuario,
    })


# ==============================================================================
# RELATÓRIO COMPLETO EM PDF (esqueleto)
# ==============================================================================
@login_required
@perfil_required('fisioterapeuta', 'coordenador', 'tecnico')
def imprimir_prontuario(request, prontuario_id):
    """Página de impressão do prontuário completo."""
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