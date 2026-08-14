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
    
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='lesoes')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='lesoes', null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_LESAO)
    gravidade = models.CharField(max_length=10, choices=GRAVIDADE)
    local = models.CharField(max_length=100)
    data_ocorrencia = models.DateField()
    descricao = models.TextField()
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
    series = models.IntegerField(default=3)
    repeticoes = models.IntegerField(default=10)
    frequencia = models.CharField(max_length=100, default='3x por semana')
    video_url = models.URLField(blank=True)
    check_realizado = models.BooleanField(default=False)  # Atleta confirma execução
    data_realizacao = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.nome

class EvolucaoFisica(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='evolucoes')
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE, related_name='evolucoes', null=True)
    data_registro = models.DateField(auto_now_add=True)
    dor = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    fadiga = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    desempenho = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    mobilidade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)], default=5)
    observacoes = models.TextField(blank=True)
    estagiario_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['-data_registro']
    
    @property
    def percentual_recuperacao(self):
        return int(((10 - self.dor) + (10 - self.fadiga) + self.desempenho + self.mobilidade) / 40 * 100)