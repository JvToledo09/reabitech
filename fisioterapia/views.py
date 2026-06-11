from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Lesao, EvolucaoFisica
from usuarios.models import Atleta

@login_required
def lista_lesoes(request):
    lesoes = Lesao.objects.all()
    return render(request, 'fisioterapia/lesoes.html', {'lesoes': lesoes})