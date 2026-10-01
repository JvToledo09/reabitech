# ==============================================================================
# REABITECH — APP PRONTUÁRIO
# Forms com validação
# ==============================================================================

from django import forms
from .models import (
    Prontuario, Triagem, Objetivo, Medicamento,
    AvaliacaoCIF, AvaliacaoCardiorrespiratoria,
    EscalaRisco, RelatorioDiario, EncaminhamentoMedico,
    Exame, EvolucaoFisioterapeutica
)


# ==============================================================================
# CSS BASE PARA TODOS OS CAMPOS
# ==============================================================================
BASE_INPUT_CLASS = 'form-control bg-light border-0 shadow-sm'
BASE_SELECT_CLASS = 'form-select bg-light border-0 shadow-sm'
BASE_TEXTAREA_CLASS = 'form-control bg-light border-0 shadow-sm'


def aplicar_css(fields):
    """Aplica classes CSS a todos os campos de um form."""
    for name, field in fields.items():
        widget = field.widget
        if isinstance(widget, forms.Select):
            widget.attrs.setdefault('class', BASE_SELECT_CLASS)
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault('class', BASE_TEXTAREA_CLASS)
            widget.attrs.setdefault('rows', 3)
        else:
            widget.attrs.setdefault('class', BASE_INPUT_CLASS)


# ==============================================================================
# 1. PRONTUÁRIO
# ==============================================================================
class ProntuarioForm(forms.ModelForm):
    class Meta:
        model = Prontuario
        fields = [
            'atleta', 'projeto', 'fisioterapeuta_responsavel',
            'estagiarios', 'status', 'data_alta'
        ]
        widgets = {
            'data_alta': forms.DateInput(attrs={'type': 'date'}),
            'estagiarios': forms.SelectMultiple(attrs={'size': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 2. TRIAGEM
# ==============================================================================
class TriagemForm(forms.ModelForm):
    class Meta:
        model = Triagem
        fields = [
            'queixa_principal', 'descricao_queixa',
            'historia_doenca_atual', 'historia_pregressa',
            'historico_familiar', 'medicamentos_uso',
            'alergias', 'cirurgias_anteriores',
            'pressao_arterial', 'frequencia_cardiaca',
            'frequencia_respiratoria', 'temperatura',
            'saturacao_o2', 'peso', 'altura',
            'inspecao', 'palpacao', 'ausculta',
            'observacoes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 3. OBJETIVO
# ==============================================================================
class ObjetivoForm(forms.ModelForm):
    class Meta:
        model = Objetivo
        fields = [
            'prazo', 'titulo', 'descricao', 'status',
            'percentual_alcancado', 'data_prevista', 'data_conclusao',
        ]
        widgets = {
            'data_prevista': forms.DateInput(attrs={'type': 'date'}),
            'data_conclusao': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 4. MEDICAMENTO
# ==============================================================================
class MedicamentoForm(forms.ModelForm):
    class Meta:
        model = Medicamento
        fields = [
            'nome', 'principio_ativo', 'dosagem', 'quantidade',
            'via', 'frequencia', 'horarios',
            'prescritor', 'crm_prescritor',
            'data_inicio', 'data_fim', 'status',
            'indicacao', 'efeitos_colaterais', 'observacoes',
        ]
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 5. AVALIAÇÃO CIF
# ==============================================================================
class AvaliacaoCIFForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoCIF
        fields = [
            # Funções do corpo
            'b1_funcoes_mentais', 'b2_funcoes_sensoriais',
            'b4_cardiorrespiratorias', 'b7_neuromusculoesqueleticas',
            'b8_pele',
            # Atividades
            'd1_aprendizagem', 'd2_tarefas_gerais', 'd3_comunicacao',
            'd4_mobilidade', 'd5_cuidado_pessoal', 'd6_vida_domestica',
            'd7_relacoes', 'd8_areas_principais',
            # Fatores ambientais
            'e1_produtos_tecnologia', 'e2_ambiente_natural',
            'e3_apoio_relacionamentos', 'e4_atitudes', 'e5_servicos_sistemas',
            # Perfil
            'perfil_funcionalidade', 'objetivos_cif',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 6. AVALIAÇÃO CARDIORRESPIRATÓRIA
# ==============================================================================
class AvaliacaoCardiorrespiratoriaForm(forms.ModelForm):
    class Meta:
        model = AvaliacaoCardiorrespiratoria
        fields = [
            'condicao_principal', 'outras_condicoes',
            'tempo_diagnostico', 'tabagismo', 'carga_tabagica',
            'frequencia_dispneia', 'tosse', 'tosse_produtiva',
            'sibilos', 'cianose', 'uso_musculos_acessorios',
            'limitacao_atividade',
            'teste_caminhada_6min', 'spo2_reouso', 'spo2_esforco',
            'fc_repouso', 'fc_maxima', 'pa_repouso', 'escala_borg',
            'espirometria', 'ecg', 'ecocardiograma', 'raio_x_torax',
            'plano_cardiorrespiratorio', 'observacoes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 7. ESCALA DE RISCO
# ==============================================================================
class EscalaRiscoForm(forms.ModelForm):
    class Meta:
        model = EscalaRisco
        fields = [
            'tipo', 'pontuacao', 'pontuacao_maxima',
            'nivel_risco', 'interpretacao', 'conduta_recomendada',
            'observacoes',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 8. RELATÓRIO DIÁRIO
# ==============================================================================
class RelatorioDiarioForm(forms.ModelForm):
    class Meta:
        model = RelatorioDiario
        fields = [
            'data_sessao', 'horario_inicio', 'horario_fim',
            'fisioterapeuta',
            'procedimentos', 'tecnicas_utilizadas',
            'dor_inicio', 'dor_fim', 'estado_geral', 'reacao_paciente',
            'pa_inicial', 'pa_final', 'fc_inicial', 'fc_final',
            'spo2_inicial', 'spo2_final',
            'plano_proxima_sessao', 'orientacoes_paciente', 'observacoes',
        ]
        widgets = {
            'data_sessao': forms.DateInput(attrs={'type': 'date'}),
            'horario_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'horario_fim': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 9. ENCAMINHAMENTO MÉDICO
# ==============================================================================
class EncaminhamentoMedicoForm(forms.ModelForm):
    class Meta:
        model = EncaminhamentoMedico
        fields = [
            'especialidade', 'medico_encaminhado', 'urgencia',
            'motivo', 'resumo_clinico', 'exames_realizados',
            'hipotese_diagnostica', 'questionamentos',
            'status', 'data_retorno', 'parecer_medico', 'conduta_sugerida',
        ]
        widgets = {
            'data_retorno': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 10. EXAME
# ==============================================================================
class ExameForm(forms.ModelForm):
    class Meta:
        model = Exame
        fields = [
            'tipo', 'descricao',
            'data_realizacao', 'local_realizacao',
            'status', 'laudo', 'conclusao', 'arquivo',
        ]
        widgets = {
            'data_realizacao': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)


# ==============================================================================
# 11. EVOLUÇÃO FISIOTERAPÊUTICA
# ==============================================================================
class EvolucaoFisioterapeuticaForm(forms.ModelForm):
    class Meta:
        model = EvolucaoFisioterapeutica
        fields = [
            'tipo', 'fisioterapeuta',
            'subjetivo', 'objetivo', 'avaliacao', 'plano',
            'escala_dor', 'forca_muscular', 'amplitude_movimento',
            'testes_especiais', 'conduta', 'resposta_ao_tratamento',
            'paciente_estavel', 'necessita_encaminhamento',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        aplicar_css(self.fields)