from django.db import models

class Atleta(models.Model):

    nome = models.CharField(max_length=100)

    idade = models.IntegerField()

    esporte = models.CharField(max_length=100)

    lesao = models.CharField(max_length=200)

    def __str__(self):
        return self.nome