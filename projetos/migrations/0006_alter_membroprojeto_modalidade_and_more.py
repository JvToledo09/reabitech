from django.db import migrations, models
import django.db.models.deletion


def zerar_modalidades(apps, schema_editor):
    """Zera modalidade (agora nullable) antes de converter para FK."""
    MembroProjeto = apps.get_model('projetos', 'MembroProjeto')
    MembroProjeto.objects.all().update(modalidade=None)


class Migration(migrations.Migration):

    dependencies = [
        ('projetos', '0005_projeto_data_expiracao_trial_and_more'),
        ('usuarios', '0001_initial'),   # ajuste se o nome for diferente
    ]

    operations = [
        # PASSO 1 — Torna modalidade nullable (ainda CharField)
        migrations.AlterField(
            model_name='membroprojeto',
            name='modalidade',
            field=models.CharField(
                blank=True, null=True, max_length=100, default=None
            ),
        ),

        # PASSO 2 — Agora sim, zera os dados
        migrations.RunPython(zerar_modalidades, migrations.RunPython.noop),

        # PASSO 3 — Converte para FK
        migrations.AlterField(
            model_name='membroprojeto',
            name='modalidade',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='membros_projeto',
                to='usuarios.modalidadeesportiva',
                verbose_name='Modalidade',
            ),
        ),

        # PASSO 4 — Sexo (max_length 1 → 20, choices unificadas)
        migrations.AlterField(
            model_name='membroprojeto',
            name='sexo',
            field=models.CharField(
                blank=True,
                choices=[
                    ('masculino', 'Masculino'),
                    ('feminino', 'Feminino'),
                    ('outro', 'Outro'),
                ],
                default='',
                max_length=20,
                verbose_name='Sexo',
            ),
        ),
    ]