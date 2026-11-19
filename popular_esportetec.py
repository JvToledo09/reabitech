
import os
import django
import random
from datetime import date, timedelta, time

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from usuarios.models import Perfil, Atleta, ModalidadeEsportiva
from projetos.models import Projeto, Plano, MembroProjeto
from fisioterapia.models import Lesao, TratamentoFisioterapico, EvolucaoFisica
from psicologia.models import AvaliacaoPsicologica
from consultas.models import Consulta
from prontuario.models import Prontuario, Exame

def run():
    print("Iniciando povoamento do ESPORTETEC...")
    
    # Nomes das modalidades sem acento para evitar erro no terminal
    modalidades_nomes = [
        "Futsal Masculino", "Futsal Feminino",
        "Volei Masculino", "Volei Feminino",
        "Volei de Praia Masculino", "Volei de Praia Feminino",
        "Basquete Masculino", "Tenis de Mesa", "Handebol"
    ]
    
    modalidades = {}
    for nome in modalidades_nomes:
        mod, _ = ModalidadeEsportiva.objects.get_or_create(nome=nome)
        modalidades[nome] = mod
        
    plano, _ = Plano.objects.get_or_create(tipo="empresarial", defaults={"nome": "Empresarial", "preco_mensal": 399.90})

    dados_profs = [
        ("jose.calixto", "Jose", "Calixto", "coordenador"),
        ("felipe.gamarra", "Felipe", "Gamarra", "tecnico"),
        ("malu", "Malu", "", "tecnico"),
        ("marcos.souza", "Marcos", "Souza", "tecnico"),
        ("ana.fisio", "Ana", "Fisio", "fisioterapeuta"),
        ("carla.psico", "Carla", "Psico", "psicologo")
    ]

    users_profs = {}
    for username, first, last, tipo in dados_profs:
        user, created = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last, "email": f"{username}@esportetec.com"})
        if created:
            user.set_password("senha123")
            user.save()
            Perfil.objects.create(usuario=user, tipo=tipo)
        users_profs[username] = user

    coord = users_profs["jose.calixto"]
    projeto, _ = Projeto.objects.get_or_create(
        nome="ESPORTETEC",
        defaults={
            "tipo": "escola", "coordenador": coord, "plano": plano, "publico": True, "ativo": True,
            "modulos_ativos": ["fisioterapia", "psicologia", "tecnico"]
        }
    )

    for username, first, last, tipo in dados_profs:
        MembroProjeto.objects.get_or_create(
            projeto=projeto, usuario=users_profs[username],
            defaults={"tipo": tipo, "ativo": True}
        )

    nomes_atletas = [
        ("Lucas", "Almeida"), ("Joao", "Silva"), ("Pedro", "Santos"), ("Gabriel", "Oliveira"),
        ("Matheus", "Costa"), ("Rafael", "Souza"), ("Bruno", "Ferreira"), ("Felipe", "Rodrigues"),
        ("Maria", "Santos"), ("Camila", "Ferreira"), ("Isabela", "Nunes"), ("Larissa", "Dias"),
        ("Marina", "Rocha"), ("Julia", "Mendes"), ("Beatriz", "Lima"), ("Leticia", "Alves"),
        ("Enzo", "Martins"), ("Guilherme", "Barbosa"), ("Thiago", "Ribeiro"), ("Nicolas", "Carvalho")
    ]

    atletas_criados = []
    for i, (first, last) in enumerate(nomes_atletas):
        username = f"{first.lower()}.{last.lower()}{i}"
        user, created = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last})
        
        if created:
            user.set_password("senha123")
            user.save()
            Perfil.objects.create(usuario=user, tipo="atleta")
            
            mod_nome = random.choice(modalidades_nomes)
            mod = modalidades[mod_nome]
            
            tecnico = None
            if "Futsal" in mod_nome or "Handebol" in mod_nome: tecnico = users_profs["felipe.gamarra"]
            elif "Basquete" in mod_nome: tecnico = users_profs["malu"]
            elif "Tenis" in mod_nome: tecnico = users_profs["marcos.souza"]
            else: tecnico = users_profs["jose.calixto"]

            atleta = Atleta.objects.create(
                usuario=user, rm=f"RM{202600+i}", modalidade=mod, tecnico_responsavel=tecnico
            )
            MembroProjeto.objects.create(
                projeto=projeto, usuario=user, tipo="atleta", ativo=True, modalidade=mod
            )
            atletas_criados.append(atleta)

    hoje = date.today()
    
    for atleta in atletas_criados:
        pront, _ = Prontuario.objects.get_or_create(
            atleta=atleta, projeto=projeto, defaults={"status": "ativo", "fisioterapeuta_responsavel": users_profs["ana.fisio"]}
        )

        if random.random() < 0.7:
            dias_atras = random.randint(10, 90)
            data_lesao = hoje - timedelta(days=dias_atras)
            
            lesao = Lesao.objects.create(
                atleta=atleta, projeto=projeto, tipo=random.choice(["muscular", "ligamentar", "tendinite"]),
                gravidade=random.choice(["leve", "moderada"]), local="Joelho D.",
                data_ocorrencia=data_lesao, descricao="Dor ao realizar movimentos bruscos.",
                status="em_tratamento", fisioterapeuta_responsavel=users_profs["ana.fisio"]
            )
            
            TratamentoFisioterapico.objects.create(
                lesao=lesao, descricao="Fortalecimento e alongamento", data_inicio=data_lesao,
                data_previsao_termino=hoje + timedelta(days=30), ativo=True
            )

            num_evolucoes = random.randint(4, 8)
            for j in range(num_evolucoes):
                data_evol = data_lesao + timedelta(days=(j * (dias_atras // num_evolucoes)))
                if data_evol > hoje: break
                
                fator = j / max(1, num_evolucoes - 1)
                dor = int(8 - (fator * 6))
                desemp = int(4 + (fator * 5))
                
                EvolucaoFisica.objects.create(
                    atleta=atleta, projeto=projeto, data_registro=data_evol,
                    dor=max(0, min(10, dor)), mobilidade=desemp, forca=desemp,
                    desempenho=desemp, resistencia=desemp, flexibilidade=desemp,
                    estagiario_responsavel=users_profs["ana.fisio"],
                    observacoes="Progresso dentro do esperado."
                )

        if random.random() < 0.5:
            AvaliacaoPsicologica.objects.create(
                atleta=atleta, projeto=projeto, data=hoje - timedelta(days=random.randint(1, 30)),
                ansiedade=random.randint(2, 7), motivacao=random.randint(5, 10),
                estresse=random.randint(2, 7), autoestima=random.randint(5, 10),
                qualidade_sono=random.randint(4, 9), psicologo_responsavel=users_profs["carla.psico"],
                observacoes="Atleta focado, mas com ansiedade pre-competicao."
            )
            
        for _ in range(random.randint(1, 3)):
            Consulta.objects.create(
                projeto=projeto, atleta=atleta, profissional=users_profs["ana.fisio"],
                data=hoje - timedelta(days=random.randint(1, 20)), hora_inicio=time(14, 0), hora_fim=time(15, 0),
                tipo="fisioterapia", status="realizada", modalidade="presencial", criado_por=users_profs["ana.fisio"]
            )
            Consulta.objects.create(
                projeto=projeto, atleta=atleta, profissional=users_profs["ana.fisio"],
                data=hoje + timedelta(days=random.randint(1, 15)), hora_inicio=time(10, 0), hora_fim=time(11, 0),
                tipo="retorno", status="agendada", modalidade="presencial", criado_por=users_profs["ana.fisio"]
            )
            
        if random.random() < 0.3:
            Exame.objects.create(
                prontuario=pront, data_solicitacao=hoje - timedelta(days=5),
                tipo="imagem", descricao="Ressonancia Magnetica Joelho D.", status="concluido"
            )

    print("TUDO PRONTO! Recarregue o site.")

if __name__ == "__main__":
    with transaction.atomic():
        run()
