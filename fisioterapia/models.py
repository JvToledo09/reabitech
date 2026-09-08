from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Atleta
from projetos.models import Projeto
from django.core.validators import MinValueValidator, MaxValueValidator

class Lesao(models.Model):
    TIPO_LESAO = [
        ('muscular', 'Muscular'),
        ('ligamentar', 'Ligamentar'),
        ('osseo', 'Ósseo'),
        ('tendinite', 'Tendinite'),
        ('fratura', 'Fratura'),
        ('outro', 'Outro'),
    ]

    GRAVIDADE = [
        ('leve', 'Leve - 1 a 2 semanas'),
        ('moderada', 'Moderada - 3 a 6 semanas'),
        ('grave', 'Grave - Mais de 6 semanas'),
    ]

    STATUS_LESAO = [
        ('ativa', 'Ativa'),
        ('em_tratamento', 'Em Tratamento'),
        ('recuperada', 'Recuperada'),
        ('cronica', 'Crônica'),
    ]

    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lesoes')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='lesoes', null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_LESAO)
    gravidade = models.CharField(max_length=10, choices=GRAVIDADE)
    # Novos campos para detalhes
    regiao_corporal = models.CharField(max_length=100, blank=True)
    lado = models.CharField(max_length=20, blank=True)  # Ex: Direito, Esquerdo, Ambos
    causa = models.CharField(max_length=200, blank=True)
    local = models.CharField(max_length=100)
    data_ocorrencia = models.DateField()
    descricao = models.TextField()
    diagnostico = models.TextField(blank=True)
    previsao_recuperacao = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_LESAO, default='ativa')
    observacoes = models.TextField(blank=True)
    fisioterapeuta_responsavel = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, 
        related_name='lesoes_atendidas'
    )
    imagem = models.ImageField(upload_to='lesoes/', null=True, blank=True)
    
    def __str__(self):
        return f"{self.atleta.usuario.get_full_name()} - {self.get_tipo_display()}"

class TratamentoFisioterapico(models.Model):
    lesao = models.ForeignKey(Lesao, on_delete=models.CASCADE, related_name='tratamentos')
    descricao = models.TextField()
    data_inicio = models.DateField(auto_now_add=True)
    data_previsao_termino = models.DateField(null=True, blank=True)
    data_termino = models.DateField(null=True, blank=True)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Tratamento - {self.lesao.atleta.usuario.get_full_name()}"

class ExercicioRecuperacao(models.Model):
    tratamento = models.ForeignKey(TratamentoFisioterapico, on_delete=models.CASCADE, related_name='exercicios')
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    # Novos campos
    grupo_muscular = models.CharField(max_length=100, blank=True)
    dificuldade = models.IntegerField(choices=[(1,'Fácil'), (2,'Médio'), (3,'Difícil')], default=1)
    series = models.IntegerField(default=3)
    repeticoes = models.IntegerField(default=10)
    duracao_minutos = models.IntegerField(default=15)
    frequencia = models.CharField(max_length=100, default='3x por semana')
    video_url = models.URLField(blank=True)
    observacoes = models.TextField(blank=True)
    # Campos de adesão do atleta
    check_realizado = models.BooleanField(default=False)
    data_realizacao = models.DateTimeField(null=True, blank=True)
    dificuldade_percebida = models.IntegerField(choices=[(1,'Muito fácil'), (2,'Fácil'), (3,'Médio'), (4,'Difícil'), (5,'Muito difícil')], null=True, blank=True)
    dor_durante_exercicio = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], null=True, blank=True)
    
    def __str__(self):
        return self.nome

class EvolucaoFisica(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='evolucoes')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='evolucoes', null=True)
    data_registro = models.DateField(auto_now_add=True)
    # Novos campos para uma análise completa
    dor = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    mobilidade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=5)
    forca = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=5)
    desempenho = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    resistencia = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=5)
    flexibilidade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=5)
    observacoes = models.TextField(blank=True)
    estagiario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-data_registro']
    
    @property
    def percentual_recuperacao(self):
        # Fórmula: (10 - dor) + mobilidade + forca + desempenho + resistencia + flexibilidade
        # Total possível é 60, então dividimos por 60 e multiplicamos por 100
        total = (10 - self.dor) + self.mobilidade + self.forca + self.desempenho + self.resistencia + self.flexibilidade
        return int((total / 60) * 100)