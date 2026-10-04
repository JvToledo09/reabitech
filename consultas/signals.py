from django.db.models.signals import post_save
from django.dispatch import receiver

from usuarios.models import Notificacao
from .models import Consulta


@receiver(post_save, sender=Consulta)
def consulta_criada_notificar(sender, instance, created, **kwargs):
    """Notifica o atleta quando uma consulta é criada."""
    if not created:
        return
    try:
        Notificacao.objects.create(
            usuario=instance.atleta.usuario,
            titulo='Nova consulta agendada',
            mensagem=(
                f"Você tem uma {instance.get_tipo_display()} agendada para "
                f"{instance.data.strftime('%d/%m/%Y')} às {instance.hora_inicio.strftime('%H:%M')}."
            ),
            link=f'/consultas/{instance.id}/',
        )
    except Exception:
        # Nunca deixa o signal quebrar o save
        pass