from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import AvaliacaoPsicologica

@login_required
def lista_avaliacoes(request):
    avaliacoes = AvaliacaoPsicologica.objects.all()
    return render(request, 'psicologia/avaliacoes.html', {'avaliacoes': avaliacoes})