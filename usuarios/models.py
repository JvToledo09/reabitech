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
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    acao = models.CharField(max_length=200)
    descricao = models.TextField()
    data = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.usuario} - {self.acao} - {self.data}"

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