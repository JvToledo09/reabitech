"""
REABITECH — Script de população do banco de dados
Recria: planos, modalidades, usuários, ESPORETEC, atletas e dados de exemplo.
Uso: python popular_dados.py
"""

import os
import django
from datetime import date, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth.models import User
from usuarios.models import Perfil, Atleta, ModalidadeEsportiva, Notificacao, Alerta
from projetos.models import Projeto, Plano, MembroProjeto, ConviteProjeto
from fisioterapia.models import Lesao, TratamentoFisioterapico, ExercicioRecuperacao, EvolucaoFisica
from psicologia.models import AvaliacaoPsicologica, QuestionarioPeriodico


def linha():
    print("=" * 70)


def titulo(texto):
    print()
    linha()
    print(texto)
    linha()


# ============================================================
# 1. PLANOS
# ============================================================
titulo("1. CRIANDO PLANOS")

planos_dados = [
    {
        'tipo': 'trial',
        'nome': 'Trial Grátis',
        'descricao': 'Teste todas as funcionalidades por 30 dias, sem cartão de crédito.',
        'preco_mensal': 0,
        'max_usuarios': 5,
        'max_projetos': 1,
        'modulos_inclusos': ['fisioterapia'],
        'destaque': False,
        'ordem': 1,
    },
    {
        'tipo': 'profissional',
        'nome': 'Profissional',
        'descricao': 'Para clínicas, times e escolas que precisam de múltiplos módulos.',
        'preco_mensal': 149.90,
        'max_usuarios': 100,
        'max_projetos': 3,
        'modulos_inclusos': ['fisioterapia', 'psicologia', 'tecnico'],
        'destaque': True,
        'ordem': 2,
    },
    {
        'tipo': 'empresarial',
        'nome': 'Empresarial',
        'descricao': 'Sem limites. Todos os módulos e suporte prioritário.',
        'preco_mensal': 399.90,
        'max_usuarios': 10000,
        'max_projetos': 999,
        'modulos_inclusos': ['fisioterapia', 'psicologia', 'tecnico'],
        'destaque': False,
        'ordem': 3,
    },
]

for p in planos_dados:
    obj, criado = Plano.objects.update_or_create(tipo=p['tipo'], defaults=p)
    status = "✅ Criado" if criado else "🔄 Atualizado"
    print(f"  {status}: {obj.nome} — R$ {obj.preco_mensal}/mês")


# ============================================================
# 2. MODALIDADES ESPORTIVAS
# ============================================================
titulo("2. CRIANDO MODALIDADES ESPORTIVAS")

modalidades_nomes = [
    'Futebol', 'Vôlei', 'Basquete', 'Natação', 'Atletismo',
    'Handebol', 'Judô', 'Reabilitação Geral', 'Pós-operatório',
]

modalidades = {}
for nome in modalidades_nomes:
    m, _ = ModalidadeEsportiva.objects.get_or_create(nome=nome)
    modalidades[nome] = m
    print(f"  ✓ {nome}")


# ============================================================
# 3. COORDENADOR
# ============================================================
titulo("3. CRIANDO COORDENADOR")

coord_user, criado = User.objects.get_or_create(
    username='coordenador',
    defaults={
        'email': 'coordenador@reabitech.com',
        'first_name': 'Carlos',
        'last_name': 'Alberto',
        'is_staff': True,
        'is_superuser': True,
    }
)
coord_user.set_password('senha123')
coord_user.save()

coord_perfil, _ = Perfil.objects.get_or_create(
    usuario=coord_user,
    defaults={'tipo': 'coordenador', 'senha_temporaria': False}
)
coord_perfil.tipo = 'coordenador'
coord_perfil.senha_temporaria = False
coord_perfil.save()
print(f"  ✓ coordenador / senha123 — Carlos Alberto")


# ============================================================
# 4. PROFISSIONAIS
# ============================================================
titulo("4. CRIANDO PROFISSIONAIS")

profissionais_dados = [
    ('ana.fisio', 'Ana', 'Ferreira', 'fisioterapeuta'),
    ('carla.psico', 'Carla', 'Mendes', 'psicologo'),
    ('andre.tecnico', 'André', 'Rocha', 'tecnico'),
]

profissionais = {}
for username, nome, sobrenome, tipo in profissionais_dados:
    u, criado = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@reabitech.com',
            'first_name': nome,
            'last_name': sobrenome,
        }
    )
    u.set_password('senha123')
    u.save()

    p, _ = Perfil.objects.get_or_create(
        usuario=u,
        defaults={'tipo': tipo, 'senha_temporaria': False}
    )
    p.tipo = tipo
    p.senha_temporaria = False
    p.save()

    profissionais[username] = u
    print(f"  ✓ {username} / senha123 — {nome} {sobrenome} ({tipo})")


# ============================================================
# 5. PROJETO ESPORETEC
# ============================================================
titulo("5. CRIANDO PROJETO ESPORETEC")

plano_pro = Plano.objects.get(tipo='profissional')

projeto, criado = Projeto.objects.get_or_create(
    nome='ESPORETEC',
    defaults={
        'tipo': 'escola',
        'descricao': 'Projeto escolar da Etec Prefeito Alberto Feres — Araras/SP. '
                     'Acompanhamento de atletas em recuperação física e emocional.',
        'plano': plano_pro,
        'coordenador': coord_user,
        'modulos_ativos': ['fisioterapia', 'psicologia', 'tecnico'],
        'publico': True,
        'ativo': True,
    }
)

# Se já existia, atualiza os campos
if not criado:
    projeto.tipo = 'escola'
    projeto.plano = plano_pro
    projeto.coordenador = coord_user
    projeto.modulos_ativos = ['fisioterapia', 'psicologia', 'tecnico']
    projeto.publico = True
    projeto.ativo = True
    projeto.save()

status = "✅ Criado" if criado else "🔄 Atualizado"
print(f"  {status}: {projeto.nome}")
print(f"     Tipo: {projeto.get_tipo_display()}")
print(f"     Coordenador: {projeto.coordenador.username}")
print(f"     Plano: {projeto.plano.nome}")


# ============================================================
# 6. VINCULAR MEMBROS AO PROJETO
# ============================================================
titulo("6. VINCULANDO MEMBROS AO PROJETO")

# Coordenador
MembroProjeto.objects.get_or_create(
    projeto=projeto,
    usuario=coord_user,
    defaults={'tipo': 'coordenador', 'ativo': True}
)
print(f"  ✓ {coord_user.username} → coordenador")

# Profissionais
for username, _, _, tipo in profissionais_dados:
    u = profissionais[username]
    MembroProjeto.objects.get_or_create(
        projeto=projeto,
        usuario=u,
        defaults={'tipo': tipo, 'ativo': True}
    )
    print(f"  ✓ {username} → {tipo}")


# ============================================================
# 7. ATLETAS DE TESTE
# ============================================================
titulo("7. CRIANDO ATLETAS DE TESTE")

atletas_dados = [
    ('joao.atleta', 'João', 'Silva', 'RM001', 'Futebol', 'M'),
    ('maria.atleta', 'Maria', 'Santos', 'RM002', 'Vôlei', 'F'),
    ('pedro.atleta', 'Pedro', 'Oliveira', 'RM003', 'Basquete', 'M'),
    ('lucas.atleta', 'Lucas', 'Costa', 'RM004', 'Natação', 'M'),
    ('julia.atleta', 'Júlia', 'Ferreira', 'RM005', 'Atletismo', 'F'),
    ('gabriel.atleta', 'Gabriel', 'Souza', 'RM006', 'Handebol', 'M'),
    ('beatriz.atleta', 'Beatriz', 'Lima', 'RM007', 'Judô', 'F'),
]

atletas = {}
for username, nome, sobrenome, rm, modalidade_nome, sexo in atletas_dados:
    # User
    u, _ = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@reabitech.com',
            'first_name': nome,
            'last_name': sobrenome,
        }
    )
    u.set_password('senha123')
    u.save()

    # Perfil
    p, _ = Perfil.objects.get_or_create(
        usuario=u,
        defaults={'tipo': 'atleta', 'senha_temporaria': False}
    )
    p.tipo = 'atleta'
    p.sexo = sexo
    p.save()

    # Atleta
    modalidade = modalidades[modalidade_nome]
    atleta, criado = Atleta.objects.get_or_create(
        usuario=u,
        defaults={
            'rm': rm,
            'modalidade': modalidade,
            'altura': 175,
            'peso': 68,
        }
    )
    if not criado:
        atleta.rm = rm
        atleta.modalidade = modalidade
        atleta.save()

    atletas[username] = atleta

    # Vincular ao projeto
    MembroProjeto.objects.get_or_create(
        projeto=projeto,
        usuario=u,
        defaults={
            'tipo': 'atleta',
            'sexo': sexo,
            'modalidade': modalidade_nome,
            'ativo': True,
        }
    )
    print(f"  ✓ {username} / senha123 — {nome} {sobrenome} (RM {rm}, {modalidade_nome})")


# ============================================================
# 8. DADOS DE EXEMPLO — LESÕES E TRATAMENTOS
# ============================================================
titulo("8. CRIANDO LESÕES E TRATAMENTOS DE EXEMPLO")

ana = profissionais['ana.fisio']

# Lesão 1 — João (futebol, entorse de joelho)
joao = atletas['joao.atleta']
lesao_joao, criado = Lesao.objects.get_or_create(
    atleta=joao,
    local='Joelho direito — ligamento colateral medial',
    defaults={
        'projeto': projeto,
        'tipo': 'ligamentar',
        'gravidade': 'moderada',
        'regiao_corporal': 'Joelho',
        'lado': 'Direito',
        'causa': 'Entorse em treino',
        'data_ocorrencia': date.today() - timedelta(days=21),
        'descricao': 'Entorse durante treino tático. Inchaço e dor ao movimentar.',
        'diagnostico': 'Entorse grau II do ligamento colateral medial.',
        'previsao_recuperacao': date.today() + timedelta(days=15),
        'status': 'em_tratamento',
        'fisioterapeuta_responsavel': ana,
    }
)
print(f"  {'✅' if criado else '🔄'} Lesão de João — Entorse de joelho")

# Tratamento para João
trat_joao, criado = TratamentoFisioterapico.objects.get_or_create(
    lesao=lesao_joao,
    defaults={
        'descricao': 'Protocolo de reabilitação com foco em fortalecimento do quadríceps '
                     'e recuperação da mobilidade articular. Alongamentos + exercícios isométricos.',
        'data_previsao_termino': date.today() + timedelta(days=15),
        'ativo': True,
    }
)
print(f"  {'✅' if criado else '🔄'} Tratamento de João")

# Exercícios para o tratamento
exercicios_dados = [
    ('Flexão de joelho com resistência', 'Quadríceps', 3, 12, 'Fácil'),
    ('Extensão de joelho sentado', 'Quadríceps', 3, 10, 'Médio'),
    ('Agachamento parcial', 'Quadríceps e glúteos', 3, 8, 'Médio'),
    ('Alongamento de isquiotibiais', 'Isquiotibiais', 3, 30, 'Fácil'),
]

for nome, grupo, series, reps, dif in exercicios_dados:
    ex, criado = ExercicioRecuperacao.objects.get_or_create(
        tratamento=trat_joao,
        nome=nome,
        defaults={
            'grupo_muscular': grupo,
            'descricao': f'Executar {series}x{reps} com foco em técnica correta. '
                         f'Não forçar além do limite de dor.',
            'dificuldade': {'Fácil': 1, 'Médio': 2, 'Difícil': 3}.get(dif, 1),
            'series': series,
            'repeticoes': reps,
            'duracao_minutos': 15,
            'frequencia': '3x por semana',
            'observacoes': 'Interromper em caso de dor aguda.',
        }
    )
    print(f"    {'✅' if criado else '🔄'} {nome}")

# Lesão 2 — Maria (vôlei, lesão no ombro)
maria = atletas['maria.atleta']
lesao_maria, criado = Lesao.objects.get_or_create(
    atleta=maria,
    local='Ombro esquerdo — manguito rotador',
    defaults={
        'projeto': projeto,
        'tipo': 'muscular',
        'gravidade': 'leve',
        'regiao_corporal': 'Ombro',
        'lado': 'Esquerdo',
        'causa': 'Movimento repetitivo de saque',
        'data_ocorrencia': date.today() - timedelta(days=10),
        'descricao': 'Dor ao elevar o braço acima da cabeça. Sem inchaço visível.',
        'diagnostico': 'Tendinite do supraespinhal.',
        'previsao_recuperacao': date.today() + timedelta(days=20),
        'status': 'em_tratamento',
        'fisioterapeuta_responsavel': ana,
    }
)
print(f"  {'✅' if criado else '🔄'} Lesão de Maria — Tendinite no ombro")

trat_maria, criado = TratamentoFisioterapico.objects.get_or_create(
    lesao=lesao_maria,
    defaults={
        'descricao': 'Fortalecimento do manguito rotador com carga progressiva. '
                     'Exercícios de rotação externa e interna com elástico.',
        'data_previsao_termino': date.today() + timedelta(days=20),
        'ativo': True,
    }
)
print(f"  {'✅' if criado else '🔄'} Tratamento de Maria")


# ============================================================
# 9. EVOLUÇÕES FÍSICAS
# ============================================================
titulo("9. CRIANDO EVOLUÇÕES FÍSICAS DE EXEMPLO")

# Evoluções de João (5 registros ao longo das últimas semanas)
joao_evolucoes = [
    (21, 9, 3, 4, 3, 4, 3),   # dias atrás, dor, mob, for, des, res, flex
    (14, 7, 5, 5, 4, 5, 4),
    (10, 6, 6, 6, 5, 6, 5),
    (5,  4, 7, 7, 6, 7, 6),
    (1,  2, 8, 8, 8, 8, 8),
]

for dias_atras, dor, mob, forca, des, res, flex in joao_evolucoes:
    EvolucaoFisica.objects.create(
        atleta=joao,
        projeto=projeto,
        dor=dor,
        mobilidade=mob,
        forca=forca,
        desempenho=des,
        resistencia=res,
        flexibilidade=flex,
        observacoes='Evolução positiva' if dor <= 4 else 'Sessão com queixa de dor',
        estagiario_responsavel=ana,
    )
print(f"  ✅ 5 evoluções de João")

# Evoluções de Maria
maria_evolucoes = [
    (10, 6, 5, 5, 5, 6, 5),
    (7,  5, 6, 6, 6, 7, 6),
    (3,  3, 7, 7, 7, 8, 7),
    (0,  2, 8, 8, 8, 8, 8),
]

for dias_atras, dor, mob, forca, des, res, flex in maria_evolucoes:
    EvolucaoFisica.objects.create(
        atleta=maria,
        projeto=projeto,
        dor=dor,
        mobilidade=mob,
        forca=forca,
        desempenho=des,
        resistencia=res,
        flexibilidade=flex,
        observacoes='Boa adesão ao tratamento',
        estagiario_responsavel=ana,
    )
print(f"  ✅ 4 evoluções de Maria")

# Evolução de Pedro (liberado)
pedro = atletas['pedro.atleta']
EvolucaoFisica.objects.create(
    atleta=pedro,
    projeto=projeto,
    dor=0,
    mobilidade=9,
    forca=9,
    desempenho=9,
    resistencia=9,
    flexibilidade=9,
    observacoes='Atleta liberado para treinos completos',
    estagiario_responsavel=ana,
)
print(f"  ✅ 1 evolução de Pedro (liberado)")


# ============================================================
# 10. AVALIAÇÕES PSICOLÓGICAS
# ============================================================
titulo("10. CRIANDO AVALIAÇÕES PSICOLÓGICAS DE EXEMPLO")

carla = profissionais['carla.psico']

# João
for dias_atras, ans, mot, est, aut, sono in [
    (14, 7, 5, 8, 5, 6),
    (7,  5, 6, 6, 6, 7),
    (1,  3, 8, 4, 8, 8),
]:
    AvaliacaoPsicologica.objects.create(
        atleta=joao,
        projeto=projeto,
        ansiedade=ans,
        motivacao=mot,
        estresse=est,
        autoestima=aut,
        qualidade_sono=sono,
        observacoes='Evolução emocional positiva ao longo do tratamento.',
        psicologo_responsavel=carla,
    )
print(f"  ✅ 3 avaliações de João")

# Maria
for dias_atras, ans, mot, est, aut, sono in [
    (10, 6, 7, 6, 7, 7),
    (3,  4, 8, 5, 8, 8),
]:
    AvaliacaoPsicologica.objects.create(
        atleta=maria,
        projeto=projeto,
        ansiedade=ans,
        motivacao=mot,
        estresse=est,
        autoestima=aut,
        qualidade_sono=sono,
        observacoes='Atleta bastante engajada no processo.',
        psicologo_responsavel=carla,
    )
print(f"  ✅ 2 avaliações de Maria")

# Pedro (avaliação com atenção)
AvaliacaoPsicologica.objects.create(
    atleta=pedro,
    projeto=projeto,
    ansiedade=8,
    motivacao=3,
    estresse=9,
    autoestima=3,
    qualidade_sono=4,
    observacoes='Atleta apresenta sinais de ansiedade pré-competitiva. '
                'Recomendado acompanhamento semanal.',
    psicologo_responsavel=carla,
)
print(f"  ✅ 1 avaliação de Pedro (com atenção)")


# ============================================================
# 11. ALERTAS DE EXEMPLO
# ============================================================
titulo("11. CRIANDO ALERTAS DE EXEMPLO")

# Alerta para Pedro (score psicológico baixo)
Alerta.objects.create(
    atleta=pedro,
    tipo='avaliacao_pendente',
    mensagem='Avaliação psicológica com score baixo (5.4/10). Verificar atleta.',
)
print(f"  ✅ Alerta de Pedro (psicológico)")

# Alerta para João (dor alta no histórico)
Alerta.objects.create(
    atleta=joao,
    tipo='dor_alta',
    mensagem='Dor alta registrada (9/10) no início do tratamento. '
             'Evolução positiva desde então.',
)
print(f"  ✅ Alerta de João (dor alta)")


# ============================================================
# 12. NOTIFICAÇÕES DE EXEMPLO
# ============================================================
titulo("12. CRIANDO NOTIFICAÇÕES DE EXEMPLO")

Notificacao.objects.create(
    usuario=joao.usuario,
    titulo='Bem-vindo ao REABITECH',
    mensagem='Seu tratamento começou. Acompanhe sua evolução no painel.',
    link='/dashboard/atleta/',
)
Notificacao.objects.create(
    usuario=ana,
    titulo='Novo paciente atribuído',
    mensagem='Você tem 2 pacientes em tratamento ativo no momento.',
    link='/dashboard/fisioterapeuta/atletas/',
)
print(f"  ✅ 2 notificações criadas")


# ============================================================
# RESUMO FINAL
# ============================================================
titulo("✅ POPULAÇÃO CONCLUÍDA COM SUCESSO")

print(f"  📊 Estatísticas do banco:")
print(f"     Usuários:        {User.objects.count()}")
print(f"     Perfis:          {Perfil.objects.count()}")
print(f"     Projetos:        {Projeto.objects.count()}")
print(f"     Planos:          {Plano.objects.count()}")
print(f"     Modalidades:     {ModalidadeEsportiva.objects.count()}")
print(f"     Atletas:         {Atleta.objects.count()}")
print(f"     Membros:         {MembroProjeto.objects.count()}")
print(f"     Lesões:          {Lesao.objects.count()}")
print(f"     Tratamentos:     {TratamentoFisioterapico.objects.count()}")
print(f"     Exercícios:      {ExercicioRecuperacao.objects.count()}")
print(f"     Evoluções:       {EvolucaoFisica.objects.count()}")
print(f"     Avaliações Psi:  {AvaliacaoPsicologica.objects.count()}")
print(f"     Alertas:         {Alerta.objects.count()}")
print(f"     Notificações:    {Notificacao.objects.count()}")

print()
linha()
print("🔑 CREDENCIAIS DE ACESSO")
linha()
print()
print("  COORDENADOR:")
print("    Login: coordenador")
print("    Senha: senha123")
print()
print("  FISIOTERAPEUTA:")
print("    Login: ana.fisio")
print("    Senha: senha123")
print()
print("  PSICÓLOGO:")
print("    Login: carla.psico")
print("    Senha: senha123")
print()
print("  TÉCNICO:")
print("    Login: andre.tecnico")
print("    Senha: senha123")
print()
print("  ATLETAS:")
print("    Login: joao.atleta / maria.atleta / pedro.atleta")
print("    Senha: senha123 (para todos)")
print()
print("  OU use o RM: RM001 / RM002 / RM003...")
print("    Senha: senha123")
print()
linha()
print("🚀 Próximo passo: python manage.py runserver")
linha()
print()