from django import forms
from .models import Atleta

class AtletaForm(forms.ModelForm):

    class Meta:
        model = Atleta

        fields = [
            'nome',
            'idade',
            'esporte',
            'lesao',
            'altura',
            'peso',
            'status',
            'observacoes',
            'foto'
        ]

        widgets = {

            'nome': forms.TextInput(attrs={
                'placeholder':'Nome do atleta'
            }),

            'idade': forms.NumberInput(attrs={
                'placeholder':'Idade'
            }),

            'esporte': forms.TextInput(attrs={
                'placeholder':'Esporte'
            }),

            'lesao': forms.TextInput(attrs={
                'placeholder':'Lesão'
            }),

            'altura': forms.NumberInput(attrs={
                'placeholder':'Altura'
            }),

            'peso': forms.NumberInput(attrs={
                'placeholder':'Peso'
            }),

            'observacoes': forms.Textarea(attrs={
                'placeholder':'Observações clínicas'
            }),

        }