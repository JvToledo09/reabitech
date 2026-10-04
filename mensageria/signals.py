# ==============================================================================
# REABITECH — SIGNALS DA MENSAGERIA
# Notifica participantes quando uma nova mensagem é enviada
# ==============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Notificacao
from .models import Mensagem


@receiver(post_save, sender=Mensagem)
def mensagem_criada_notificar(sender, instance, created, **kwargs):
    """Ao criar uma Mensagem, notifica todos os participantes (exceto o autor)."""
    if not created:
        return
    try:
        conversa = instance.conversa
        autor_nome = instance.autor.get_full_name() or instance.autor.username

        # Título amigável para cada destinatário
        for p in conversa.participantes.exclude(usuario=instance.autor).select_related('usuario'):
            if conversa.tipo == 'grupo':
                titulo_notif = f"Nova mensagem no grupo {conversa.nome or '(sem nome)'}"
            else:
                titulo_notif = f"Nova mensagem de {autor_nome}"

            Notificacao.objects.create(
                usuario=p.usuario,
                titulo=titulo_notif,
                mensagem=f"{autor_nome}: {instance.conteudo[:90]}" if instance.conteudo else f"{autor_nome} enviou um anexo.",
                link=f'/mensageria/conversa/{conversa.id}/',
            )
    except Exception:
        # Nunca deixa o signal quebrar o save
        pass
