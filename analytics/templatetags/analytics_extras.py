# ==============================================================================
# REABITECH — TEMPLATE TAGS DO ANALYTICS
# ==============================================================================

from django import template

register = template.Library()


@register.filter
def index(lista, i):
    """Retorna lista[i]. Uso: {{ lista|index:forloop.counter0 }}"""
    try:
        return lista[int(i)]
    except (IndexError, TypeError, ValueError):
        return ''


@register.filter
def pct(valor, casas=1):
    try:
        return f"{float(valor):.{int(casas)}f}%"
    except (TypeError, ValueError):
        return '0%'


@register.filter
def sub(a, b):
    try:
        return float(a) - float(b)
    except (TypeError, ValueError):
        return 0
