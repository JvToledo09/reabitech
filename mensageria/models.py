# ==============================================================================
# REABITECH — APP MENSAGERIA
# Models: Conversa, ParticipanteConversa, Mensagem
# Chat interno entre profissionais do projeto (atleta NÃO participa)
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ==============================================================================
# 1. CONVERSA (DM ou Grupo)
# ==============================================================================
class Conversa(models.Model):
    """
    Conversa entre 2+ membros do MESMO projeto.
    - tipo='dm'    → conversa direta (sempre 2 participantes)
    - tipo='grupo' → grupo (nome obrigatório, 2+ participantes)
    """
    TIPO_CHOICES = [
        ('dm', 'Conversa Direta'),
        ('grupo', 'Grupo'),
    ]

    # ----- Relacionamentos -----
    projeto = models.ForeignKey(
        'projetos.Projeto',
        on_delete=models.CASCADE,
        related_name='conversas',
        verbose_name='Projeto'
    )
    criada_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='conversas_criadas',
        verbose_name='Criada por'
    )

    # ----- Identificação -----
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default='dm',
        verbose_name='Tipo'
    )
    nome = models.CharField(
        max_length=150,
        blank=True,
        default='',
        help_text='Obrigatório apenas para grupos',
        verbose_name='Nome do Grupo'
    )

    # ----- Timestamps -----
    criada_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Criada em'
    )
    atualizada_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Última movimentação'
    )

    class Meta:
        ordering = ['-atualizada_em']
        verbose_name = 'Conversa'
        verbose_name_plural = 'Conversas'
        indexes = [
            models.Index(fields=['projeto', '-atualizada_em']),
        ]

    def __str__(self):
        if self.tipo == 'grupo':
            return f"Grupo: {self.nome or '(sem nome)'}"
        return f"DM #{self.id}"

    # ----- Métodos úteis -----
    def outro_participante(self, user):
        """Retorna o outro participante da DM (ou None se for grupo)."""
        if self.tipo != 'dm':
            return None
        return self.participantes.exclude(usuario=user).select_related('usuario').first()

    def titulo_para(self, user):
        """Título amigável exibido pra um usuário específico."""
        if self.tipo == 'grupo':
            return self.nome or 'Grupo sem nome'
        outro = self.outro_participante(user)
        if outro:
            return outro.usuario.get_full_name() or outro.usuario.username
        return 'Conversa'

    def total_nao_lidas_para(self, user):
        """Conta mensagens não lidas desta conversa para um usuário."""
        try:
            participante = self.participantes.get(usuario=user)
        except ParticipanteConversa.DoesNotExist:
            return 0

        return self.mensagens.filter(
            deletada=False,
            criada_em__gt=participante.ultima_leitura
        ).exclude(autor=user).count()

    def ultima_mensagem(self):
        """Retorna a última mensagem não deletada, ou None."""
        return self.mensagens.filter(deletada=False).order_by('-criada_em').first()


# ==============================================================================
# 2. PARTICIPANTE DE CONVERSA (M2M customizada)
# ==============================================================================
class ParticipanteConversa(models.Model):
    """
    Vincula um usuário a uma conversa.
    Guarda 'ultima_leitura' pra calcular mensagens não lidas.
    """
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name='participantes',
        verbose_name='Conversa'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participacoes_conversa',
        verbose_name='Usuário'
    )

    entrou_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Entrou em'
    )
    ultima_leitura = models.DateTimeField(
        default=timezone.now,
        verbose_name='Última leitura'
    )

    class Meta:
        unique_together = ['conversa', 'usuario']
        verbose_name = 'Participante de Conversa'
        verbose_name_plural = 'Participantes de Conversa'
        ordering = ['entrou_em']

    def __str__(self):
        return f"{self.usuario.username} em {self.conversa}"

    def marcar_como_lida(self):
        """Atualiza ultima_leitura pro agora."""
        self.ultima_leitura = timezone.now()
        self.save(update_fields=['ultima_leitura'])


# ==============================================================================
# 3. MENSAGEM
# ==============================================================================
class Mensagem(models.Model):
    """
    Mensagem enviada numa conversa.
    Suporta anexo (imagem/PDF) e soft-delete.
    """
    conversa = models.ForeignKey(
        Conversa,
        on_delete=models.CASCADE,
        related_name='mensagens',
        verbose_name='Conversa'
    )
    autor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='mensagens_enviadas',
        verbose_name='Autor'
    )

    conteudo = models.TextField(
        verbose_name='Conteúdo'
    )
    anexo = models.FileField(
        upload_to='mensageria/anexos/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Anexo',
        help_text='Imagem ou PDF (máx 10MB)'
    )

    criada_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Enviada em'
    )
    editada_em = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Editada em'
    )
    deletada = models.BooleanField(
        default=False,
        verbose_name='Deletada'
    )

    class Meta:
        ordering = ['criada_em']
        verbose_name = 'Mensagem'
        verbose_name_plural = 'Mensagens'
        indexes = [
            models.Index(fields=['conversa', 'criada_em']),
        ]

    def __str__(self):
        return f"Msg de {self.autor.username} em {self.conversa} ({self.criada_em:%d/%m %H:%M})"

    @property
    def tem_anexo(self):
        return bool(self.anexo)

    @property
    def is_imagem(self):
        if not self.anexo:
            return False
        nome = (self.anexo.name or '').lower()
        return nome.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))

    @property
    def is_pdf(self):
        if not self.anexo:
            return False
        return (self.anexo.name or '').lower().endswith('.pdf')
