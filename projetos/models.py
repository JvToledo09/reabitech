from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid


# ==============================================
# PLANO (Free / Pro / Enterprise)
# ==============================================
class Plano(models.Model):
    TIPO_CHOICES = [
        ('free', 'Gratuito'),
        ('pro', 'Profissional'),
        ('enterprise', 'Empresarial'),
    ]

    # 🔥 NÃO usar unique=True aqui (evita conflito de migração)
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='free'
    )
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, default='')
    preco_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )
    max_usuarios = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text='Número máximo de membros no projeto'
    )
    max_projetos = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Quantos projetos o coordenador pode ter'
    )
    modulos_inclusos = models.JSONField(
        default=list,
        help_text="Lista de módulos: ['fisioterapia', 'psicologia', 'tecnico', 'nutricao']"
    )
    destaque = models.BooleanField(
        default=False,
        help_text='Destacar na landing page'
    )
    ordem = models.IntegerField(
        default=0,
        help_text='Ordem de exibição (menor número primeiro)'
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['ordem', 'preco_mensal']
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        return f"{self.nome} (R$ {self.preco_mensal}/mês)"

    @property
    def modulos_display(self):
        """Retorna os módulos em texto legível."""
        mapa = dict(Projeto.MODULOS_CHOICES)
        return [mapa.get(m, m) for m in (self.modulos_inclusos or [])]


# ==============================================
# PROJETO (Clínica, Time, Escola, etc.)
# ==============================================
class Projeto(models.Model):
    TIPO_CHOICES = [
        ('escola', 'Escola / Instituição de Ensino'),
        ('clinica', 'Clínica de Reabilitação'),
        ('time', 'Time / Clube Esportivo'),
        ('academia', 'Academia'),
        ('projeto_social', 'Projeto Social'),
        ('outro', 'Outro'),
    ]

    MODULOS_CHOICES = [
        ('fisioterapia', 'Fisioterapia'),
        ('psicologia', 'Psicologia Esportiva'),
        ('tecnico', 'Análise Técnica'),
        ('nutricao', 'Nutrição'),
    ]

    # ----- Identificação -----
    nome = models.CharField(max_length=150)
    slug = models.SlugField(
        max_length=160,
        unique=True,
        blank=True,
        default=''
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='outro'
    )
    descricao = models.TextField(blank=True, default='')
    logo = models.ImageField(
        upload_to='projetos/logos/',
        blank=True,
        null=True
    )

    # ----- Relacionamentos -----
    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name='projetos',
        null=True,
        blank=True
    )
    coordenador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='projetos_coordenados'
    )

    # ----- Configurações -----
    modulos_ativos = models.JSONField(
        default=list,
        help_text="Módulos ativos neste projeto"
    )
    publico = models.BooleanField(
        default=False,
        help_text='Aparecer na landing pública'
    )
    ativo = models.BooleanField(default=True)

    # ----- Timestamps -----
    criado_em = models.DateTimeField(auto_now_add=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Projeto'
        verbose_name_plural = 'Projetos'

    def save(self, *args, **kwargs):
        # Gera slug automaticamente se não foi passado
        if not self.slug:
            base = uuid.uuid4().hex[:8]
            nome_slug = (
                self.nome.lower()
                .replace(' ', '-')
                .replace('ç', 'c')
                .replace('ã', 'a')
                .replace('á', 'a')
                .replace('é', 'e')
                .replace('í', 'i')
                .replace('ó', 'o')
                .replace('ú', 'u')
            )[:50]
            self.slug = f"{nome_slug}-{base}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    def tem_modulo(self, modulo):
        """Verifica se o projeto tem um módulo ativo."""
        return modulo in (self.modulos_ativos or [])

    @property
    def total_membros(self):
        return self.membros.filter(ativo=True).count()

    @property
    def total_atletas(self):
        return self.membros.filter(ativo=True, tipo='atleta').count()

    @property
    def total_profissionais(self):
        return self.membros.filter(
            ativo=True
        ).exclude(tipo='atleta').count()


# ==============================================
# MEMBRO DO PROJETO
# ==============================================
class MembroProjeto(models.Model):
    TIPO_MEMBRO = [
        ('coordenador', 'Coordenador'),
        ('fisioterapeuta', 'Fisioterapeuta'),
        ('psicologo', 'Psicólogo'),
        ('tecnico', 'Técnico'),
        ('nutricionista', 'Nutricionista'),
        ('atleta', 'Atleta'),
    ]

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]

    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='membros'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='membros_projeto'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_MEMBRO,
        default='atleta'
    )
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        blank=True,
        default=''
    )
    modalidade = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )
    ativo = models.BooleanField(default=True)
    entrou_em = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        unique_together = ['projeto', 'usuario']
        verbose_name = 'Membro do Projeto'
        verbose_name_plural = 'Membros do Projeto'
        ordering = ['-entrou_em']

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} em {self.projeto.nome}"


# ==============================================
# CONVITE
# ==============================================
class ConviteProjeto(models.Model):
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='convites'
    )
    email = models.EmailField()
    tipo_membro = models.CharField(
        max_length=20,
        choices=MembroProjeto.TIPO_MEMBRO,
        default='atleta'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        default=''
    )
    criado_em = models.DateTimeField(auto_now_add=True, null=True)
    expiracao = models.DateTimeField(blank=True, null=True)
    aceito = models.BooleanField(default=False)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Convite de Projeto'
        verbose_name_plural = 'Convites de Projeto'

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = uuid.uuid4().hex
        if not self.expiracao:
            self.expiracao = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Convite para {self.email} - {self.projeto.nome}"

    @property
    def expirado(self):
        """Retorna True se o convite já expirou."""
        if not self.expiracao:
            return False
        return timezone.now() > self.expiracao

    @property
    def valido(self):
        """Retorna True se o convite ainda é válido."""
        return not self.aceito and not self.expirado