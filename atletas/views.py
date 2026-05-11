from django.shortcuts import render, redirect, get_object_or_404

from .models import Atleta
from .forms import AtletaForm


def lista_atletas(request):

    atletas = Atleta.objects.all().order_by('-id')

    return render(
        request,
        'atletas/lista.html',
        {'atletas': atletas}
    )


def novo_atleta(request):

    if request.method == 'POST':

        form = AtletaForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            form.save()

            return redirect('/atletas/')

    else:

        form = AtletaForm()

    return render(
        request,
        'atletas/form.html',
        {'form': form}
    )


def detalhes_atleta(request, id):

    atleta = get_object_or_404(
        Atleta,
        id=id
    )

    return render(
        request,
        'atletas/detalhes.html',
        {'atleta': atleta}
    )