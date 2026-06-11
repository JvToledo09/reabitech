from django.db import models
from django.contrib.auth.models import User
from usuarios.models import Atleta
from django.core.validators import MinValueValidator, MaxValueValidator

class AvaliacaoPsicologica(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='avaliacoes_psicologicas')
    data = models.DateField(auto_now_add=True)
    ansiedade = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    motivacao = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    estresse = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    autoestima = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    qualidade_sono = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    observacoes = models.TextField(blank=True)
    psicologo_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    @property
    def score_total(self):
        return round((self.ansiedade + self.motivacao + self.estresse + self.autoestima + self.qualidade_sono) / 5, 1)
    
    @property
    def status_emocional(self):
        score = self.score_total
        if score >= 7:
            return "Bom"
        elif score >= 4:
            return "Regular"
        else:
            return "Atenção Necessária"
    
    def __str__(self):
        return f"Avaliação {self.atleta.usuario.get_full_name()} - {self.data}"

class QuestionarioPeriodico(models.Model):
    atleta = models.ForeignKey(Atleta, on_delete=models.CASCADE, related_name='questionarios')
    data = models.DateField(auto_now_add=True)
    pergunta_1 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pergunta_2 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pergunta_3 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pergunta_4 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    pergunta_5 = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comentarios = models.TextField(blank=True)
    
    def __str__(self):
        return f"Questionário - {self.atleta.usuario.get_full_name()} - {self.data}"