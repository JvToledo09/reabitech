from django import forms
from .models import Atleta

class AtletaForm(forms.ModelForm):
    class Meta:
        model = Atleta
        fields = '__all__'