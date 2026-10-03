from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


@login_required
def painel_principal(request):
    """Painel principal — redireciona para o dashboard do perfil ativo."""
    if hasattr(request.user, 'perfil'):
        tipo = request.user.perfil.tipo
        if tipo == 'coordenador':
            return redirect('dashboard:dashboard_coordenador')
        elif tipo == 'tecnico':
            return redirect('dashboard:dashboard_tecnico')
        elif tipo == 'fisioterapeuta':
            return redirect('dashboard:dashboard_fisioterapeuta')
        elif tipo == 'psicologo':
            return redirect('dashboard:dashboard_psicologo')
        elif tipo == 'atleta':
            return redirect('dashboard:dashboard_atleta')
    return redirect('landing')