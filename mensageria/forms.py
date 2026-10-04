# ==============================================================================
# REABITECH — FORMS DA MENSAGERIA
# ==============================================================================

from django import forms
from django.contrib.auth.models import User

from projetos.models import MembroProjeto
from .models import Conversa, Mensagem


# ==============================================================================
# FORM — Criar Conversa (DM ou Grupo)
# ==============================================================================
class NovaConversaForm(forms.Form):
    """
    Formulário para criar uma nova conversa.
    - tipo='dm'    → 1 destinatário obrigatório
    - tipo='grupo' → nome obrigatório + 2+ destinatários
    """
    tipo = forms.ChoiceField(
        choices=Conversa.TIPO_CHOICES,
        initial='dm',
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Tipo de conversa'
    )
    nome = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: Equipe do João'
        }),
        label='Nome do grupo (só para grupos)'
    )
    destinatarios = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        label='Participantes'
    )

    def __init__(self, *args, projeto=None, user_atual=None, **kwargs):
        super().__init__(*args, **kwargs)
        if projeto and user_atual:
            ids = MembroProjeto.objects.filter(
                projeto=projeto, ativo=True
            ).exclude(tipo='atleta').exclude(usuario=user_atual).values_list('usuario_id', flat=True)
            self.fields['destinatarios'].queryset = User.objects.filter(
                id__in=ids
            ).order_by('first_name', 'username')

    def clean(self):
        cleaned = super().clean()
        tipo = cleaned.get('tipo')
        nome = (cleaned.get('nome') or '').strip()
        dests = cleaned.get('destinatarios')

        if tipo == 'grupo' and not nome:
            self.add_error('nome', 'Nome do grupo é obrigatório.')

        if tipo == 'dm':
            if not dests or dests.count() != 1:
                self.add_error('destinatarios', 'Conversa direta precisa de exatamente 1 destinatário.')

        if tipo == 'grupo':
            if not dests or dests.count() < 2:
                self.add_error('destinatarios', 'Grupo precisa de pelo menos 2 participantes.')

        return cleaned


# ==============================================================================
# FORM — Enviar Mensagem
# ==============================================================================
class MensagemForm(forms.ModelForm):
    """Formulário de envio de mensagem com anexo opcional."""

    class Meta:
        model = Mensagem
        fields = ['conteudo', 'anexo']
        widgets = {
            'conteudo': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Escreva uma mensagem...',
                'style': 'resize: vertical; min-height: 44px;'
            }),
            'anexo': forms.ClearableFileInput(attrs={
                'class': 'form-control form-control-sm',
                'accept': 'image/*,application/pdf'
            }),
        }
        labels = {
            'conteudo': '',
            'anexo': 'Anexo',
        }

    def clean_anexo(self):
        anexo = self.cleaned_data.get('anexo')
        if anexo:
            # Limite de 10MB
            if anexo.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Anexo muito grande (máx 10MB).')
            nome = (anexo.name or '').lower()
            permitidos = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf')
            if not nome.endswith(permitidos):
                raise forms.ValidationError('Apenas imagens (JPG/PNG/GIF/WEBP) ou PDF.')
        return anexo

    def clean_conteudo(self):
        conteudo = (self.cleaned_data.get('conteudo') or '').strip()
        anexo = self.cleaned_data.get('anexo')
        # Permite enviar só anexo sem texto
        if not conteudo and not anexo:
            raise forms.ValidationError('Escreva algo ou anexe um arquivo.')
        return conteudo
