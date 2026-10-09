# -*- coding: utf-8 -*-
"""
REABITECH — Popular dados de demonstracao
Cria atletas, prontuarios, lesoes, exames, consultas e mensagens para o video.
Idempotente: pode rodar varias vezes sem duplicar.
"""
import os
import random
from datetime import date, datetime, time, timedelta

from django.contrib.auth.models import User
from django.utils import timezone

from usuarios.models import (
    Perfil, Atleta, ModalidadeEsportiva, Notificacao, Alerta
)
from projetos.models import Projeto, MembroProjeto, Plano
from prontuario.models import (
    Prontuario, Triagem, Objetivo, Medicamento, AvaliacaoCIF,
    AvaliacaoCardiorrespiratoria, EscalaRisco, RelatorioDiario,
    EncaminhamentoMedico, Exame, EvolucaoFisioterapeutica,
    CompartilhamentoProntuario, ObservacaoTecnico,
)
from fisioterapia.models import (
    Lesao, TratamentoFisioterapico, ExercicioRecuperacao, EvolucaoFisica
)
from psicologia.models import AvaliacaoPsicologica, QuestionarioPeriodico
from consultas.models import Consulta
from mensageria.models import Conversa, ParticipanteConversa, Mensagem

print("=" * 60)
print("POPULANDO DADOS DE DEMONSTRACAO")
print("=" * 60)

# ---------- 0. Pega o projeto ESPORETEC ----------
projeto = Projeto.objects.first()
if not projeto:
    print("ERRO: nenhum projeto encontrado. Crie um projeto antes.")
    raise SystemExit(1)
print(f"Projeto: {projeto.nome}")

# ---------- 1. Modalidades (garante que existem) ----------
modalidades = {}
for nome in ['Futsal', 'Vôlei', 'Basquete', 'Handebol', 'Tênis de Mesa']:
    m, _ = ModalidadeEsportiva.objects.get_or_create(nome=nome)
    modalidades[nome] = m
print(f"Modalidades: {list(modalidades.keys())}")

# ---------- 2. Pega profissionais existentes ----------
fisios = list(User.objects.filter(perfil__tipo='fisioterapeuta'))
psicos = list(User.objects.filter(perfil__tipo='psicologo'))
tecnicos = list(User.objects.filter(perfil__tipo='tecnico'))
print(f"Fisios: {len(fisios)} | Psicos: {len(psicos)} | Tecnicos: {len(tecnicos)}")

if not fisios:
    print("ERRO: nenhum fisioterapeuta no banco. Rode popular_dados.py antes.")
    raise SystemExit(1)

# ---------- 3. Lista de atletas a criar ----------
ATLETAS = [
    # Futsal
    ('Lucas Almeida', 'RM100', 'Futsal', 175, 72, 'masculino', 2005),
    ('Rafael Souza', 'RM101', 'Futsal', 178, 75, 'masculino', 2004),
    ('Bruno Costa', 'RM102', 'Futsal', 172, 68, 'masculino', 2006),
    # Vôlei
    ('Camila Ferreira', 'RM103', 'Vôlei', 180, 70, 'feminino', 2005),
    ('Julia Martins', 'RM104', 'Vôlei', 182, 72, 'feminino', 2004),
    ('Beatriz Lima', 'RM105', 'Vôlei', 178, 68, 'feminino', 2006),
    # Basquete
    ('Gabriel Santos', 'RM106', 'Basquete', 190, 85, 'masculino', 2004),
    ('Matheus Oliveira', 'RM107', 'Basquete', 195, 92, 'masculino', 2003),
    ('Pedro Henrique', 'RM108', 'Basquete', 188, 80, 'masculino', 2005),
    # Handebol
    ('Marina Rocha', 'RM109', 'Handebol', 170, 65, 'feminino', 2005),
    ('Larissa Dias', 'RM110', 'Handebol', 168, 62, 'feminino', 2006),
    ('Felipe Cardoso', 'RM111', 'Handebol', 185, 82, 'masculino', 2004),
    # Tênis de Mesa
    ('Vinicius Teixeira', 'RM112', 'Tênis de Mesa', 170, 62, 'masculino', 2007),
    ('Isabela Nunes', 'RM113', 'Tênis de Mesa', 165, 58, 'feminino', 2006),
    ('Rodrigo Pereira', 'RM114', 'Tênis de Mesa', 172, 66, 'masculino', 2005),
]

# ---------- 4. Cria os atletas ----------
atletas_criados = []
for nome, rm, mod, alt, peso, sexo, ano_nasc in ATLETAS:
    username = 'demo_' + nome.lower().replace(' ', '_').replace('í','i').replace('é','e')
    user, criado = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': nome.split(' ')[0],
            'last_name': ' '.join(nome.split(' ')[1:]),
            'email': f'{username}@esporte.com',
        }
    )
    if criado:
        user.set_password('senha123')
        user.save()
        Perfil.objects.get_or_create(usuario=user, defaults={'tipo': 'atleta', 'sexo': sexo})
    else:
        if not hasattr(user, 'perfil'):
            Perfil.objects.create(usuario=user, tipo='atleta', sexo=sexo)

    # Atleta
    atleta, _ = Atleta.objects.get_or_create(
        usuario=user,
        defaults={
            'rm': rm,
            'modalidade': modalidades[mod],
            'altura': alt,
            'peso': peso,
            'data_ingresso': date.today() - timedelta(days=random.randint(60, 400)),
        }
    )
    # Vínculo no projeto
    MembroProjeto.objects.get_or_create(
        projeto=projeto,
        usuario=user,
        defaults={'tipo': 'atleta', 'ativo': True, 'modalidade': modalidades[mod]}
    )
    # Técnico responsável
    if tecnicos:
        atleta.tecnico_responsavel = random.choice(tecnicos)
        atleta.save()
    atletas_criados.append(atleta)

print(f"Criados {len(atletas_criados)} atletas")

# ---------- 5. Cria prontuarios + conteudo clinico ----------
LESOES_POR_MODALIDADE = {
    'Futsal': [
        ('muscular', 'moderada', 'Coxa posterior', 'direito', 'Estiramento no isquiotibial durante sprint'),
        ('ligamentar', 'grave', 'Joelho', 'esquerdo', 'Ruptura parcial do ligamento cruzado anterior'),
        ('osseo', 'leve', 'Tornozelo', 'direito', 'Entorse de grau I'),
    ],
    'Vôlei': [
        ('ligamentar', 'grave', 'Tornozelo', 'direito', 'Entorse grau II no ligamento talofibular'),
        ('tendinite', 'moderada', 'Ombro', 'direito', 'Tendinite no manguito rotador'),
        ('muscular', 'leve', 'Coluna lombar', '', 'Contratura lombar por sobrecarga'),
    ],
    'Basquete': [
        ('ligamentar', 'grave', 'Joelho', 'esquerdo', 'Ruptura do ligamento cruzado anterior'),
        ('muscular', 'moderada', 'Panturrilha', 'direito', 'Estiramento do gastrocnêmio'),
        ('fratura', 'grave', 'Tornozelo', 'direito', 'Fratura por estresse'),
    ],
    'Handebol': [
        ('tendinite', 'moderada', 'Ombro', 'esquerdo', 'Tendinite por arremesso repetitivo'),
        ('muscular', 'moderada', 'Coxa anterior', 'direito', 'Contusão no quadríceps'),
        ('ligamentar', 'leve', 'Punho', 'direito', 'Entorse de punho'),
    ],
    'Tênis de Mesa': [
        ('tendinite', 'leve', 'Cotovelo', 'direito', 'Epicondilite lateral'),
        ('muscular', 'leve', 'Lombar', '', 'Lombalgia por postura'),
        ('tendinite', 'moderada', 'Ombro', 'direito', 'Tendinite do supraespinhal'),
    ],
}

# Listas de dados realistas
OBJETIVOS_EXEMPLO = [
    ('curto', 'Reduzir dor para 2/10 na escala EVA', 'em_andamento', 60),
    ('curto', 'Recuperar 90% da amplitude de movimento', 'em_andamento', 45),
    ('medio', 'Recuperar força muscular grau 4 no MRC', 'em_andamento', 30),
    ('medio', 'Retornar à atividade esportiva leve', 'pendente', 0),
    ('longo', 'Retorno completo ao esporte competitivo', 'pendente', 0),
    ('longo', 'Recuperar propriocepção e estabilidade', 'em_andamento', 40),
]

MEDICAMENTOS_EXEMPLO = [
    ('Ibuprofeno', '400mg', '1 comprimido', 'oral', '8h_8h', 'Em uso'),
    ('Paracetamol', '750mg', '1 comprimido', 'oral', '6h_6h', 'Em uso'),
    ('Diclofenaco gel', '10mg/g', 'Aplicação local', 'topico', '8h_8h', 'Em uso'),
    ('Omeprazol', '20mg', '1 cápsula', 'oral', '1x_dia', 'Em uso'),
]

EXAMES_EXEMPLO = [
    ('raio_x', 'Raio-X do joelho', 'realizado', 'Sem fraturas visíveis. Espaço articular preservado.'),
    ('ressonancia', 'Ressonância magnética do joelho', 'laudo_disponivel', 'Ruptura parcial do LCA. Menisco medial íntegro.'),
    ('ultrassom', 'Ultrassonografia da coxa', 'realizado', 'Edema muscular no terço médio do isquiotibial.'),
    ('espirometria', 'Espirometria', 'laudo_disponivel', 'VEF1 dentro do previsto. Padrão normal.'),
]

EXERCICIOS_EXEMPLO = [
    ('Alongamento isquiotibial', 'Alongamento passivo por 30 segundos', 'Isquiotibiais', 1, 3, 3, 10, '3x por semana'),
    ('Fortalecimento de quadríceps', 'Cadeira extensora com carga leve', 'Quadríceps', 2, 3, 12, 20, '4x por semana'),
    ('Equilíbrio unipodal', 'Apoio em uma perna com olhos fechados', 'Propriocepção', 2, 3, 5, 5, 'Diário'),
    ('Ponte de glúteo', 'Elevação de quadril deitado', 'Glúteos', 1, 3, 15, 10, '3x por semana'),
    ('Elevação de panturrilha', 'Em pé, sobe na ponta dos pés', 'Panturrilha', 1, 3, 15, 8, 'Diário'),
    ('Bicicleta estacionária', 'Aquecimento aeróbico', 'Cardio', 1, 1, 0, 15, 'Diário'),
]

print("\nCriando prontuarios e conteudo clinico...")

for i, atleta in enumerate(atletas_criados):
    # Prontuario
    pront, criado = Prontuario.objects.get_or_create(
        atleta=atleta,
        defaults={
            'projeto': projeto,
            'fisioterapeuta_responsavel': random.choice(fisios),
            'status': 'ativo',
        }
    )
    if not criado:
        continue

    # --- Triagem ---
    Triagem.objects.create(
        prontuario=pront,
        queixa_principal=random.choice(['dor', 'limitacao_movimento', 'edema']),
        descricao_queixa='Paciente relata dor e limitação funcional após trauma esportivo durante treino.',
        historia_doenca_atual='Lesão ocorreu durante atividade esportiva. Início súbito de dor e edema local.',
        historia_pregressa='Sem comorbidades relevantes.',
        historico_familiar='Sem histórico familiar de doenças osteomusculares.',
        medicamentos_uso='Ibuprofeno 400mg se dor.',
        alergias='Nega alergias.',
        cirurgias_anteriores='Nega cirurgias prévias.',
        pressao_arterial='120/80',
        frequencia_cardiaca=random.randint(65, 85),
        frequencia_respiratoria=16,
        temperatura=36.5,
        saturacao_o2=98,
        peso=atleta.peso,
        altura=atleta.altura,
        inspecao='Edema localizado. Sem deformidades.',
        palpacao='Dor à palpação na região afetada.',
        ausculta='Murmúrio vesicular presente bilateralmente.',
        observacoes='Paciente orientado, colaborativo.',
    )

    # --- Objetivos (3 por atleta) ---
    for prazo, titulo, status, pct in random.sample(OBJETIVOS_EXEMPLO, 3):
        Objetivo.objects.create(
            prontuario=pront,
            prazo=prazo,
            titulo=titulo,
            descricao='Objetivo específico, mensurável e temporal.',
            status=status,
            percentual_alcancado=pct,
            data_prevista=date.today() + timedelta(days=random.randint(14, 60)),
            criado_por=random.choice(fisios),
        )

    # --- Medicamentos (2 por atleta) ---
    for nome, dosagem, qtd, via, freq, status in random.sample(MEDICAMENTOS_EXEMPLO, 2):
        Medicamento.objects.create(
            prontuario=pront,
            nome=nome,
            dosagem=dosagem,
            quantidade=qtd,
            via=via,
            frequencia=freq,
            prescritor='Dr. Carlos Andrade',
            crm_prescritor='CRM-SP 123456',
            data_inicio=date.today() - timedelta(days=random.randint(5, 30)),
            status='ativo',
            indicacao='Controle da dor e inflamação.',
            registrado_por=random.choice(fisios),
        )

    # --- CIF ---
    AvaliacaoCIF.objects.create(
        prontuario=pront,
        avaliador=random.choice(fisios),
        b1_funcoes_mentais=0, b2_funcoes_sensoriais=random.randint(1, 2),
        b4_cardiorrespiratorias=0, b7_neuromusculoesqueleticas=random.randint(2, 3),
        b8_pele=0,
        d1_aprendizagem=0, d2_tarefas_gerais=random.randint(0, 1),
        d3_comunicacao=0, d4_mobilidade=random.randint(2, 3),
        d5_cuidado_pessoal=random.randint(0, 1), d6_vida_domestica=random.randint(0, 2),
        d7_relacoes=0, d8_areas_principais=random.randint(2, 3),
        e1_produtos_tecnologia=0, e2_ambiente_natural=0,
        e3_apoio_relacionamentos=0, e4_atitudes=0, e5_servicos_sistemas=0,
        perfil_funcionalidade='Paciente apresenta limitação funcional moderada na região afetada.',
        objetivos_cif='Recuperar funcionalidade plena para retorno esportivo.',
    )

    # --- Escalas (2 por atleta) ---
    EscalaRisco.objects.create(
        prontuario=pront,
        tipo='eva',
        aplicado_por=random.choice(fisios),
        pontuacao=random.randint(3, 8),
        pontuacao_maxima=10,
        nivel_risco=random.choice(['baixo', 'moderado']),
        interpretacao='Dor referida pelo paciente no momento da avaliação.',
    )
    EscalaRisco.objects.create(
        prontuario=pront,
        tipo='morse',
        aplicado_por=random.choice(fisios),
        pontuacao=random.randint(15, 40),
        pontuacao_maxima=125,
        nivel_risco='baixo',
        interpretacao='Risco de queda baixo.',
    )

    # --- Exames (2 por atleta) ---
    for tipo, descricao, status, laudo in random.sample(EXAMES_EXEMPLO, 2):
        Exame.objects.create(
            prontuario=pront,
            tipo=tipo,
            descricao=descricao,
            data_realizacao=date.today() - timedelta(days=random.randint(5, 60)),
            local_realizacao='Hospital São Lucas',
            status=status,
            laudo=laudo,
            conclusao='Correlacionar com quadro clínico.',
            solicitado_por=random.choice(fisios),
        )

    # --- Encaminhamento ---
    EncaminhamentoMedico.objects.create(
        prontuario=pront,
        especialidade='ortopedia',
        medico_encaminhado='Dr. Roberto Almeida',
        urgencia='eletivo',
        motivo='Avaliação ortopédica complementar.',
        resumo_clinico='Paciente com lesão esportiva. Solicito avaliação especializada.',
        hipotese_diagnostica='Lesão ligamentar.',
        status='realizado',
        data_retorno=date.today() - timedelta(days=random.randint(1, 15)),
        parecer_medico='Confirma lesão. Manter fisioterapia intensiva.',
        conduta_sugerida='Fisioterapia 3x por semana por 8 semanas.',
        encaminhado_por=random.choice(fisios),
    )

    # --- Relatorios diarios (3 por atleta) ---
    for j in range(3):
        data_rel = date.today() - timedelta(days=random.randint(1, 30))
        RelatorioDiario.objects.create(
            prontuario=pront,
            data_sessao=data_rel,
            horario_inicio=time(14, 0),
            horario_fim=time(15, 0),
            fisioterapeuta=random.choice(fisios),
            procedimentos='TENS, cinesioterapia, exercícios de fortalecimento.',
            tecnicas_utilizadas='Mobilização passiva, alongamento, exercícios ativos.',
            dor_inicio=random.randint(4, 7),
            dor_fim=random.randint(1, 4),
            estado_geral='Paciente chegou com dor moderada e saiu com melhora.',
            reacao_paciente='Boa adesão ao tratamento.',
            pa_inicial='120/80',
            pa_final='118/78',
            fc_inicial=78,
            fc_final=72,
            plano_proxima_sessao='Progressão de carga nos exercícios.',
            orientacoes_paciente='Continuar exercícios em casa.',
        )

    # --- EvolucaoFisioterapeutica (2 por atleta) ---
    for j in range(2):
        EvolucaoFisioterapeutica.objects.create(
            prontuario=pront,
            tipo=random.choice(['inicial', 'intermediaria', 'reavaliacao']),
            fisioterapeuta=random.choice(fisios),
            subjetivo='Paciente relata melhora progressiva da dor.',
            objetivo='Amplitude de movimento em progressão. Força muscular grau 4.',
            avaliacao='Boa evolução dentro do esperado.',
            plano='Manter protocolo e progredir carga.',
            escala_dor=random.randint(2, 5),
            forca_muscular='MRC 4',
            amplitude_movimento='Amplitude funcional.',
            conduta='Cinesioterapia e fortalecimento.',
            resposta_ao_tratamento='Positiva.',
            paciente_estavel=True,
        )

    # --- Cardio (só pra atletas de esportes dinâmicos) ---
    if atleta.modalidade and atleta.modalidade.nome in ['Futsal', 'Basquete', 'Handebol']:
        AvaliacaoCardiorrespiratoria.objects.create(
            prontuario=pront,
            avaliador=random.choice(fisios),
            condicao_principal='asma',
            frequencia_dispneia=0,
            teste_caminhada_6min=random.randint(550, 700),
            spo2_reouso=98,
            spo2_esforco=97,
            fc_repouso=68,
            fc_maxima=185,
            pa_repouso='118/76',
            escala_borg=4,
            plano_cardiorrespiratorio='Sem restrições cardiorrespiratórias para atividade esportiva.',
        )

print(f"  {len(atletas_criados)} prontuarios completos criados")

# ---------- 6. Lesoes + tratamentos + exercicios ----------
print("\nCriando lesoes, tratamentos e exercicios...")
lesoes_criadas = 0
for atleta in atletas_criados:
    if not atleta.modalidade:
        continue
    modalidade_nome = atleta.modalidade.nome
    opcoes = LESOES_POR_MODALIDADE.get(modalidade_nome, [])
    if not opcoes:
        continue

    # 1 lesao por atleta
    tipo, grav, local, lado, descricao = random.choice(opcoes)
    lesao, criada = Lesao.objects.get_or_create(
        atleta=atleta,
        defaults={
            'projeto': projeto,
            'tipo': tipo,
            'gravidade': grav,
            'regiao_corporal': local,
            'lado': lado,
            'local': local + (f' {lado}' if lado else ''),
            'causa': 'Durante atividade esportiva',
            'data_ocorrencia': date.today() - timedelta(days=random.randint(10, 90)),
            'descricao': descricao,
            'diagnostico': 'Confirmado por exame de imagem.',
            'previsao_recuperacao': date.today() + timedelta(days=random.randint(30, 90)),
            'status': random.choice(['ativa', 'em_tratamento']),
            'fisioterapeuta_responsavel': random.choice(fisios),
        }
    )
    if criada:
        lesoes_criadas += 1

    # Tratamento
    trat, criado = TratamentoFisioterapico.objects.get_or_create(
        lesao=lesao,
        defaults={
            'descricao': 'Protocolo de reabilitação com foco em fortalecimento, mobilidade e propriocepção.',
            'data_previsao_termino': lesao.previsao_recuperacao,
            'ativo': True,
        }
    )

    # Exercicios (3 por tratamento)
    if criado:
        for nome, desc, grupo, dif, series, reps, dur, freq in random.sample(EXERCICIOS_EXEMPLO, 3):
            ExercicioRecuperacao.objects.create(
                tratamento=trat,
                nome=nome,
                descricao=desc,
                grupo_muscular=grupo,
                dificuldade=dif,
                series=series,
                repeticoes=reps,
                duracao_minutos=dur,
                frequencia=freq,
                check_realizado=random.choice([True, False, False]),
            )

    # EvolucaoFisica (3 por atleta)
    for j in range(3):
        EvolucaoFisica.objects.create(
            atleta=atleta,
            projeto=projeto,
            dor=random.randint(2, 7),
            mobilidade=random.randint(5, 9),
            forca=random.randint(5, 9),
            desempenho=random.randint(5, 9),
            resistencia=random.randint(5, 9),
            flexibilidade=random.randint(5, 9),
            observacoes='Progresso dentro do esperado.',
            estagiario_responsavel=random.choice(fisios),
        )

print(f"  {lesoes_criadas} lesoes + tratamentos + exercicios + evolucoes criados")

# ---------- 7. Avaliacoes psicologicas ----------
print("\nCriando avaliacoes psicologicas...")
if psicos:
    psi = psicos[0]
    for atleta in atletas_criados:
        for j in range(2):
            AvaliacaoPsicologica.objects.create(
                atleta=atleta,
                projeto=projeto,
                ansiedade=random.randint(2, 8),
                motivacao=random.randint(4, 9),
                estresse=random.randint(3, 8),
                autoestima=random.randint(4, 9),
                qualidade_sono=random.randint(4, 9),
                observacoes='Paciente responde bem ao acompanhamento psicologico.',
                psicologo_responsavel=psi,
            )
        QuestionarioPeriodico.objects.create(
            atleta=atleta,
            projeto=projeto,
            pergunta_1=random.randint(3, 5),
            pergunta_2=random.randint(3, 5),
            pergunta_3=random.randint(3, 5),
            pergunta_4=random.randint(3, 5),
            pergunta_5=random.randint(3, 5),
            comentarios='Semana produtiva. Me sinto mais confiante.',
        )
    print(f"  {len(atletas_criados) * 2} avaliacoes + {len(atletas_criados)} questionarios")

# ---------- 8. Consultas na agenda ----------
print("\nCriando consultas...")
consultas_criadas = 0
for atleta in atletas_criados[:10]:
    # Consulta passada (realizada)
    Consulta.objects.create(
        projeto=projeto,
        atleta=atleta,
        profissional=random.choice(fisios),
        criado_por=random.choice(fisios),
        tipo=random.choice(['fisioterapia', 'avaliacao_inicial', 'retorno']),
        status='realizada',
        prioridade='normal',
        modalidade='presencial',
        data=date.today() - timedelta(days=random.randint(1, 20)),
        hora_inicio=time(14, 0),
        hora_fim=time(15, 0),
        local='Sala 2',
        motivo='Sessão de fisioterapia',
        realizada_em=timezone.now() - timedelta(days=random.randint(1, 20)),
    )
    consultas_criadas += 1

    # Consulta hoje ou próximo dia
    dia = date.today() + timedelta(days=random.randint(0, 7))
    Consulta.objects.create(
        projeto=projeto,
        atleta=atleta,
        profissional=random.choice(fisios),
        criado_por=random.choice(fisios),
        tipo='fisioterapia',
        status='agendada',
        prioridade=random.choice(['normal', 'alta']),
        modalidade='presencial',
        data=dia,
        hora_inicio=time(10 + random.randint(0, 6), 0),
        hora_fim=time(11 + random.randint(0, 6), 0),
        local='Sala 2',
        motivo='Sessão de fisioterapia',
    )
    consultas_criadas += 1
print(f"  {consultas_criadas} consultas criadas")

# ---------- 9. Mensageria ----------
print("\nCriando conversas na mensageria...")
profissionais = fisios + psicos + tecnicos
if len(profissionais) >= 2:
    # Conversa 1: coordenador + fisio
    coord = User.objects.filter(perfil__tipo='coordenador').first()
    if coord and fisios:
        conv, criada = Conversa.objects.get_or_create(
            projeto=projeto, tipo='dm', criada_por=coord,
            defaults={'nome': ''}
        )
        if criada:
            ParticipanteConversa.objects.create(conversa=conv, usuario=coord)
            ParticipanteConversa.objects.create(conversa=conv, usuario=fisios[0])
            msgs = [
                (coord, 'Ana, como estão os atendimentos desta semana?'),
                (fisios[0], 'Bom dia! Está corrido. Tenho 8 pacientes em tratamento ativo.'),
                (coord, 'Ótimo. Algum caso que precise de atenção especial?'),
                (fisios[0], 'Sim, dois atletas com lesão ligamentar grave. Já encaminhei pra ortopedia.'),
                (coord, 'Perfeito. Vou acompanhar pelo painel.'),
            ]
            for autor, texto in msgs:
                Mensagem.objects.create(conversa=conv, autor=autor, conteudo=texto)

    # Conversa 2: fisio + tecnico (grupo)
    if fisios and tecnicos and psicos:
        conv2, criada = Conversa.objects.get_or_create(
            projeto=projeto, tipo='grupo', nome='Equipe ESPORETEC',
            defaults={'criada_por': fisios[0]}
        )
        if criada:
            for u in [fisios[0], tecnicos[0], psicos[0]]:
                ParticipanteConversa.objects.create(conversa=conv2, usuario=u)
            Mensagem.objects.create(conversa=conv2, autor=fisios[0], conteudo='Galera, vamos alinhar o retorno dos atletas lesionados?')
            Mensagem.objects.create(conversa=conv2, autor=tecnicos[0], conteudo='Beleza. Quem está liberado pra treino leve?')
            Mensagem.objects.create(conversa=conv2, autor=fisios[0], conteudo='João e Lucas. Os outros seguem em fisioterapia.')
            Mensagem.objects.create(conversa=conv2, autor=psicos[0], conteudo='Vou reforçar o acompanhamento emocional no retorno.')
    print("  2 conversas + mensagens criadas")

# ---------- 10. Notificacoes ----------
print("\nCriando notificacoes...")
for user in User.objects.filter(perfil__tipo__in=['coordenador', 'fisioterapeuta'])[:5]:
    Notificacao.objects.get_or_create(
        usuario=user,
        titulo='Nova lesão registrada',
        defaults={
            'mensagem': 'Um atleta registrou nova lesão. Verifique os detalhes.',
            'link': '/dashboard/fisioterapeuta/',
        }
    )

# ---------- 11. Alertas ----------
print("\nCriando alertas...")
for atleta in atletas_criados[:5]:
    Alerta.objects.get_or_create(
        atleta=atleta,
        tipo='dor_alta',
        defaults={'mensagem': 'Dor alta registrada na última evolução (7/10).'},
    )

print("\n" + "=" * 60)
print("POPULACAO CONCLUIDA")
print("=" * 60)
print(f"Atletas: {Atleta.objects.filter(usuario__username__startswith='demo_').count()}")
print(f"Prontuarios: {Prontuario.objects.count()}")
print(f"Lesoes: {Lesao.objects.count()}")
print(f"Consultas: {Consulta.objects.count()}")
print(f"Conversas: {Conversa.objects.count()}")
print(f"Mensagens: {Mensagem.objects.count()}")
print(f"Avaliacoes psi: {AvaliacaoPsicologica.objects.count()}")
print(f"Evolucoes fisicas: {EvolucaoFisica.objects.count()}")
print("")
print("Login de teste dos atletas: usuario 'demo_lucas_almeida', 'demo_camila_ferreira' etc — senha: senha123")
