# ==============================================================================
# REABITECH — APP PROJETOS
# Models: Plano, Projeto, MembroProjeto, ConviteProjeto
# Plataforma SaaS multi-tenant para reabilitação
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from datetime import timedelta
import uuid


# ==============================================================================
# 1. PLANO (Trial, Profissional, Empresarial)
# ==============================================================================
class Plano(models.Model):
    """
    Plano de assinatura SaaS.
    Define limite de usuários, projetos e módulos disponíveis.
    """
    TIPO_CHOICES = [
        ('trial', 'Trial Grátis (30 dias)'),
        ('profissional', 'Profissional'),
        ('empresarial', 'Empresarial'),
    ]

    # ----- Identificação -----
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='trial',
        verbose_name='Tipo do Plano'
    )
    nome = models.CharField(
        max_length=100,
        verbose_name='Nome do Plano'
    )
    descricao = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição'
    )

    # ----- Preço -----
    preco_mensal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Preço Mensal (R$)'
    )

    # ----- Limites -----
    max_usuarios = models.IntegerField(
        default=10,
        validators=[MinValueValidator(1)],
        help_text='Número máximo de membros (0 = ilimitado)',
        verbose_name='Máximo de Usuários'
    )
    max_projetos = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text='Quantos projetos o coordenador pode ter (0 = ilimitado)',
        verbose_name='Máximo de Projetos'
    )

    # ----- Módulos incluídos -----
    modulos_inclusos = models.JSONField(
        default=list,
        help_text="Lista de módulos: ['fisioterapia', 'psicologia', 'tecnico']",
        verbose_name='Módulos Inclusos'
    )

    # ----- Exibição -----
    destaque = models.BooleanField(
        default=False,
        help_text='Destacar na landing page (recomendado)',
        verbose_name='Destacado'
    )
    ordem = models.IntegerField(
        default=0,
        help_text='Ordem de exibição (menor primeiro)',
        verbose_name='Ordem'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        ordering = ['ordem', 'preco_mensal']
        verbose_name = 'Plano'
        verbose_name_plural = 'Planos'

    def __str__(self):
        if self.preco_mensal == 0:
            return f"{self.nome} (Grátis)"
        return f"{self.nome} (R$ {self.preco_mensal}/mês)"

    @property
    def modulos_display(self):
        """Retorna os módulos em texto legível."""
        mapa = dict(Projeto.MODULOS_CHOICES)
        return [mapa.get(m, m) for m in (self.modulos_inclusos or [])]

    @property
    def preco_formatado(self):
        """Retorna o preço formatado ou 'Grátis'."""
        if self.preco_mensal == 0:
            return 'Grátis'
        return f'R$ {self.preco_mensal:.2f}'

    @property
    def is_trial(self):
        """Retorna True se for plano Trial."""
        return self.tipo == 'trial'

    @property
    def total_projetos(self):
        """Quantos projetos usam este plano."""
        return self.projetos.count()


# ==============================================================================
# 2. PROJETO (Clínica, Escola, Time, etc.)
# ==============================================================================
class Projeto(models.Model):
    """
    Projeto é o ambiente do cliente. Pode ser uma clínica, escola, time,
    academia, projeto social ou consultório.
    """
    TIPO_CHOICES = [
        ('clinica', 'Clínica de Fisioterapia / Reabilitação'),
        ('escola', 'Escola / Instituição de Ensino'),
        ('time', 'Time / Clube Esportivo'),
        ('academia', 'Academia'),
        ('projeto_social', 'Projeto Social'),
        ('consultorio', 'Consultório Individual'),
        ('outro', 'Outro'),
    ]

    MODULOS_CHOICES = [
        ('fisioterapia', 'Fisioterapia'),
        ('psicologia', 'Psicologia'),
        ('tecnico', 'Análise Técnica'),
    ]

    # ----- Identificação -----
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome do Projeto'
    )
    slug = models.SlugField(
        max_length=160,
        unique=True,
        blank=True,
        default='',
        verbose_name='Slug (URL)'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='clinica',
        verbose_name='Tipo'
    )
    descricao = models.TextField(
        blank=True,
        default='',
        verbose_name='Descrição'
    )
    logo = models.ImageField(
        upload_to='projetos/logos/',
        blank=True,
        null=True,
        verbose_name='Logo'
    )

    # ----- Relacionamentos -----
    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        related_name='projetos',
        null=True,
        blank=True,
        verbose_name='Plano Contratado'
    )
    coordenador = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='projetos_coordenados',
        verbose_name='Coordenador Responsável'
    )

    # ----- Configurações -----
    modulos_ativos = models.JSONField(
        default=list,
        help_text="Módulos ativos: ['fisioterapia', 'psicologia', 'tecnico']",
        verbose_name='Módulos Ativos'
    )
    publico = models.BooleanField(
        default=False,
        help_text='Aparecer na landing page pública',
        verbose_name='Público'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    # ----- Timestamps -----
    criado_em = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name='Criado em'
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        null=True,
        verbose_name='Atualizado em'
    )

    # ----- Trial -----
    data_expiracao_trial = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Data em que o trial expira (null = sem expiração)',
        verbose_name='Expiração do Trial'
    )

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
                .replace(' ', '-').replace('ç', 'c').replace('ã', 'a')
                .replace('á', 'a').replace('é', 'e').replace('í', 'i')
                .replace('ó', 'o').replace('ú', 'u')
                .replace('â', 'a').replace('ê', 'e').replace('ô', 'o')
            )[:50]
            self.slug = f"{nome_slug}-{base}"

        # Se o plano for Trial, define data de expiração automaticamente
        if self.plano and self.plano.is_trial and not self.data_expiracao_trial:
            self.data_expiracao_trial = timezone.now() + timedelta(days=30)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome} ({self.get_tipo_display()})"

    # ----- Métodos -----
    def tem_modulo(self, modulo):
        """Verifica se o projeto tem um módulo ativo."""
        return modulo in (self.modulos_ativos or [])

    def esta_ativo(self):
        """Verifica se o projeto está ativo e o trial não expirou."""
        if not self.ativo:
            return False
        if self.data_expiracao_trial and timezone.now() > self.data_expiracao_trial:
            return False
        return True

    def dias_restantes_trial(self):
        """Retorna quantos dias faltam para o trial expirar."""
        if not self.data_expiracao_trial:
            return None
        delta = self.data_expiracao_trial - timezone.now()
        return max(0, delta.days)

    # ----- Properties -----
    @property
    def total_membros(self):
        """Total de membros ativos."""
        return self.membros.filter(ativo=True).count()

    @property
    def total_atletas(self):
        """Total de atletas/pacientes ativos."""
        return self.membros.filter(ativo=True, tipo='atleta').count()

    @property
    def total_profissionais(self):
        """Total de profissionais (todos, exceto atletas)."""
        return self.membros.filter(ativo=True).exclude(tipo='atleta').count()

    @property
    def modulos_display(self):
        """Retorna os módulos ativos em texto."""
        mapa = dict(self.MODULOS_CHOICES)
        return [mapa.get(m, m) for m in (self.modulos_ativos or [])]

    @property
    def trial_expirado(self):
        """Retorna True se o trial expirou."""
        if not self.data_expiracao_trial:
            return False
        return timezone.now() > self.data_expiracao_trial


# ==============================================================================
# 3. MEMBRO DO PROJETO
# ==============================================================================
class MembroProjeto(models.Model):
    """
    Vincula um usuário a um projeto, definindo seu papel.
    O mesmo usuário pode ter papéis diferentes em projetos diferentes.
    """
    TIPO_MEMBRO = [
        ('coordenador', 'Coordenador / Admin'),
        ('fisioterapeuta', 'Fisioterapeuta'),
        ('psicologo', 'Psicólogo'),
        ('tecnico', 'Técnico / Professor'),
        ('atleta', 'Paciente / Aluno / Atleta'),
    ]

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
        ('O', 'Outro'),
    ]

    # ----- Relacionamentos -----
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='membros',
        verbose_name='Projeto'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='membros_projeto',
        verbose_name='Usuário'
    )

    # ----- Papel -----
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_MEMBRO,
        default='atleta',
        verbose_name='Função'
    )

    # ----- Dados específicos -----
    sexo = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        blank=True,
        default='',
        verbose_name='Sexo'
    )
    modalidade = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='Ex: Futebol, Reabilitação, Pós-operatório, etc.',
        verbose_name='Modalidade'
    )

    # ----- Status -----
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    entrou_em = models.DateTimeField(
        auto_now_add=True,
        null=True,
        verbose_name='Entrou em'
    )

    class Meta:
        unique_together = ['projeto', 'usuario']
        verbose_name = 'Membro do Projeto'
        verbose_name_plural = 'Membros do Projeto'
        ordering = ['-entrou_em']

    def __str__(self):
        return f"{self.usuario.username} - {self.get_tipo_display()} em {self.projeto.nome}"

    @property
    def nome_completo(self):
        """Nome completo do usuário ou username."""
        return self.usuario.get_full_name() or self.usuario.username

    @property
    def is_coordenador(self):
        return self.tipo == 'coordenador'

    @property
    def is_atleta(self):
        return self.tipo == 'atleta'


# ==============================================================================
# 4. CONVITE DE PROJETO
# ==============================================================================
class ConviteProjeto(models.Model):
    """
    Convite enviado por email para um novo membro participar do projeto.
    """
    # ----- Relacionamentos -----
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='convites',
        verbose_name='Projeto'
    )

    # ----- Destinatário -----
    email = models.EmailField(verbose_name='E-mail')
    tipo_membro = models.CharField(
        max_length=20,
        choices=MembroProjeto.TIPO_MEMBRO,
        default='atleta',
        verbose_name='Função'
    )

    # ----- Token -----
    token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        default='',
        verbose_name='Token do Convite'
    )

    # ----- Datas -----
    criado_em = models.DateTimeField(auto_now_add=True, null=True)
    expiracao = models.DateTimeField(blank=True, null=True, verbose_name='Expira em')

    # ----- Status -----
    aceito = models.BooleanField(default=False, verbose_name='Aceito')

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

    # ----- Properties -----
    @property
    def expirado(self):
        """Retorna True se o convite expirou."""
        if not self.expiracao:
            return False
        return timezone.now() > self.expiracao

    @property
    def valido(self):
        """Retorna True se o convite ainda pode ser aceito."""
        return not self.aceito and not self.expirado

    @property
    def link(self):
        """Retorna o link de aceite (relativo)."""
        return f'/projetos/aceitar-convite/{self.token}/'