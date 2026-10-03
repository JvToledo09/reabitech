from django.db import models


# ==============================================================================
# ⚠️ ATENÇÃO: MODELO LEGADO / NÃO USADO
# ==============================================================================
# Este `Atleta` é o modelo ANTIGO do início do projeto.
# O modelo OFICIAL usado pelo sistema é `usuarios.Atleta` (relacionado a User).
#
# Este arquivo está mantido apenas para compatibilidade com migrações antigas.
# NÃO crie novas views/forms usando este modelo.
# ==============================================================================
class Atleta(models.Model):
    STATUS = (
        ('Recuperando', 'Recuperando'),
        ('Atenção', 'Atenção'),
        ('Crítico', 'Crítico'),
        ('Liberado', 'Liberado'),
    )

    nome = models.CharField(max_length=100)
    idade = models.IntegerField()
    esporte = models.CharField(max_length=100)
    lesao = models.CharField(max_length=200)
    altura = models.DecimalField(max_digits=4, decimal_places=2)
    peso = models.DecimalField(max_digits=5, decimal_places=2)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default='Recuperando'
    )

    observacoes = models.TextField(blank=True)

    foto = models.ImageField(
        upload_to='atletas/',
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Atleta (legado)'
        verbose_name_plural = 'Atletas (legado)'

    def __str__(self):
        return self.nome