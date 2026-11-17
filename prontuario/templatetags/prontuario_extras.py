
from django import template

register = template.Library()

@register.filter
def get_item(dicionario, chave):
    """Retorna dicionario[chave]. Uso: {{ dict|get_item:variavel }}"""
    try:
        return dicionario.get(chave, '')
    except (AttributeError, TypeError):
        return ''

@register.filter
def index(lista, i):
    """Retorna lista[i]. Uso: {{ lista|index:forloop.counter0 }}"""
    try:
        return lista[int(i)]
    except (IndexError, TypeError, ValueError):
        return ''
