from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Plano(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    preco_mensal = models.DecimalField(max_digits=10, decimal_places=2)
    max_usuarios = models.IntegerField(default=10)
    inclui_fisioterapia = models.BooleanField(default=True)
    inclui_psicologia = models.BooleanField(default=True)
    inclui_relatorios = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return self.nome

class Projeto(models.Model):
    TIPO_PROJETO = [
        ('time', 'Time Esportivo'),
        ('escola', 'Projeto Escolar'),
        ('clinica', 'Consultório/Clínica'),
        ('outro', 'Outro'),
    ]
    nome = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=TIPO_PROJETO)
    descricao = models.TextField(blank=True)
    plano = models.ForeignKey(Plano, on_delete=models.PROTECT)
    coordenador = models.ForeignKey(User, on_delete=models.PROTECT, related_name='projetos_coordenados')
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='projetos/logos/', blank=True, null=True)

    # Campos para exibição pública (parcerias)
    publico = models.BooleanField(default=False)  # Se True, aparece na landing page
    site_oficial = models.URLField(blank=True)

    def __str__(self):
        return self.nome

class MembroProjeto(models.Model):
    TIPO_MEMBRO = [
        ('coordenador', 'Coordenador'),
        ('tecnico', 'Técnico'),
        ('fisioterapeuta', 'Fisioterapeuta'),
        ('psicologo', 'Psicólogo'),
        ('atleta', 'Atleta'),
    ]
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='membros')
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='membros_projeto')
    tipo = models.CharField(max_length=20, choices=TIPO_MEMBRO)
    data_entrada = models.DateTimeField(auto_now_add=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        unique_together = ('projeto', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} - {self.projeto.nome} ({self.tipo})"

class ConviteProjeto(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='convites')
    email = models.EmailField()
    tipo_membro = models.CharField(max_length=20, choices=MembroProjeto.TIPO_MEMBRO)
    token = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    expiracao = models.DateTimeField()
    aceito = models.BooleanField(default=False)

    def __str__(self):
        return f"Convite para {self.email} - {self.projeto.nome}"