# ==============================================================================
# REABITECH — TIMELINE CLINICA UNIFICADA
# Agrega eventos de todos os modulos em uma linha do tempo por atleta/projeto.
# ==============================================================================

from datetime import datetime, date, time
from django.utils import timezone


# ------------------------------------------------------------------------------
# Catalogo de tipos de evento (icone + cor por tipo)
# ------------------------------------------------------------------------------
TIPOS_EVENTO = {
    'consulta':       {'label': 'Consulta',              'icone': 'fa-calendar-check',       'cor': 'info'},
    'evolucao':       {'label': 'Evolucao Fisio',        'icone': 'fa-chart-line',           'cor': 'success'},
    'evolucao_fisica':{'label': 'Evolucao Fisica',       'icone': 'fa-heart-pulse',          'cor': 'success'},
    'lesao':          {'label': 'Lesao',                 'icone': 'fa-band-aid',             'cor': 'danger'},
    'tratamento':     {'label': 'Tratamento',            'icone': 'fa-hand-holding-medical', 'cor': 'warning'},
    'avaliacao_psi':  {'label': 'Avaliacao Psicologica', 'icone': 'fa-brain',                'cor': 'primary'},
    'questionario':   {'label': 'Questionario',          'icone': 'fa-clipboard-question',   'cor': 'info'},
    'observacao_tec': {'label': 'Observacao Tecnico',    'icone': 'fa-comments',             'cor': 'secondary'},
    'relatorio':      {'label': 'Relatorio Diario',      'icone': 'fa-clipboard-check',      'cor': 'success'},
    'triagem':        {'label': 'Triagem',               'icone': 'fa-notes-medical',        'cor': 'info'},
    'objetivo':       {'label': 'Objetivo',              'icone': 'fa-bullseye',             'cor': 'primary'},
    'medicamento':    {'label': 'Medicamento',           'icone': 'fa-pills',                'cor': 'warning'},
    'exame':          {'label': 'Exame',                 'icone': 'fa-microscope',           'cor': 'info'},
    'encaminhamento': {'label': 'Encaminhamento',        'icone': 'fa-share',                'cor': 'info'},
    'escala':         {'label': 'Escala de Risco',       'icone': 'fa-gauge-high',           'cor': 'warning'},
    'cif':            {'label': 'Avaliacao CIF',         'icone': 'fa-clipboard-list',       'cor': 'success'},
    'cardio':         {'label': 'Avaliacao Cardio',      'icone': 'fa-heart-pulse',          'cor': 'danger'},
}


# ------------------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------------------
def _aware(d):
    """Converte date/datetime em datetime aware para ordenacao."""
    if d is None:
        return None
    if isinstance(d, datetime):
        return timezone.make_aware(d) if timezone.is_naive(d) else d
    return timezone.make_aware(datetime.combine(d, time(0, 0)))


def _safe_attr(obj, *names, default=None):
    """Retorna o primeiro atributo que existe e nao e vazio."""
    for n in names:
        v = getattr(obj, n, None)
        if v not in (None, '', 0):
            return v
    return default


def _nome_usuario(user):
    if not user:
        return ''
    return user.get_full_name() or user.username


def _add(eventos, tipo, data, titulo, descricao='', extra=None, obj=None, link=None):
    """Adiciona um evento a lista (ignora se data for None)."""
    if data is None:
        return
    meta = TIPOS_EVENTO.get(tipo, {'label': tipo, 'icone': 'fa-circle', 'cor': 'secondary'})
    eventos.append({
        'tipo': tipo,
        'data': data,
        'data_date': data.date() if isinstance(data, datetime) else data,
        'titulo': titulo,
        'descricao': (descricao or '').strip(),
        'icone': meta['icone'],
        'cor': meta['cor'],
        'label_tipo': meta['label'],
        'extra': extra or {},
        'obj': obj,
        'link': link,
    })


# ------------------------------------------------------------------------------
# Coletores
# ------------------------------------------------------------------------------
def _coletar_consultas(eventos, atleta, projeto):
    try:
        from consultas.models import Consulta
    except ImportError:
        return
    qs = Consulta.objects.filter(atleta=atleta, projeto=projeto).select_related('profissional')
    for c in qs:
        dt = _aware(datetime.combine(c.data, c.hora_inicio))
        extra = {
            'profissional': _nome_usuario(c.profissional),
            'status': c.get_status_display(),
            'hora': c.hora_inicio.strftime('%H:%M'),
            'duracao': c.duracao_minutos,
            'local': c.local,
        }
        _add(eventos, 'consulta', dt,
             titulo=c.get_tipo_display(),
             descricao=c.motivo or c.observacoes or '',
             extra=extra, obj=c,
             link=f'/consultas/{c.id}/')


def _coletar_evolucoes(eventos, atleta, projeto):
    try:
        from prontuario.models import EvolucaoFisioterapeutica
    except ImportError:
        return
    qs = EvolucaoFisioterapeutica.objects.filter(
        prontuario__atleta=atleta, prontuario__projeto=projeto
    ).select_related('fisioterapeuta').order_by('-data')
    for e in qs:
        descricao = e.avaliacao or e.conduta or e.subjetivo or e.objetivo or ''
        extra = {
            'profissional': _nome_usuario(e.fisioterapeuta),
            'dor': e.escala_dor,
            'estavel': e.paciente_estavel,
            'encaminhamento': e.necessita_encaminhamento,
        }
        _add(eventos, 'evolucao', e.data,
             titulo=e.get_tipo_display(),
             descricao=descricao,
             extra=extra, obj=e,
             link=f'/prontuario/evolucao/{e.id}/')


def _coletar_relatorios(eventos, atleta, projeto):
    try:
        from prontuario.models import RelatorioDiario
    except ImportError:
        return
    qs = RelatorioDiario.objects.filter(
        prontuario__atleta=atleta, prontuario__projeto=projeto
    ).select_related('fisioterapeuta')
    for r in qs:
        dt = _aware(datetime.combine(r.data_sessao, r.horario_inicio))
        extra = {
            'profissional': _nome_usuario(r.fisioterapeuta),
            'duracao': r.duracao_minutos,
            'dor_antes': r.dor_inicio,
            'dor_depois': r.dor_fim,
        }
        _add(eventos, 'relatorio', dt,
             titulo='Sessao de Fisioterapia',
             descricao=r.procedimentos or r.observacoes or '',
             extra=extra, obj=r,
             link=f'/prontuario/relatorio/{r.id}/')


def _coletar_triagens(eventos, atleta, projeto):
    try:
        from prontuario.models import Triagem
    except ImportError:
        return
    qs = Triagem.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto)
    for t in qs:
        _add(eventos, 'triagem', t.data_triagem,
             titulo=f'Triagem: {t.get_queixa_principal_display()}',
             descricao=t.descricao_queixa or '',
             obj=t,
             link=f'/prontuario/triagem/{t.id}/editar/')


def _coletar_objetivos(eventos, atleta, projeto):
    try:
        from prontuario.models import Objetivo
    except ImportError:
        return
    qs = Objetivo.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto).select_related('criado_por')
    for o in qs:
        dt = _aware(o.data_definicao)
        extra = {
            'prazo': o.get_prazo_display(),
            'status': o.get_status_display(),
            'percentual': o.percentual_alcancado,
        }
        _add(eventos, 'objetivo', dt,
             titulo=o.titulo,
             descricao=o.descricao or '',
             extra=extra, obj=o)


def _coletar_medicamentos(eventos, atleta, projeto):
    try:
        from prontuario.models import Medicamento
    except ImportError:
        return
    qs = Medicamento.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto).select_related('registrado_por')
    for m in qs:
        data = m.data_inicio
        if not data and m.criado_em:
            data = m.criado_em.date()
        extra = {
            'dosagem': m.dosagem,
            'via': m.get_via_display(),
            'frequencia': m.get_frequencia_display(),
            'status': m.get_status_display(),
            'prescritor': m.prescritor,
        }
        _add(eventos, 'medicamento', _aware(data),
             titulo=m.nome,
             descricao=m.indicacao or m.observacoes or '',
             extra=extra, obj=m)


def _coletar_exames(eventos, atleta, projeto):
    try:
        from prontuario.models import Exame
    except ImportError:
        return
    qs = Exame.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto).select_related('solicitado_por')
    for ex in qs:
        dt = _aware(ex.data_realizacao or ex.data_solicitacao)
        extra = {
            'tipo': ex.get_tipo_display(),
            'status': ex.get_status_display(),
            'local': ex.local_realizacao,
        }
        _add(eventos, 'exame', dt,
             titulo=f'{ex.get_tipo_display()}: {ex.descricao}',
             descricao=ex.conclusao or ex.laudo or '',
             extra=extra, obj=ex)


def _coletar_encaminhamentos(eventos, atleta, projeto):
    try:
        from prontuario.models import EncaminhamentoMedico
    except ImportError:
        return
    qs = EncaminhamentoMedico.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto)
    for en in qs:
        dt = _aware(en.data_encaminhamento)
        extra = {
            'especialidade': en.get_especialidade_display(),
            'urgencia': en.get_urgencia_display(),
            'status': en.get_status_display(),
            'medico': en.medico_encaminhado,
        }
        _add(eventos, 'encaminhamento', dt,
             titulo=f'Encaminhamento: {en.get_especialidade_display()}',
             descricao=en.motivo or '',
             extra=extra, obj=en)


def _coletar_escalas(eventos, atleta, projeto):
    try:
        from prontuario.models import EscalaRisco
    except ImportError:
        return
    qs = EscalaRisco.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto)
    for es in qs:
        extra = {
            'pontuacao': es.pontuacao,
            'maxima': es.pontuacao_maxima,
            'nivel': es.get_nivel_risco_display(),
            'percentual': es.percentual_risco,
        }
        _add(eventos, 'escala', es.data_aplicacao,
             titulo=f'{es.get_tipo_display()}: {es.pontuacao}/{es.pontuacao_maxima}',
             descricao=es.interpretacao or '',
             extra=extra, obj=es)


def _coletar_cif(eventos, atleta, projeto):
    try:
        from prontuario.models import AvaliacaoCIF
    except ImportError:
        return
    qs = AvaliacaoCIF.objects.filter(prontuario__atleta=atleta, prontuario__projeto=projeto)
    for a in qs:
        extra = {
            'pontuacao_global': a.pontuacao_global,
            'classificacao': a.classificacao_global,
        }
        _add(eventos, 'cif', a.data_avaliacao,
             titulo='Avaliacao CIF',
             descricao=a.perfil_funcionalidade or '',
             extra=extra, obj=a)


def _coletar_cardio(eventos, atleta, projeto):
    try:
        from prontuario.models import AvaliacaoCardiorrespiratoria
    except ImportError:
        return
    qs = AvaliacaoCardiorrespiratoria.objects.filter(
        prontuario__atleta=atleta, prontuario__projeto=projeto
    )
    for c in qs:
        extra = {
            'condicao': c.get_condicao_principal_display(),
            'dispneia': c.frequencia_dispneia,
            'spo2_repouso': c.spo2_reouso,
            'spo2_esforco': c.spo2_esforco,
        }
        _add(eventos, 'cardio', c.data_avaliacao,
             titulo=f'Cardio: {c.get_condicao_principal_display()}',
             descricao=c.plano_cardiorrespiratorio or c.observacoes or '',
             extra=extra, obj=c)


def _coletar_observacoes_tecnico(eventos, atleta, projeto):
    try:
        from prontuario.models import ObservacaoTecnico
    except ImportError:
        return
    qs = ObservacaoTecnico.objects.filter(
        prontuario__atleta=atleta, prontuario__projeto=projeto
    ).select_related('tecnico')
    for o in qs:
        extra = {
            'tecnico': _nome_usuario(o.tecnico),
            'impacto': o.get_nivel_impacto_display(),
            'desempenho': o.desempenho_treino,
            'dor': o.dor_relatada,
            'aderencia': o.aderencia,
        }
        _add(eventos, 'observacao_tec', o.criado_em,
             titulo=o.titulo,
             descricao=o.descricao,
             extra=extra, obj=o)


# ---- FISIOTERAPIA (field names corrigidos) ----

def _coletar_lesoes(eventos, atleta, projeto):
    """Lesao: atleta, projeto, tipo, gravidade, regiao_corporal, lado, causa,
    local, data_ocorrencia, descricao, diagnostico, previsao_recuperacao,
    status, observacoes, fisioterapeuta_responsavel, imagem."""
    try:
        from fisioterapia.models import Lesao
    except ImportError:
        return
    qs = Lesao.objects.filter(atleta=atleta, projeto=projeto).select_related('fisioterapeuta_responsavel')
    for l in qs:
        titulo = l.tipo or 'Lesao'
        if l.regiao_corporal:
            titulo += f' — {l.regiao_corporal}'
        if l.lado:
            titulo += f' ({l.lado})'
        descricao = l.descricao or l.diagnostico or l.causa or ''
        extra = {
            'gravidade': l.gravidade,
            'local': l.regiao_corporal,
            'status': l.status,
            'profissional': _nome_usuario(l.fisioterapeuta_responsavel) if l.fisioterapeuta_responsavel else '',
        }
        _add(eventos, 'lesao', _aware(l.data_ocorrencia),
             titulo=titulo, descricao=descricao, extra=extra, obj=l)


def _coletar_tratamentos(eventos, atleta, projeto):
    """TratamentoFisioterapico: lesao (FK), descricao, data_inicio,
    data_previsao_termino, data_termino, ativo."""
    try:
        from fisioterapia.models import TratamentoFisioterapico
    except ImportError:
        return
    qs = TratamentoFisioterapico.objects.filter(
        lesao__atleta=atleta, lesao__projeto=projeto
    ).select_related('lesao')
    for t in qs:
        titulo = 'Tratamento'
        if t.lesao and t.lesao.tipo:
            titulo = f'Tratamento — {t.lesao.tipo}'
        extra = {
            'status': 'Ativo' if t.ativo else 'Finalizado',
            'data_fim': t.data_termino,
            'previsao': t.data_previsao_termino,
        }
        _add(eventos, 'tratamento', _aware(t.data_inicio),
             titulo=titulo, descricao=t.descricao or '',
             extra=extra, obj=t)


def _coletar_evolucoes_fisicas(eventos, atleta, projeto):
    """EvolucaoFisica: atleta, projeto, data_registro, dor, mobilidade,
    forca, desempenho, resistencia, flexibilidade, observacoes,
    estagiario_responsavel."""
    try:
        from fisioterapia.models import EvolucaoFisica
    except ImportError:
        return
    qs = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).select_related('estagiario_responsavel')
    for e in qs:
        descricao = e.observacoes or f'Dor {e.dor}/10, Mobilidade {e.mobilidade}/10, Forca {e.forca}/10'
        extra = {
            'dor': e.dor,
            'mobilidade': e.mobilidade,
            'forca': e.forca,
            'desempenho': e.desempenho,
            'resistencia': e.resistencia,
            'flexibilidade': e.flexibilidade,
            'profissional': _nome_usuario(e.estagiario_responsavel) if e.estagiario_responsavel else '',
        }
        _add(eventos, 'evolucao_fisica', _aware(e.data_registro),
             titulo='Evolucao Fisica',
             descricao=descricao,
             extra=extra, obj=e)


# ---- PSICOLOGIA (field names corrigidos) ----

def _coletar_avaliacoes_psi(eventos, atleta, projeto):
    """AvaliacaoPsicologica: atleta, projeto, data, ansiedade, motivacao,
    estresse, autoestima, qualidade_sono, observacoes, psicologo_responsavel."""
    try:
        from psicologia.models import AvaliacaoPsicologica
    except ImportError:
        return
    qs = AvaliacaoPsicologica.objects.filter(
        atleta=atleta, projeto=projeto
    ).select_related('psicologo_responsavel')
    for a in qs:
        extra = {
            'ansiedade': a.ansiedade,
            'motivacao': a.motivacao,
            'estresse': a.estresse,
            'autoestima': a.autoestima,
            'sono': a.qualidade_sono,
            'profissional': _nome_usuario(a.psicologo_responsavel) if a.psicologo_responsavel else '',
        }
        _add(eventos, 'avaliacao_psi', _aware(a.data),
             titulo='Avaliacao Psicologica',
             descricao=a.observacoes or '',
             extra=extra, obj=a)


def _coletar_questionarios(eventos, atleta, projeto):
    """QuestionarioPeriodico: atleta, projeto, data, pergunta_1..5, comentarios."""
    try:
        from psicologia.models import QuestionarioPeriodico
    except ImportError:
        return
    qs = QuestionarioPeriodico.objects.filter(atleta=atleta, projeto=projeto)
    for q in qs:
        respostas = [q.pergunta_1, q.pergunta_2, q.pergunta_3, q.pergunta_4, q.pergunta_5]
        validas = [r for r in respostas if r is not None]
        media = round(sum(validas) / len(validas), 1) if validas else None
        extra = {
            'media': media,
        }
        _add(eventos, 'questionario', _aware(q.data),
             titulo='Questionario Periodico',
             descricao=q.comentarios or '',
             extra=extra, obj=q)


# ------------------------------------------------------------------------------
# Funcao principal
# ------------------------------------------------------------------------------
TODOS_COLETORES = [
    _coletar_consultas,
    _coletar_evolucoes,
    _coletar_relatorios,
    _coletar_triagens,
    _coletar_objetivos,
    _coletar_medicamentos,
    _coletar_exames,
    _coletar_encaminhamentos,
    _coletar_escalas,
    _coletar_cif,
    _coletar_cardio,
    _coletar_observacoes_tecnico,
    _coletar_lesoes,
    _coletar_tratamentos,
    _coletar_evolucoes_fisicas,
    _coletar_avaliacoes_psi,
    _coletar_questionarios,
]


def coletar_eventos(atleta, projeto, tipos_desejados=None):
    """Retorna lista de eventos agregados de todos os modulos."""
    eventos = []
    for coletor in TODOS_COLETORES:
        try:
            coletor(eventos, atleta, projeto)
        except Exception as exc:
            import logging
            logging.getLogger(__name__).warning(f'Erro no coletor {coletor.__name__}: {exc}')

    if tipos_desejados:
        eventos = [e for e in eventos if e['tipo'] in tipos_desejados]

    eventos.sort(key=lambda x: x['data'], reverse=True)
    return eventos


def agrupar_por_mes(eventos):
    """Retorna lista de grupos por mes/ano."""
    MESES = {
        1: 'Janeiro', 2: 'Fevereiro', 3: 'Marco', 4: 'Abril',
        5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
        9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro',
    }
    grupos = []
    for ev in eventos:
        dt = ev['data']
        chave = (dt.year, dt.month)
        if not grupos or grupos[-1]['chave'] != chave:
            grupos.append({
                'chave': chave,
                'mes': dt.month,
                'ano': dt.year,
                'mes_ano': f'{MESES[dt.month]} {dt.year}',
                'eventos': [],
            })
        grupos[-1]['eventos'].append(ev)
    return grupos


def contagem_por_tipo(eventos):
    """Retorna dict {tipo: quantidade}."""
    from collections import Counter
    return dict(Counter(e['tipo'] for e in eventos))
