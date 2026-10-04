from django import forms
from django.utils import timezone

from usuarios.models import Atleta
from .models import Consulta


class ConsultaForm(forms.ModelForm):
    """Formulario de criacao/edicao de consulta com validacao de conflito."""

    class Meta:
        model = Consulta
        fields = [
            'atleta', 'profissional', 'tipo', 'prioridade', 'modalidade',
            'data', 'hora_inicio', 'hora_fim', 'local',
            'motivo', 'observacoes',
        ]
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fim': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'atleta': forms.Select(attrs={'class': 'form-select'}),
            'profissional': forms.Select(attrs={'class': 'form-select'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'prioridade': forms.Select(attrs={'class': 'form-select'}),
            'modalidade': forms.Select(attrs={'class': 'form-select'}),
            'local': forms.TextInput(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        labels = {
            'atleta': 'Atleta / Paciente',
            'profissional': 'Profissional Responsavel',
        }

    def __init__(self, *args, projeto=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.projeto = projeto

        if projeto:
            self.fields['atleta'].queryset = Atleta.objects.filter(
                usuario__membros_projeto__projeto=projeto,
                usuario__membros_projeto__ativo=True,
                usuario__membros_projeto__tipo='atleta',
            ).distinct()

            self.fields['profissional'].queryset = self.fields['profissional'].queryset.filter(
                membros_projeto__projeto=projeto,
                membros_projeto__ativo=True,
                membros_projeto__tipo__in=['fisioterapeuta', 'psicologo', 'coordenador'],
            ).distinct()

    def clean(self):
        cleaned = super().clean()
        data = cleaned.get('data')
        hi = cleaned.get('hora_inicio')
        hf = cleaned.get('hora_fim')
        atleta = cleaned.get('atleta')
        profissional = cleaned.get('profissional')

        if hi and hf and hi >= hf:
            raise forms.ValidationError('O horario de termino deve ser posterior ao de inicio.')

        if data and data < timezone.localdate():
            raise forms.ValidationError('Nao e possivel agendar consultas em datas passadas.')

        if data and hi and hf and profissional:
            conflito = Consulta.objects.filter(
                profissional=profissional,
                data=data,
                status__in=['agendada', 'confirmada', 'remarcada'],
            ).exclude(pk=self.instance.pk if self.instance else None)

            for c in conflito:
                if not (hf <= c.hora_inicio or hi >= c.hora_fim):
                    raise forms.ValidationError(
                        f'Conflito: o profissional ja tem consulta das {c.hora_inicio.strftime("%H:%M")} '
                        f'as {c.hora_fim.strftime("%H:%M")}.'
                    )

        if data and hi and hf and atleta:
            conflito = Consulta.objects.filter(
                atleta=atleta,
                data=data,
                status__in=['agendada', 'confirmada', 'remarcada'],
            ).exclude(pk=self.instance.pk if self.instance else None)

            for c in conflito:
                if not (hf <= c.hora_inicio or hi >= c.hora_fim):
                    raise forms.ValidationError(
                        f'Conflito: o atleta ja tem consulta das {c.hora_inicio.strftime("%H:%M")} '
                        f'as {c.hora_fim.strftime("%H:%M")}.'
                    )

        return cleaned


class CancelamentoForm(forms.Form):
    motivo = forms.CharField(
        label='Motivo do cancelamento',
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opcional'}),
        required=False,
    )
