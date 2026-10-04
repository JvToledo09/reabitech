# ==============================================================================
# REABITECH — APP CONSULTAS
# Agenda de consultas / sessões de reabilitação
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, date

from usuarios.models import Atleta
from projetos.models import Projeto


class Consulta(models.Model):
    """
    Agendamento de consulta/sessão para um atleta.
    Pode ser avaliação, sessão de fisioterapia, sessão de psicologia,
    retorno, reavaliação ou alta.
    """

    TIPO_CHOICES = [
        ('avaliacao_inicial', 'Avaliação Inicial'),
        ('fisioterapia', 'Sessão de Fisioterapia'),
        ('psicologia', 'Sessão de Psicologia'),
        ('retorno', 'Retorno'),
        ('reavaliacao', 'Reavaliação'),
        ('alta', 'Alta'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('agendada', 'Agendada'),
        ('confirmada', 'Confirmada'),
        ('realizada', 'Realizada'),
        ('cancelada', 'Cancelada'),
        ('faltou', 'Faltou'),
        ('remarcada', 'Remarcada'),
    ]

    PRIORIDADE_CHOICES = [
        ('baixa', 'Baixa'),
        ('normal', 'Normal'),
        ('alta', 'Alta'),
        ('urgente', 'Urgente'),
    ]

    MODALIDADE_CHOICES = [
        ('presencial', 'Presencial'),
        ('online', 'Online'),
        ('domiciliar', 'Domiciliar'),
    ]

    # ----- Relacionamentos -----
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='consultas',
        verbose_name='Projeto'
    )
    atleta = models.ForeignKey(
        Atleta,
        on_delete=models.CASCADE,
        related_name='consultas',
        verbose_name='Atleta / Paciente'
    )
    profissional = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas_como_profissional',
        verbose_name='Profissional Responsável'
    )
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='consultas_criadas',
        verbose_name='Criado por'
    )

    # ----- Tipo / status -----
    tipo = models.CharField(
        max_length=25,
        choices=TIPO_CHOICES,
        default='fisioterapia',
        verbose_name='Tipo de Consulta'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='agendada',
        verbose_name='Status'
    )
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default='normal',
        verbose_name='Prioridade'
    )
    modalidade = models.CharField(
        max_length=20,
        choices=MODALIDADE_CHOICES,
        default='presencial',
        verbose_name='Modalidade'
    )

    # ----- Data e hora -----
    data = models.DateField(
        verbose_name='Data',
        help_text='Data da consulta'
    )
    hora_inicio = models.TimeField(
        verbose_name='Horário de Início'
    )
    hora_fim = models.TimeField(
        verbose_name='Horário de Término'
    )

    # ----- Local -----
    local = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Local',
        help_text='Ex: Sala 2, Clínica Central, Link Meet'
    )

    # ----- Conteúdo -----
    motivo = models.TextField(
        blank=True,
        verbose_name='Motivo / Objetivo',
        help_text='Motivo da consulta (opcional)'
    )
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    motivo_cancelamento = models.TextField(
        blank=True,
        verbose_name='Motivo do Cancelamento'
    )

    # ----- Reagendamento -----
    consulta_original = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='remarcacoes',
        verbose_name='Consulta Original',
        help_text='Preenchido quando esta consulta é uma remarcação'
    )

    # ----- Lembretes -----
    lembrete_enviado = models.BooleanField(
        default=False,
        verbose_name='Lembrete Enviado'
    )

    # ----- Timestamps -----
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    realizada_em = models.DateTimeField(null=True, blank=True)
    cancelada_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['data', 'hora_inicio']
        verbose_name = 'Consulta'
        verbose_name_plural = 'Consultas'
        indexes = [
            models.Index(fields=['projeto', 'data']),
            models.Index(fields=['atleta', 'data']),
            models.Index(fields=['profissional', 'data']),
            models.Index(fields=['status', 'data']),
        ]

    def __str__(self):
        nome = self.atleta.usuario.get_full_name() or self.atleta.usuario.username
        return f"{self.get_tipo_display()} — {nome} ({self.data.strftime('%d/%m/%Y')} {self.hora_inicio.strftime('%H:%M')})"

    # ----- Properties -----
    @property
    def duracao_minutos(self):
        """Duração da consulta em minutos."""
        if not (self.hora_inicio and self.hora_fim):
            return 0
        inicio = datetime.combine(date.today(), self.hora_inicio)
        fim = datetime.combine(date.today(), self.hora_fim)
        delta = fim - inicio
        return max(0, int(delta.total_seconds() / 60))

    @property
    def is_hoje(self):
        return self.data == timezone.localdate()

    @property
    def pode_editar(self):
        """Só é possível editar consultas ainda em aberto."""
        return self.status in ('agendada', 'confirmada', 'remarcada')

    @property
    def cor_status(self):
        """Cor Bootstrap do status (usado em badges)."""
        return {
            'agendada': 'info',
            'confirmada': 'primary',
            'realizada': 'success',
            'cancelada': 'danger',
            'faltou': 'warning',
            'remarcada': 'secondary',
        }.get(self.status, 'secondary')

    @property
    def cor_prioridade(self):
        return {
            'baixa': 'secondary',
            'normal': 'info',
            'alta': 'warning',
            'urgente': 'danger',
        }.get(self.prioridade, 'secondary')

    @property
    def icone_tipo(self):
        return {
            'avaliacao_inicial': 'fa-clipboard-check',
            'fisioterapia': 'fa-dumbbell',
            'psicologia': 'fa-brain',
            'retorno': 'fa-rotate-right',
            'reavaliacao': 'fa-magnifying-glass-chart',
            'alta': 'fa-flag-checkered',
            'outro': 'fa-calendar-day',
        }.get(self.tipo, 'fa-calendar-day')

    # ----- Ações de status -----
    def confirmar(self, por_usuario=None):
        self.status = 'confirmada'
        self.save(update_fields=['status', 'atualizado_em'])

    def marcar_realizada(self, por_usuario=None):
        self.status = 'realizada'
        self.realizada_em = timezone.now()
        self.save(update_fields=['status', 'realizada_em', 'atualizado_em'])

    def marcar_falta(self, por_usuario=None):
        self.status = 'faltou'
        self.save(update_fields=['status', 'atualizado_em'])

    def cancelar(self, motivo=''):
        self.status = 'cancelada'
        self.cancelada_em = timezone.now()
        if motivo:
            self.motivo_cancelamento = motivo
        self.save(update_fields=['status', 'cancelada_em', 'motivo_cancelamento', 'atualizado_em'])