from django.shortcuts import render, redirect
from .models import Atleta

def lista_atletas(request):
    atletas = Atleta.objects.all()

    return render(request, 'atletas/lista.html', {
        'atletas': atletas
    })

def novo_atleta(request):

    if request.method == 'POST':

        nome = request.POST.get('nome')
        idade = request.POST.get('idade')
        esporte = request.POST.get('esporte')
        lesao = request.POST.get('lesao')

        Atleta.objects.create(
            nome=nome,
            idade=idade,
            esporte=esporte,
            lesao=lesao
        )

        return redirect('/atletas/')

    return render(request, 'atletas/form.html')