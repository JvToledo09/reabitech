from django.contrib import admin
from .models import (
    Prontuario, Triagem, Objetivo, Medicamento,
    AvaliacaoCIF, AvaliacaoCardiorrespiratoria,
    EscalaRisco, RelatorioDiario, EncaminhamentoMedico,
    Exame, EvolucaoFisioterapeutica
)


@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    list_display = ('numero_prontuario', 'atleta', 'status', 'data_abertura', 'data_arquivamento_previsto')
    list_filter = ('status', 'projeto')
    search_fields = ('numero_prontuario', 'atleta__usuario__first_name', 'atleta__usuario__last_name')
    readonly_fields = ('numero_prontuario', 'criado_em', 'atualizado_em')
    date_hierarchy = 'data_abertura'


@admin.register(Triagem)
class TriagemAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'queixa_principal', 'data_triagem')
    list_filter = ('queixa_principal',)
    search_fields = ('prontuario__atleta__usuario__first_name',)


@admin.register(Objetivo)
class ObjetivoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'prontuario', 'prazo', 'status', 'percentual_alcancado')
    list_filter = ('prazo', 'status')
    search_fields = ('titulo', 'prontuario__atleta__usuario__first_name')


@admin.register(Medicamento)
class MedicamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'dosagem', 'frequencia', 'via', 'status', 'prontuario')
    list_filter = ('status', 'via')
    search_fields = ('nome', 'principio_ativo')


@admin.register(AvaliacaoCIF)
class AvaliacaoCIFAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'data_avaliacao', 'pontuacao_global', 'classificacao_global')
    list_filter = ('classificacao_global',)
    readonly_fields = ('pontuacao_funcoes_corpo', 'pontuacao_atividades',
                       'pontuacao_fatores_ambientais', 'pontuacao_global',
                       'classificacao_global')


@admin.register(AvaliacaoCardiorrespiratoria)
class AvaliacaoCardiorrespiratoriaAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'condicao_principal', 'data_avaliacao', 'avaliador')
    list_filter = ('condicao_principal', 'tabagismo')


@admin.register(EscalaRisco)
class EscalaRiscoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'prontuario', 'pontuacao', 'nivel_risco', 'data_aplicacao')
    list_filter = ('tipo', 'nivel_risco')


@admin.register(RelatorioDiario)
class RelatorioDiarioAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'data_sessao', 'fisioterapeuta', 'dor_inicio', 'dor_fim')
    list_filter = ('data_sessao', 'fisioterapeuta')
    date_hierarchy = 'data_sessao'


@admin.register(EncaminhamentoMedico)
class EncaminhamentoMedicoAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'especialidade', 'urgencia', 'status', 'data_encaminhamento')
    list_filter = ('especialidade', 'urgencia', 'status')


@admin.register(Exame)
class ExameAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'tipo', 'descricao', 'status', 'data_solicitacao')
    list_filter = ('tipo', 'status')


@admin.register(EvolucaoFisioterapeutica)
class EvolucaoFisioterapeuticaAdmin(admin.ModelAdmin):
    list_display = ('prontuario', 'tipo', 'data', 'fisioterapeuta', 'escala_dor')
    list_filter = ('tipo', 'paciente_estavel', 'necessita_encaminhamento')
    date_hierarchy = 'data'