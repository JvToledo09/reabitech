from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps

def perfil_required(*tipos_permitidos):
    """
    Decorator que verifica se o usuário tem um dos perfis permitidos.
    Uso: @perfil_required('coordenador', 'tecnico')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            # Verifica se o usuário tem perfil
            if not hasattr(request.user, 'perfil'):
                messages.error(request, 'Perfil não definido.')
                return redirect('dashboard')
            if request.user.perfil.tipo not in tipos_permitidos:
                messages.error(request, 'Você não tem permissão para acessar esta página.')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator