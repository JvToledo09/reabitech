from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def painel_principal(request):
    return render(request, 'painel/index.html')