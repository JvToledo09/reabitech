from django.db import models
from django.contrib.auth.models import User
from datetime import date

class Perfil(models.Model):
    TIPO_USUARIO = [
        ('coordenador', 'Coordenador'),
        ('tecnico', 'Técnico'),
        ('fisioterapeuta', 'Fisioterapeuta'),
        ('psicologo', 'Psicólogo'),
        ('atleta', 'Atleta'),
    ]

    SEXO_CHOICES = [
        ('masculino', 'Masculino'),
        ('feminino', 'Feminino'),
        ('outro', 'Outro'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO)
    telefone = models.CharField(max_length=15, blank=True)
    foto = models.ImageField(upload_to='perfil_fotos/', null=True, blank=True)
    senha_temporaria = models.BooleanField(default=False)
    
    # 🔥 Campos extras para enriquecer o perfil
    data_nascimento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=20, choices=SEXO_CHOICES, blank=True, null=True)
    
    @property
    def idade(self):
        if self.data_nascimento:
            hoje = date.today()
            return hoje.year - self.data_nascimento.year - ((hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day))
        return None

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.get_tipo_display()}"
    
class ModalidadeEsportiva(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    
    def __str__(self):
        return self.nome

class Atleta(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='atleta')
    rm = models.CharField(max_length=20, unique=True)
    modalidade = models.ForeignKey(ModalidadeEsportiva, on_delete=models.SET_NULL, null=True, blank=True)
    tecnico_responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='atletas_orientados'
    )
    data_ingresso = models.DateField(auto_now_add=True)
    altura = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.usuario.get_full_name()} - RM: {self.rm}"
    
    @property
    def imc(self):
        if self.altura and self.peso:
            altura_m = float(self.altura) / 100
            return round(float(self.peso) / (altura_m ** 2), 2)
        return None

# ==============================================
# 🔥 NOVOS MODELOS DE GESTÃO (AUDITORIA, ALERTAS e NOTIFICAÇÃO MELHORADA)
# ==============================================

class Notificacao(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificacoes')
    titulo = models.CharField(max_length=200)
    mensagem = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)
    lida = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True, null=True)

    class Meta:                    # 🔥 ADICIONAR ESSE BLOCO
        ordering = ['-criada_em']
        indexes = [
            models.Index(fields=['usuario', 'lida']),
        ]

    def __str__(self):
        return f"{self.titulo} - {self.usuario.username}"
        

class Auditoria(models.Model):
    """
    Registro de todas as ações importantes do sistema.
    Usado para compliance, auditoria e rastreamento de alterações.
    """
    ACAO_CHOICES = [
        ('criar', 'Criação'),
        ('editar', 'Edição'),
        ('deletar', 'Exclusão'),
        ('visualizar', 'Visualização'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('exportar', 'Exportação'),
        ('importar', 'Importação'),
    ]

    # Quem fez
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='auditorias',
        verbose_name='Usuário'
    )

    # O que fez
    acao = models.CharField(
        max_length=20,
        choices=ACAO_CHOICES,
        verbose_name='Ação'
    )
    modelo = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Modelo Afetado',
        help_text='Ex: Prontuario, Lesao, Atleta'
    )
    objeto_id = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID do Objeto'
    )
    objeto_repr = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Representação do Objeto',
        help_text='String do objeto no momento da ação'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição Detalhada'
    )

    # De onde fez
    ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='Endereço IP'
    )
    user_agent = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='User Agent'
    )

    # Projeto (multi-tenant)
    projeto = models.ForeignKey(
        'projetos.Projeto',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='auditorias',
        verbose_name='Projeto'
    )

    # Quando
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data/Hora'
    )

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Auditoria'
        verbose_name_plural = 'Auditorias'
        indexes = [
            models.Index(fields=['usuario', '-criado_em']),
            models.Index(fields=['modelo', 'objeto_id']),
            models.Index(fields=['-criado_em']),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.get_acao_display()} {self.modelo} #{self.objeto_id}"

    @property
    def cor(self):
        """Cor para exibir na interface."""
        return {
            'criar': 'success',
            'editar': 'warning',
            'deletar': 'danger',
            'visualizar': 'info',
            'login': 'primary',
            'logout': 'secondary',
            'exportar': 'info',
            'importar': 'warning',
        }.get(self.acao, 'secondary')

    @property
    def icone(self):
        """Ícone FontAwesome para exibir."""
        return {
            'criar': 'fa-plus-circle',
            'editar': 'fa-edit',
            'deletar': 'fa-trash-alt',
            'visualizar': 'fa-eye',
            'login': 'fa-sign-in-alt',
            'logout': 'fa-sign-out-alt',
            'exportar': 'fa-file-export',
            'importar': 'fa-file-import',
        }.get(self.acao, 'fa-info-circle')

class Alerta(models.Model):
    # Alertas de recuperação (Ex: Dor subiu para 8, falta exercício)
    TIPO_ALERTA = [
        ('dor_alta', 'Dor Alta'),
        ('falta_exercicio', 'Falta de Exercício'),
        ('evolucao_baixa', 'Evolução Baixa'),
        ('avaliacao_pendente', 'Avaliação Pendente'),
        ('tratamento_prazo', 'Tratamento no Prazo'),
        ('recuperacao_estagnada', 'Recuperação Estagnada'),
    ]
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='alertas')
    tipo = models.CharField(max_length=30, choices=TIPO_ALERTA)
    mensagem = models.TextField()
    criado_em = models.DateTimeField(auto_now_add=True)
    resolvido = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.atleta} - {self.get_tipo_display()}"