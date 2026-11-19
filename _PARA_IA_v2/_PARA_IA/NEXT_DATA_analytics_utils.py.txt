# ==============================================================================
# REABITECH — UTILITÁRIOS DE ANALYTICS
# ==============================================================================

from datetime import timedelta, date, datetime
from collections import defaultdict

from django.db.models import Count, Avg, Sum, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone


PERIODOS = {
    '7d':   {'label': 'Últimos 7 dias',  'dias': 7},
    '30d':  {'label': 'Últimos 30 dias', 'dias': 30},
    '90d':  {'label': 'Últimos 90 dias', 'dias': 90},
    '180d': {'label': 'Últimos 6 meses', 'dias': 180},
    '365d': {'label': 'Último ano',      'dias': 365},
    'tudo': {'label': 'Todo o período',  'dias': None},
}

PERIODO_DEFAULT = '30d'


def get_periodo(request):
    key = request.GET.get('periodo', PERIODO_DEFAULT)
    if key not in PERIODOS:
        key = PERIODO_DEFAULT
    dias = PERIODOS[key]['dias']
    label = PERIODOS[key]['label']
    hoje = timezone.localdate()
    data_fim = hoje
    data_inicio = (hoje - timedelta(days=dias)) if dias else None
    return data_inicio, data_fim, key, label


def aplicar_periodo(qs, campo_data, data_inicio, data_fim):
    if data_inicio:
        qs = qs.filter(**{f'{campo_data}__gte': data_inicio})
    if data_fim:
        qs = qs.filter(**{f'{campo_data}__lte': data_fim})
    return qs


def get_periodo_anterior(data_inicio, data_fim):
    if not data_inicio or not data_fim:
        return None, None
    duracao = (data_fim - data_inicio).days or 1
    fim_ant = data_inicio - timedelta(days=1)
    inicio_ant = fim_ant - timedelta(days=duracao)
    return inicio_ant, fim_ant


def calcular_variacao(valor_atual, valor_anterior):
    try:
        atual = float(valor_atual or 0)
        anterior = float(valor_anterior or 0)
    except (TypeError, ValueError):
        atual = anterior = 0

    if anterior == 0:
        pct = 100.0 if atual > 0 else 0.0
    else:
        pct = round(((atual - anterior) / anterior) * 100, 1)

    if pct > 1:
        direcao, cor = 'up', 'success'
    elif pct < -1:
        direcao, cor = 'down', 'danger'
    else:
        direcao, cor = 'flat', 'secondary'

    return {
        'valor': atual,
        'variacao_pct': pct,
        'direcao': direcao,
        'cor': cor,
    }


def comparar_periodos(qs_atual, qs_anterior, campo_agregado=None, agregacao='count'):
    try:
        if agregacao == 'count':
            v_atual = qs_atual.count()
            v_anterior = qs_anterior.count()
        elif agregacao == 'avg' and campo_agregado:
            v_atual = qs_atual.aggregate(v=Avg(campo_agregado))['v'] or 0
            v_anterior = qs_anterior.aggregate(v=Avg(campo_agregado))['v'] or 0
        elif agregacao == 'sum' and campo_agregado:
            v_atual = qs_atual.aggregate(v=Sum(campo_agregado))['v'] or 0
            v_anterior = qs_anterior.aggregate(v=Sum(campo_agregado))['v'] or 0
        else:
            v_atual = v_anterior = 0
        return calcular_variacao(v_atual, v_anterior)
    except Exception:
        return calcular_variacao(0, 0)


def serie_por_dia(qs, campo_data, campo_valor=None, agregacao='count', data_inicio=None, data_fim=None):
    try:
        qs = qs.annotate(_dia=TruncDate(campo_data))
        if agregacao == 'count':
            dados = qs.values('_dia').annotate(v=Count('id')).order_by('_dia')
        elif agregacao == 'avg' and campo_valor:
            dados = qs.values('_dia').annotate(v=Avg(campo_valor)).order_by('_dia')
        elif agregacao == 'sum' and campo_valor:
            dados = qs.values('_dia').annotate(v=Sum(campo_valor)).order_by('_dia')
        else:
            return [], []

        dict_dados = {item['_dia']: round(float(item['v'] or 0), 1) for item in dados}

        if data_inicio and data_fim:
            labels, valores = [], []
            dia = data_inicio
            while dia <= data_fim:
                labels.append(dia.strftime('%d/%m'))
                valores.append(dict_dados.get(dia, 0))
                dia += timedelta(days=1)
            return labels, valores

        labels = [d.strftime('%d/%m') for d in dict_dados.keys()]
        valores = list(dict_dados.values())
        return labels, valores
    except Exception:
        return [], []


def serie_por_mes(qs, campo_data, campo_valor=None, agregacao='count', meses=6):
    try:
        qs = qs.annotate(_mes=TruncMonth(campo_data))
        if agregacao == 'count':
            dados = qs.values('_mes').annotate(v=Count('id')).order_by('_mes')
        elif agregacao == 'avg' and campo_valor:
            dados = qs.values('_mes').annotate(v=Avg(campo_valor)).order_by('_mes')
        elif agregacao == 'sum' and campo_valor:
            dados = qs.values('_mes').annotate(v=Sum(campo_valor)).order_by('_mes')
        else:
            return [], []

        dict_dados = {item['_mes'].strftime('%m/%Y'): round(float(item['v'] or 0), 1) for item in dados}

        hoje = timezone.localdate()
        labels, valores = [], []
        ano, mes = hoje.year, hoje.month
        for _ in range(meses):
            label = f"{mes:02d}/{ano}"
            labels.append(label)
            valores.append(dict_dados.get(label, 0))
            mes -= 1
            if mes == 0:
                mes = 12
                ano -= 1
        labels.reverse()
        valores.reverse()
        return labels, valores
    except Exception:
        return [], []


def top_n(qs, campo, n=5):
    try:
        dados = qs.values(campo).annotate(v=Count('id')).order_by('-v')[:n]
        labels, valores = [], []
        for item in dados:
            valor = item[campo]
            labels.append(str(valor) if valor is not None else 'Não informado')
            valores.append(item['v'])
        return labels, valores
    except Exception:
        return [], []


DIAS_SEMANA = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']


def heatmap_semana_hora(qs, campo_datetime, campo_hora=None):
    try:
        resultado = defaultdict(int)
        for item in qs.only(campo_datetime, campo_hora if campo_hora else 'id').iterator():
            dt = getattr(item, campo_datetime, None)
            if not dt:
                continue
            if isinstance(dt, datetime):
                dia_semana = dt.weekday()
                hora = dt.hour
            elif isinstance(dt, date):
                dia_semana = dt.weekday()
                hora = 0
            else:
                continue
            if campo_hora:
                h = getattr(item, campo_hora, None)
                if h:
                    hora = h.hour
            resultado[(dia_semana, hora)] += 1

        linhas = []
        for (d, h), total in resultado.items():
            linhas.append({'dia_idx': d, 'dia': DIAS_SEMANA[d], 'hora': h, 'total': total})
        return linhas
    except Exception:
        return []


def agrupar_por_choice(qs, campo, choices):
    try:
        dados = dict(
            qs.values_list(campo)
            .annotate(v=Count('id'))
            .values_list(campo, 'v')
        )
        labels, valores = [], []
        for chave, label in choices:
            v = dados.get(chave, 0)
            if v > 0:
                labels.append(label)
                valores.append(v)
        return labels, valores
    except Exception:
        return [], []


def gerar_csv(labels, series_dict):
    import csv
    from io import StringIO

    buffer = StringIO()
    writer = csv.writer(buffer, delimiter=';')
    writer.writerow(['Label'] + list(series_dict.keys()))
    for i, label in enumerate(labels):
        linha = [label]
        for serie in series_dict.values():
            linha.append(serie[i] if i < len(serie) else '')
        writer.writerow(linha)
    return buffer.getvalue()
