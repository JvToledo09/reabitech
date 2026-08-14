import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from projetos.models import Plano, Projeto
from django.contrib.auth.models import User
from usuarios.models import Perfil, Atleta

# Criar planos
planos = [
    {'nome': 'Básico', 'descricao': 'Para pequenos projetos', 'preco_mensal': 49.90, 'max_usuarios': 10},
    {'nome': 'Profissional', 'descricao': 'Para projetos em crescimento', 'preco_mensal': 99.90, 'max_usuarios': 30},
    {'nome': 'Enterprise', 'descricao': 'Para grandes organizações', 'preco_mensal': 199.90, 'max_usuarios': 100},
]
for p in planos:
    Plano.objects.get_or_create(nome=p['nome'], defaults=p)

# Criar projeto ESPORETEC (se não existir)
if not Projeto.objects.filter(nome='ESPORETEC').exists():
    # Criar um coordenador fictício (ou usar um existente)
    user, _ = User.objects.get_or_create(username='coord_esportetec', defaults={'email': 'coord@esportetec.com'})
    if not hasattr(user, 'perfil'):
        Perfil.objects.create(usuario=user, tipo='coordenador')
    projeto = Projeto.objects.create(
        nome='ESPORETEC',
        tipo='escola',
        descricao='Projeto de Esportes da ETEC Pref. Alberto Feres',
        plano=Plano.objects.get(nome='Enterprise'),
        coordenador=user,
        publico=True,
        site_oficial='https://www.etec.sp.gov.br'
    )
    # Adicionar o coordenador como membro
    from projetos.models import MembroProjeto
    MembroProjeto.objects.get_or_create(projeto=projeto, usuario=user, tipo='coordenador')
    print('Projeto ESPORETEC criado com sucesso!')