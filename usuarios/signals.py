# ==============================================================================
# REABITECH — SIGNALS DE AUDITORIA
# Registra automaticamente ações importantes no banco
# ==============================================================================

import threading
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Auditoria


# ==============================================================================
# THREAD-LOCAL — Usuário atual (para uso em signals automáticos)
# ==============================================================================
_thread_locals = threading.local()


def get_current_user():
    """Retorna o usuário logado na requisição atual (thread-local)."""
    return getattr(_thread_locals, 'user', None)


def set_current_user(user):
    """Define o usuário atual no thread-local."""
    _thread_locals.user = user


# ==============================================================================
# LOGIN / LOGOUT
# ==============================================================================
@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    """Registra login."""
    ip = getattr(request, 'auditoria_ip', None)
    user_agent = getattr(request, 'auditoria_user_agent', '')

    Auditoria.objects.create(
        usuario=user,
        acao='login',
        descricao=f'{user.get_full_name() or user.username} fez login no sistema.',
        ip=ip,
        user_agent=user_agent,
    )


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    """Registra logout."""
    if not user:
        return

    ip = getattr(request, 'auditoria_ip', None)
    user_agent = getattr(request, 'auditoria_user_agent', '')

    Auditoria.objects.create(
        usuario=user,
        acao='logout',
        descricao=f'{user.get_full_name() or user.username} saiu do sistema.',
        ip=ip,
        user_agent=user_agent,
    )


# ==============================================================================
# AUDITORIA AUTOMÁTICA DE MODELS
# ==============================================================================
# Modelos monitorados: cada save/delete registra uma entrada em Auditoria.
# Para adicionar um novo, basta acrescentar à tupla MODELOS_MONITORADOS.
# ==============================================================================
def criar_auditoria_modelo(sender, instance, acao, **kwargs):
    """
    Helper para criar auditoria de models.
    Chamado automaticamente por signals conectados no final deste arquivo.
    """
    try:
        model_name = sender.__name__
        objeto_repr = str(instance)[:300]

        # Tenta descobrir o usuário logado no thread-local
        usuario = get_current_user()

        # Fallback: campos comuns que apontam para um usuário
        if not usuario:
            usuario = (
                getattr(instance, 'criado_por', None) or
                getattr(instance, 'registrado_por', None) or
                getattr(instance, 'avaliador', None) or
                getattr(instance, 'fisioterapeuta', None) or
                getattr(instance, 'solicitado_por', None)
            )

        descricao = f'{acao.capitalize()}: {model_name} #{instance.pk}'

        Auditoria.objects.create(
            usuario=usuario,
            acao=acao,
            modelo=model_name,
            objeto_id=instance.pk,
            objeto_repr=objeto_repr,
            descricao=descricao,
        )
    except Exception:
        pass  # Nunca deixa a auditoria quebrar o fluxo principal


def conectar_signals_automaticos():
    """
    Conecta post_save/post_delete dos models monitorados.
    Executado no ready() do app (via apps.py).
    """
    try:
        from projetos.models import Projeto, MembroProjeto
        from prontuario.models import Prontuario, Triagem, Objetivo

        MODELOS = [
            Projeto, MembroProjeto,
            Prontuario, Triagem, Objetivo,
        ]

        for modelo in MODELOS:
            post_save.connect(
                lambda sender, instance, created, **kw: criar_auditoria_modelo(
                    sender, instance, 'criar' if created else 'editar', **kw
                ),
                sender=modelo,
                dispatch_uid=f'auditoria_save_{modelo.__name__}',
            )
            post_delete.connect(
                lambda sender, instance, **kw: criar_auditoria_modelo(
                    sender, instance, 'deletar', **kw
                ),
                sender=modelo,
                dispatch_uid=f'auditoria_delete_{modelo.__name__}',
            )
    except Exception:
        pass  # Não quebra se algum modelo ainda não existir


# ==============================================================================
# DECORATOR PARA REGISTRAR MANUALMENTE
# ==============================================================================
def auditar(acao, modelo='', descricao=''):
    """
    Decorator para registrar ações em views.

    Uso:
        @auditar('criar', 'Atleta', 'Criou novo atleta')
        def minha_view(request):
            ...
    """
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            response = view_func(request, *args, **kwargs)

            from .middleware import registrar_auditoria
            registrar_auditoria(
                request,
                acao=acao,
                modelo=modelo,
                descricao=descricao or f'Ação: {acao}',
            )

            return response
        return wrapper
    return decorator