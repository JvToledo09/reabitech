from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Perfil(models.Model):
    TIPO_USUARIO = [
        ('coordenador', 'Coordenador'),
        ('tecnico', 'Técnico'),
        ('estagiario_fisio', 'Estagiário - Fisioterapia'),
        ('estagiario_psico', 'Estagiário - Psicologia'),
        ('atleta', 'Atleta'),
    ]
    
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    tipo = models.CharField(max_length=20, choices=TIPO_USUARIO)
    telefone = models.CharField(max_length=15, blank=True)
    foto = models.ImageField(upload_to='perfil_fotos/', null=True, blank=True)
    
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
    modalidade = models.ForeignKey(ModalidadeEsportiva, on_delete=models.SET_NULL, null=True)
    tecnico_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='atletas_orientados')
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