from django.contrib import admin
from .models import Lesao, TratamentoFisioterapico, ExercicioRecuperacao, EvolucaoFisica

admin.site.register(Lesao)
admin.site.register(TratamentoFisioterapico)
admin.site.register(ExercicioRecuperacao)
admin.site.register(EvolucaoFisica)