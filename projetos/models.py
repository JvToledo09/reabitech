from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime, timedelta

class Plano(models.Model):
    """
    Planos de assinatura do REABITECH
    """
    TIPO_PLANO = [
        ('gratuito', 'Gratuito'),
        ('profissional', 'Profissional'),
        ('premium', 'Premium'),
    ]
    
    nome = models.CharField(max_length=50, choices=TIPO_PLANO, unique=True)
    descricao = models.TextField()
    valor_mensal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_projetos = models.IntegerField(default=1)
    max_atletas = models.IntegerField(default=10)
    max_profissionais = models.IntegerField(default=2)
    tem_fisioterapia = models.BooleanField(default=True)
    tem_psicologia = models.BooleanField(default=True)
    tem_relatorios = models.BooleanField(default=True)
    tem_graficos = models.BooleanField(default=True)
    destaque = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.get_nome_display()} - R${self.valor_mensal}/mês"

class Projeto(models.Model):
    """
    Projeto/Clube/Equipe que utiliza a plataforma
    """
    STATUS_PROJETO = [
        ('ativo', 'Ativo'),
        ('inativo', 'Inativo'),
        ('pendente', 'Pendente'),
        ('expirado', 'Expirado'),
    ]
    
    nome = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    descricao = models.TextField(blank=True)
    logo = models.ImageField(upload_to='projetos/logos/', null=True, blank=True)
    
    plano = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True)
    data_assinatura = models.DateField(auto_now_add=True)
    data_vencimento = models.DateField(null=True, blank=True)
    
    coordenador = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='projetos_coordenados')
    
    status = models.CharField(max_length=20, choices=STATUS_PROJETO, default='pendente')
    ativo = models.BooleanField(default=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)
    
    email_contato = models.EmailField(blank=True)
    telefone_contato = models.CharField(max_length=20, blank=True)
    endereco = models.TextField(blank=True)
    
    def __str__(self):
        return self.nome
    
    @property
    def is_expirado(self):
        if self.data_vencimento:
            return datetime.now().date() > self.data_vencimento
        return False
    
    @property
    def dias_restantes(self):
        if self.data_vencimento:
            return (self.data_vencimento - datetime.now().date()).days
        return 0
    
    @property
    def quantidade_atletas(self):
        return self.atletas.count()
    
    @property
    def quantidade_profissionais(self):
        return self.profissionais.count()

class ProfissionalProjeto(models.Model):
    """
    Relacionamento entre profissionais e projetos
    """
    TIPO_PROFISSIONAL = [
        ('tecnico', 'Técnico'),
        ('fisioterapeuta', 'Fisioterapeuta'),
        ('psicologo', 'Psicólogo'),
        ('nutricionista', 'Nutricionista'),
        ('preparador', 'Preparador Físico'),
        ('outro', 'Outro'),
    ]
    
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='profissionais')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projetos_profissionais')
    tipo = models.CharField(max_length=20, choices=TIPO_PROFISSIONAL)
    especialidade = models.CharField(max_length=100, blank=True)
    data_entrada = models.DateField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['projeto', 'usuario']
    
    def __str__(self):
        return f"{self.usuario.username} - {self.projeto.nome} - {self.get_tipo_display()}"

class AtletaProjeto(models.Model):
    """
    Relacionamento entre atletas e projetos
    """
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='atletas')
    atleta = models.ForeignKey('usuarios.Atleta', on_delete=models.CASCADE, related_name='projetos_atleta')
    data_entrada = models.DateField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['projeto', 'atleta']
    
    def __str__(self):
        return f"{self.atleta.usuario.username} - {self.projeto.nome}"

class Parceria(models.Model):
    """
    Solicitações de parceria de novos projetos
    """
    STATUS_PARCERIA = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('rejeitado', 'Rejeitado'),
        ('em_analise', 'Em Análise'),
    ]
    
    nome_projeto = models.CharField(max_length=100)
    nome_parceiro = models.CharField(max_length=100)
    email = models.EmailField()
    telefone = models.CharField(max_length=20)
    plano_interesse = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True)
    mensagem = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_PARCERIA, default='pendente')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    data_resposta = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.nome_projeto} - {self.nome_parceiro} - {self.status}"

class Assinatura(models.Model):
    """
    Histórico de assinaturas do projeto
    """
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='assinaturas')
    plano = models.ForeignKey(Plano, on_delete=models.SET_NULL, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    valor_pago = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='ativa')
    
    def __str__(self):
        return f"{self.projeto.nome} - {self.plano} - {self.data_inicio} a {self.data_fim}"