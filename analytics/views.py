# ==============================================================================
# REABITECH — VIEWS DE ANALYTICS
# Dashboard analítico avançado + APIs JSON para gráficos
# ==============================================================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta, date

from projetos.models import Projeto, MembroProjeto
from usuarios.models import Atleta, Alerta, ModalidadeEsportiva
from fisioterapia.models import (
    Lesao, TratamentoFisioterapico, ExercicioRecuperacao, EvolucaoFisica,
)
from psicologia.models import AvaliacaoPsicologica
from consultas.models import Consulta

# Imports do prontuário — só o essencial (evita ImportError)
try:
    from prontuario.models import Prontuario
except Exception:
    Prontuario = None

from .utils import (
    PERIODOS, get_periodo, aplicar_periodo, get_periodo_anterior,
    comparar_periodos, calcular_variacao,
    serie_por_dia, serie_por_mes,
    agrupar_por_choice, gerar_csv,
)


# ==============================================================================
# HELPERS
# ==============================================================================
def _get_projeto_ativo(request):
    pid = request.session.get('projeto_id')
    if not pid:
        return None
    try:
        projeto = Projeto.objects.get(id=pid, ativo=True)
    except Projeto.DoesNotExist:
        return None
    if not MembroProjeto.objects.filter(
        projeto=projeto, usuario=request.user, ativo=True
    ).exists():
        return None
    return projeto


def _get_tipo_usuario(request):
    try:
        return request.user.perfil.tipo
    except Exception:
        return None


def _pode_ver(user_tipo):
    return user_tipo in ('coordenador', 'fisioterapeuta', 'psicologo', 'tecnico')


# ==============================================================================
# VIEW PRINCIPAL — Dashboard Analítico
# ==============================================================================
@login_required
def dashboard_analitico(request):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Selecione um projeto ativo.')
        return redirect('dashboard:dashboard')

    tipo = _get_tipo_usuario(request)
    if not _pode_ver(tipo):
        messages.info(request, 'Dashboard analítico é exclusivo para profissionais da equipe.')
        return redirect('dashboard:dashboard')

    data_inicio, data_fim, periodo_key, periodo_label = get_periodo(request)
    data_ini_ant, data_fim_ant = get_periodo_anterior(data_inicio, data_fim)

    membros_atletas = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario_id', flat=True)

    atletas = Atleta.objects.filter(usuario_id__in=membros_atletas)
    atletas_ids = list(atletas.values_list('id', flat=True))

    # ============================================================
    # KPIs com variação
    # ============================================================
    total_atletas = atletas.count()

    qs_evol = EvolucaoFisica.objects.filter(projeto=projeto)
    ev_janela = aplicar_periodo(qs_evol, 'data_registro', data_inicio, data_fim)
    ev_anterior = aplicar_periodo(qs_evol, 'data_registro', data_ini_ant, data_fim_ant)
    kpi_evolucoes = comparar_periodos(ev_janela, ev_anterior, agregacao='count')

    qs_psi = AvaliacaoPsicologica.objects.filter(projeto=projeto)
    psi_janela = aplicar_periodo(qs_psi, 'data', data_inicio, data_fim)
    psi_anterior = aplicar_periodo(qs_psi, 'data', data_ini_ant, data_fim_ant)
    kpi_psi = comparar_periodos(psi_janela, psi_anterior, agregacao='count')

    qs_cons = Consulta.objects.filter(projeto=projeto)
    cons_janela = aplicar_periodo(qs_cons, 'data', data_inicio, data_fim)
    cons_anterior = aplicar_periodo(qs_cons, 'data', data_ini_ant, data_fim_ant)
    kpi_consultas = comparar_periodos(cons_janela, cons_anterior, agregacao='count')

    qs_les = Lesao.objects.filter(projeto=projeto)
    les_janela = aplicar_periodo(qs_les, 'data_ocorrencia', data_inicio, data_fim)
    les_anterior = aplicar_periodo(qs_les, 'data_ocorrencia', data_ini_ant, data_fim_ant)
    kpi_lesoes = comparar_periodos(les_janela, les_anterior, agregacao='count')

    media_rec_atual = (ev_janela.aggregate(v=Avg('desempenho'))['v'] or 0) * 10
    media_rec_ant = (ev_anterior.aggregate(v=Avg('desempenho'))['v'] or 0) * 10
    kpi_recuperacao = calcular_variacao(media_rec_atual, media_rec_ant)

    dor_atual = ev_janela.aggregate(v=Avg('dor'))['v'] or 0
    dor_ant = ev_anterior.aggregate(v=Avg('dor'))['v'] or 0
    kpi_dor = calcular_variacao(dor_atual, dor_ant)
    if kpi_dor['direcao'] == 'down':
        kpi_dor['cor'] = 'success'
    elif kpi_dor['direcao'] == 'up':
        kpi_dor['cor'] = 'danger'

    # Adesão
    ex_total = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta_id__in=atletas_ids,
        tratamento__lesao__projeto=projeto,
    )
    ex_feitos = ex_total.filter(check_realizado=True).count()
    ex_total_n = ex_total.count()
    adesao = round((ex_feitos / ex_total_n) * 100, 1) if ex_total_n else 0

    total_prontuarios = 0
    if Prontuario:
        try:
            total_prontuarios = Prontuario.objects.filter(projeto=projeto).count()
        except Exception:
            total_prontuarios = 0

    alertas_abertos = Alerta.objects.filter(
        atleta_id__in=atletas_ids, resolvido=False
    ).count()

    # ============================================================
    # Séries temporais
    # ============================================================
    ev_labels, ev_valores = serie_por_dia(
        ev_janela, 'data_registro', 'desempenho',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim,
    )
    ev_valores = [round(v * 10, 1) for v in ev_valores]
    ev_valores = [round(v * 10, 1) for v in ev_valores]
    _, dor_valores = serie_por_dia(
        ev_janela, 'data_registro', 'dor',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim,
    )
    cons_labels, cons_valores = serie_por_dia(
        cons_janela, 'data',
        agregacao='count', data_inicio=data_inicio, data_fim=data_fim,
    )

    meses_labels, meses_evol = serie_por_mes(
        qs_evol, 'data_registro', 'desempenho',
        agregacao='avg', meses=6,
    )
    meses_evol = [round(v * 10, 1) for v in meses_evol]
    meses_evol = [round(v * 10, 1) for v in meses_evol]
    _, meses_cons = serie_por_mes(qs_cons, 'data', agregacao='count', meses=6)
    _, meses_psi = serie_por_mes(qs_psi, 'data', agregacao='count', meses=6)

    # ============================================================
    # Distribuições
    # ============================================================
    les_tipos_labels, les_tipos_data = agrupar_por_choice(
        les_janela, 'tipo', Lesao.TIPO_LESAO
    )
    cons_status_labels, cons_status_data = agrupar_por_choice(
        cons_janela, 'status', Consulta.STATUS_CHOICES
    )

    psi_status_labels, psi_status_data = [], []
    try:
        bom = psi_janela.filter(ansiedade__lte=3).count()
        regular = psi_janela.filter(ansiedade__gte=4, ansiedade__lte=6).count()
        atencao = psi_janela.filter(ansiedade__gte=7).count()
        if bom + regular + atencao > 0:
            psi_status_labels = ['Bom', 'Regular', 'Atenção']
            psi_status_data = [bom, regular, atencao]
    except Exception:
        pass

    modal_labels, modal_data = [], []
    try:
        for m in ModalidadeEsportiva.objects.all():
            n = atletas.filter(modalidade=m).count()
            if n > 0:
                modal_labels.append(m.nome)
                modal_data.append(n)
    except Exception:
        pass

    # ============================================================
    # Rankings
    # ============================================================
    ranking_atletas = []
    try:
        for atleta in atletas.select_related('usuario', 'modalidade')[:30]:
            evs = ev_janela.filter(atleta=atleta)
            if not evs.exists():
                continue
            media_rec = (evs.aggregate(v=Avg('desempenho'))['v'] or 0) * 10
            media_dor = evs.aggregate(v=Avg('dor'))['v'] or 0

            ex_at = ExercicioRecuperacao.objects.filter(
                tratamento__lesao__atleta=atleta,
                tratamento__lesao__projeto=projeto,
            )
            adesao_at = 0
            if ex_at.exists():
                adesao_at = round(
                    (ex_at.filter(check_realizado=True).count() / ex_at.count()) * 100, 1
                )

            ranking_atletas.append({
                'atleta': atleta,
                'media_recuperacao': round(media_rec, 1),
                'media_dor': round(media_dor, 1),
                'total_evolucoes': evs.count(),
                'adesao': adesao_at,
            })
        ranking_atletas.sort(key=lambda x: x['media_recuperacao'], reverse=True)
    except Exception:
        ranking_atletas = []

    top_atletas = ranking_atletas[:8]
    atletas_atencao = [a for a in ranking_atletas if a['media_recuperacao'] < 40][:5]

    modal_rank_labels, modal_rank_data = [], []
    try:
        for m in ModalidadeEsportiva.objects.all():
            n = les_janela.filter(atleta__modalidade=m).count()
            if n > 0:
                modal_rank_labels.append(m.nome)
                modal_rank_data.append(n)
        pares = sorted(zip(modal_rank_labels, modal_rank_data), key=lambda x: -x[1])[:6]
        modal_rank_labels = [p[0] for p in pares]
        modal_rank_data = [p[1] for p in pares]
    except Exception:
        pass

    # Heatmap semanal
    DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    heat_counts = [0] * 7
    try:
        for e in ev_janela.only('data_registro').iterator():
            if e.data_registro:
                heat_counts[e.data_registro.weekday()] += 1
        for c in cons_janela.only('data').iterator():
            if c.data:
                heat_counts[c.data.weekday()] += 1
    except Exception:
        pass

    context = {
        'projeto': projeto,
        'tipo_usuario': tipo,
        'periodo_key': periodo_key,
        'periodo_label': periodo_label,
        'periodos': PERIODOS,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'kpi_evolucoes': kpi_evolucoes,
        'kpi_psi': kpi_psi,
        'kpi_consultas': kpi_consultas,
        'kpi_lesoes': kpi_lesoes,
        'kpi_recuperacao': kpi_recuperacao,
        'kpi_dor': kpi_dor,
        'total_atletas': total_atletas,
        'adesao_geral': adesao,
        'total_prontuarios': total_prontuarios,
        'alertas_abertos': alertas_abertos,
        'total_exercicios': ex_total_n,
        'total_exercicios_feitos': ex_feitos,
        'ev_labels': ev_labels,
        'ev_valores': ev_valores,
        'dor_valores': dor_valores,
        'cons_labels': cons_labels,
        'cons_valores': cons_valores,
        'meses_labels': meses_labels,
        'meses_evol': meses_evol,
        'meses_cons': meses_cons,
        'meses_psi': meses_psi,
        'les_tipos_labels': les_tipos_labels,
        'les_tipos_data': les_tipos_data,
        'cons_status_labels': cons_status_labels,
        'cons_status_data': cons_status_data,
        'psi_status_labels': psi_status_labels,
        'psi_status_data': psi_status_data,
        'modal_labels': modal_labels,
        'modal_data': modal_data,
        'top_atletas': top_atletas,
        'atletas_atencao': atletas_atencao,
        'modal_rank_labels': modal_rank_labels,
        'modal_rank_data': modal_rank_data,
        'heatmap_labels': DIAS,
        'heatmap_valores': heat_counts,
    }
    return render(request, 'analytics/dashboard.html', context)


# ==============================================================================
# APIs JSON
# ==============================================================================
@login_required
def api_serie_temporal(request):
    projeto = _get_projeto_ativo(request)
    if not projeto or not _pode_ver(_get_tipo_usuario(request)):
        return JsonResponse({'erro': 'sem acesso'}, status=403)
    data_inicio, data_fim, _, _ = get_periodo(request)
    qs = aplicar_periodo(EvolucaoFisica.objects.filter(projeto=projeto),
        'data_registro', data_inicio, data_fim)
    labels, rec = serie_por_dia(qs, 'data_registro', 'desempenho',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim)
    rec = [round(v * 10, 1) for v in rec]
    rec = [round(v * 10, 1) for v in rec]
    _, dor = serie_por_dia(qs, 'data_registro', 'dor',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim)
    return JsonResponse({
        'labels': labels,
        'series': [
            {'nome': 'Recuperação (%)', 'valores': rec, 'cor': '#2BA181'},
            {'nome': 'Dor (0-10)', 'valores': dor, 'cor': '#ef4444'},
        ],
    })


@login_required
def api_distribuicoes(request):
    projeto = _get_projeto_ativo(request)
    if not projeto or not _pode_ver(_get_tipo_usuario(request)):
        return JsonResponse({'erro': 'sem acesso'}, status=403)
    data_inicio, data_fim, _, _ = get_periodo(request)
    les = aplicar_periodo(Lesao.objects.filter(projeto=projeto),
        'data_ocorrencia', data_inicio, data_fim)
    cons = aplicar_periodo(Consulta.objects.filter(projeto=projeto),
        'data', data_inicio, data_fim)
    ll, ld = agrupar_por_choice(les, 'tipo', Lesao.TIPO_LESAO)
    cl, cd = agrupar_por_choice(cons, 'status', Consulta.STATUS_CHOICES)
    return JsonResponse({
        'lesoes': {'labels': ll, 'data': ld},
        'consultas': {'labels': cl, 'data': cd},
    })


@login_required
def api_ranking_atletas(request):
    projeto = _get_projeto_ativo(request)
    if not projeto or not _pode_ver(_get_tipo_usuario(request)):
        return JsonResponse({'erro': 'sem acesso'}, status=403)
    data_inicio, data_fim, _, _ = get_periodo(request)
    membros_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario_id', flat=True)
    atletas = Atleta.objects.filter(usuario_id__in=membros_ids).select_related('usuario')
    qs = aplicar_periodo(EvolucaoFisica.objects.filter(projeto=projeto),
        'data_registro', data_inicio, data_fim)
    ranking = []
    for atleta in atletas:
        evs = qs.filter(atleta=atleta)
        if not evs.exists():
            continue
        media = (evs.aggregate(v=Avg('desempenho'))['v'] or 0) * 10
        ranking.append({
            'nome': atleta.usuario.get_full_name() or atleta.usuario.username,
            'valor': round(media, 1),
        })
    ranking.sort(key=lambda x: x['valor'], reverse=True)
    top = ranking[:10]
    return JsonResponse({
        'labels': [r['nome'] for r in top],
        'data': [r['valor'] for r in top],
    })


@login_required
def api_heatmap(request):
    projeto = _get_projeto_ativo(request)
    if not projeto or not _pode_ver(_get_tipo_usuario(request)):
        return JsonResponse({'erro': 'sem acesso'}, status=403)
    data_inicio, data_fim, _, _ = get_periodo(request)
    ev = aplicar_periodo(EvolucaoFisica.objects.filter(projeto=projeto),
        'data_registro', data_inicio, data_fim)
    cons = aplicar_periodo(Consulta.objects.filter(projeto=projeto),
        'data', data_inicio, data_fim)
    DIAS = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
    counts = [0] * 7
    for e in ev.only('data_registro').iterator():
        if e.data_registro:
            counts[e.data_registro.weekday()] += 1
    for c in cons.only('data').iterator():
        if c.data:
            counts[c.data.weekday()] += 1
    return JsonResponse({'labels': DIAS, 'data': counts})


@login_required
def exportar_serie_csv(request):
    projeto = _get_projeto_ativo(request)
    if not projeto or not _pode_ver(_get_tipo_usuario(request)):
        messages.error(request, 'Sem permissão.')
        return redirect('dashboard:dashboard')
    data_inicio, data_fim, _, _ = get_periodo(request)
    qs = aplicar_periodo(EvolucaoFisica.objects.filter(projeto=projeto),
        'data_registro', data_inicio, data_fim)
    labels, rec = serie_por_dia(qs, 'data_registro', 'desempenho',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim)
    rec = [round(v * 10, 1) for v in rec]
    rec = [round(v * 10, 1) for v in rec]
    _, dor = serie_por_dia(qs, 'data_registro', 'dor',
        agregacao='avg', data_inicio=data_inicio, data_fim=data_fim)
    _, n_evol = serie_por_dia(qs, 'data_registro', agregacao='count',
        data_inicio=data_inicio, data_fim=data_fim)
    csv_content = gerar_csv(labels, {
        'Recuperacao_Media_%': rec,
        'Dor_Media': dor,
        'Num_Evolucoes': n_evol,
    })
    response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
    nome = f'analytics_{projeto.slug}_{timezone.now().strftime("%Y%m%d")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    response.write('\ufeff')
    return response
