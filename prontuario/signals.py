# ==============================================================================
# REABITECH — SIGNALS DO PRONTUÁRIO
# Notificações automáticas em eventos importantes
# ==============================================================================

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User

from usuarios.models import Notificacao, Alerta
from .models import (
    Prontuario, Medicamento, EscalaRisco,
    AvaliacaoCardiorrespiratoria, EncaminhamentoMedico, Exame
)


# ==============================================================================
# 1. Novo prontuário → avisa o coordenador
# ==============================================================================
@receiver(post_save, sender=Prontuario)
def notificar_novo_prontuario(sender, instance, created, **kwargs):
    if created:
        # Notifica o coordenador
        Notificacao.objects.create(
            usuario=instance.projeto.coordenador,
            titulo='Novo prontuário criado',
            mensagem=f'Prontuário {instance.numero_prontuario} criado para '
                     f'{instance.atleta.usuario.get_full_name()} por '
                     f'{instance.fisioterapeuta_responsavel.get_full_name() if instance.fisioterapeuta_responsavel else "—"}.',
            link=f'/prontuario/{instance.id}/'
        )
        # Notifica o atleta
        Notificacao.objects.create(
            usuario=instance.atleta.usuario,
            titulo='Prontuário aberto',
            mensagem=f'Seu prontuário clínico foi aberto. Nº {instance.numero_prontuario}.',
            link=f'/dashboard/atleta/'
        )


# ==============================================================================
# 2. Medicamento novo → avisa o coordenador
# ==============================================================================
@receiver(post_save, sender=Medicamento)
def notificar_medicamento(sender, instance, created, **kwargs):
    if created and instance.status == 'ativo':
        Notificacao.objects.create(
            usuario=instance.prontuario.projeto.coordenador,
            titulo='Novo medicamento registrado',
            mensagem=f'{instance.prontuario.atleta.usuario.get_full_name()} '
                     f'está tomando {instance.nome} {instance.dosagem}.',
            link=f'/prontuario/{instance.prontuario.id}/medicamentos/'
        )


# ==============================================================================
# 3. Escala de risco ALTO → gera alerta
# ==============================================================================
@receiver(post_save, sender=EscalaRisco)
def alerta_escala_risco_alto(sender, instance, created, **kwargs):
    if created and instance.nivel_risco in ['alto', 'critico']:
        Alerta.objects.create(
            atleta=instance.prontuario.atleta,
            tipo='dor_alta',
            mensagem=f'Escala {instance.get_tipo_display()} com nível '
                     f'{instance.get_nivel_risco_display()} '
                     f'({instance.pontuacao}/{instance.pontuacao_maxima}).',
        )
        # Notifica coordenador e fisio
        for user in [instance.prontuario.projeto.coordenador, instance.prontuario.fisioterapeuta_responsavel]:
            if user:
                Notificacao.objects.create(
                    usuario=user,
                    titulo=f'⚠️ Risco {instance.get_nivel_risco_display()}',
                    mensagem=f'Escala {instance.get_tipo_display()} aplicada em '
                             f'{instance.prontuario.atleta.usuario.get_full_name()}.',
                    link=f'/prontuario/{instance.prontuario.id}/escalas/'
                )


# ==============================================================================
# 4. Cardio com dispneia alta → alerta
# ==============================================================================
@receiver(post_save, sender=AvaliacaoCardiorrespiratoria)
def alerta_cardio_grave(sender, instance, created, **kwargs):
    if created and instance.frequencia_dispneia >= 3:
        Alerta.objects.create(
            atleta=instance.prontuario.atleta,
            tipo='dor_alta',
            mensagem=f'Avaliação cardiorrespiratória: dispneia {instance.frequencia_dispneia}/4. '
                     f'Verificar paciente.',
        )


# ==============================================================================
# 5. Encaminhamento urgente → notifica todos os profissionais
# ==============================================================================
@receiver(post_save, sender=EncaminhamentoMedico)
def notificar_encaminhamento_urgente(sender, instance, created, **kwargs):
    if created and instance.urgencia in ['urgente', 'prioritario']:
        Notificacao.objects.create(
            usuario=instance.prontuario.projeto.coordenador,
            titulo=f'🏥 Encaminhamento {instance.get_urgencia_display()}',
            mensagem=f'{instance.prontuario.atleta.usuario.get_full_name()} '
                     f'foi encaminhado para {instance.get_especialidade_display()}.',
            link=f'/prontuario/{instance.prontuario.id}/encaminhamentos/'
        )


# ==============================================================================
# 6. Exame com laudo disponível → notifica
# ==============================================================================
@receiver(post_save, sender=Exame)
def notificar_exame_laudo(sender, instance, created, **kwargs):
    if not created and instance.status == 'laudo_disponivel':
        Notificacao.objects.create(
            usuario=instance.prontuario.projeto.coordenador,
            titulo='Laudo de exame disponível',
            mensagem=f'{instance.prontuario.atleta.usuario.get_full_name()}: '
                     f'{instance.get_tipo_display()} — {instance.descricao[:60]}',
            link=f'/prontuario/{instance.prontuario.id}/exames/'
        )