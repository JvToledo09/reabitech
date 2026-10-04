# ==============================================================================
# REABITECH — ADMIN DA MENSAGERIA
# ==============================================================================

from django.contrib import admin
from .models import Conversa, ParticipanteConversa, Mensagem


class ParticipanteInline(admin.TabularInline):
    model = ParticipanteConversa
    extra = 0
    autocomplete_fields = ['usuario']


@admin.register(Conversa)
class ConversaAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo', 'nome', 'projeto', 'criada_por', 'atualizada_em')
    list_filter = ('tipo', 'projeto')
    search_fields = ('nome', 'projeto__nome')
    inlines = [ParticipanteInline]
    readonly_fields = ('criada_em', 'atualizada_em')


@admin.register(Mensagem)
class MensagemAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversa', 'autor', 'criada_em', 'deletada', 'tem_anexo')
    list_filter = ('deletada', 'criada_em')
    search_fields = ('conteudo', 'autor__username')
    readonly_fields = ('criada_em',)

    def tem_anexo(self, obj):
        return bool(obj.anexo)
    tem_anexo.boolean = True
    tem_anexo.short_description = 'Anexo?'


@admin.register(ParticipanteConversa)
class ParticipanteConversaAdmin(admin.ModelAdmin):
    list_display = ('conversa', 'usuario', 'entrou_em', 'ultima_leitura')
    list_filter = ('entrou_em',)
    search_fields = ('usuario__username', 'usuario__email')
