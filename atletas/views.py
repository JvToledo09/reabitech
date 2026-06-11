from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from usuarios.models import Atleta

@login_required
def lista_atletas(request):
    atletas = Atleta.objects.all()
    return render(request, 'atletas/lista.html', {'atletas': atletas})