# ==============================================================================
# REABITECH — APP USUARIOS
# Decorators customizados
# ==============================================================================

from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps


def perfil_required(*tipos_permitidos):
    """
    Decorator que verifica se o usuário tem um dos perfis permitidos.
    
    Uso:
        @perfil_required('coordenador')
        @perfil_required('coordenador', 'tecnico')
    
    Se o usuário não tiver perfil, redireciona para o dashboard.
    Se não tiver permissão, mostra mensagem e redireciona.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verifica se está logado
            if not request.user.is_authenticated:
                return redirect('login')

            # Verifica se tem perfil
            if not hasattr(request.user, 'perfil'):
                messages.error(request, 'Perfil não definido. Contate o administrador.')
                return redirect('dashboard:dashboard')

            # Verifica permissão
            if request.user.perfil.tipo not in tipos_permitidos:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('dashboard:dashboard')

            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator