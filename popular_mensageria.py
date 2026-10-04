# ==============================================================================
# REABITECH — Popular dados de teste da MENSAGERIA
# Uso: python manage.py shell < popular_mensageria.py
# Ou via load_dotenv (produção)
# ==============================================================================

from django.contrib.auth.models import User
from projetos.models import Projeto, MembroProjeto
from mensageria.models import Conversa, ParticipanteConversa, Mensagem


def _get_user(username):
    try:
        return User.objects.get(username=username)
    except User.DoesNotExist:
        return None


def main():
    print("\n🚀 Populando mensageria de teste...\n")

    projeto = Projeto.objects.first()
    if not projeto:
        print("❌ Nenhum projeto encontrado. Rode popular_dados.py primeiro.")
        return

    print(f"📁 Projeto: {projeto.nome}")

    coordenador = _get_user('coordenador')
    ana = _get_user('ana.fisio')
    carla = _get_user('carla.psico')
    andre = _get_user('andre.tecnico')

    profissionais = [u for u in [coordenador, ana, carla, andre] if u]
    if len(profissionais) < 2:
        print("❌ Faltam usuários profissionais (coordenador, ana.fisio, carla.psico, andre.tecnico).")
        return

    # ============================================================
    # 1. DM — Coordenador ↔ Fisioterapeuta
    # ============================================================
    if coordenador and ana:
        conversa_dm, created = Conversa.objects.get_or_create(
            projeto=projeto, tipo='dm',
            defaults={'criada_por': coordenador}
        )
        if created:
            ParticipanteConversa.objects.get_or_create(conversa=conversa_dm, usuario=coordenador)
            ParticipanteConversa.objects.get_or_create(conversa=conversa_dm, usuario=ana)

            Mensagem.objects.create(
                conversa=conversa_dm, autor=coordenador,
                conteudo='Oi Ana, tudo bem? Como estão os atendimentos desta semana?'
            )
            Mensagem.objects.create(
                conversa=conversa_dm, autor=ana,
                conteudo='Oi! Tudo ótimo. Atendi 8 pacientes hoje, todos com evolução positiva.'
            )
            Mensagem.objects.create(
                conversa=conversa_dm, autor=coordenador,
                conteudo='Excelente! Vou precisar de um relatório consolidado até sexta.'
            )
            Mensagem.objects.create(
                conversa=conversa_dm, autor=ana,
                conteudo='Perfeito, envio até quinta à noite. 👌'
            )
            print(f"   ✅ DM Coordenador ↔ Ana criada ({conversa_dm.mensagens.count()} mensagens)")
        else:
            print(f"   ℹ️  DM Coordenador ↔ Ana já existia")

    # ============================================================
    # 2. DM — Fisioterapeuta ↔ Psicóloga
    # ============================================================
    if ana and carla:
        conversa_dm2, created = Conversa.objects.get_or_create(
            projeto=projeto, tipo='dm',
            defaults={'criada_por': ana}
        )
        if created:
            ParticipanteConversa.objects.get_or_create(conversa=conversa_dm2, usuario=ana)
            ParticipanteConversa.objects.get_or_create(conversa=conversa_dm2, usuario=carla)

            Mensagem.objects.create(
                conversa=conversa_dm2, autor=ana,
                conteudo='Carla, sobre o paciente João: ele está com dor no joelho esquerdo ainda em 6/10.'
            )
            Mensagem.objects.create(
                conversa=conversa_dm2, autor=carla,
                conteudo='Obrigada pelo aviso. Vou conversar com ele hoje sobre ansiedade pré-treino.'
            )
            print(f"   ✅ DM Ana ↔ Carla criada ({conversa_dm2.mensagens.count()} mensagens)")

    # ============================================================
    # 3. GRUPO — Equipe do João (coordenador + ana + carla + andre)
    # ============================================================
    conversa_grupo, created = Conversa.objects.get_or_create(
        projeto=projeto, tipo='grupo', nome='Equipe do João',
        defaults={'criada_por': coordenador}
    )
    if created:
        for prof in profissionais:
            ParticipanteConversa.objects.get_or_create(conversa=conversa_grupo, usuario=prof)

        if coordenador:
            Mensagem.objects.create(
                conversa=conversa_grupo, autor=coordenador,
                conteudo='Pessoal, criei esse grupo pra alinharmos o caso do João. Vamos trocar informações por aqui.'
            )
        if ana:
            Mensagem.objects.create(
                conversa=conversa_grupo, autor=ana,
                conteudo='Show! Já coloquei os exercícios dele na plataforma. Adesão tá em 85%.'
            )
        if carla:
            Mensagem.objects.create(
                conversa=conversa_grupo, autor=carla,
                conteudo='Ótimo. Na avaliação de ontem o score emocional subiu pra 7.4. Progresso! 🎉'
            )
        if andre:
            Mensagem.objects.create(
                conversa=conversa_grupo, autor=andre,
                conteudo='Boa! Nos treinos ele já tá bem mais confiante no apoio do lado esquerdo.'
            )
        if coordenador:
            Mensagem.objects.create(
                conversa=conversa_grupo, autor=coordenador,
                conteudo='Time sensacional. Vamos manter esse ritmo! 💪'
            )
        print(f"   ✅ Grupo 'Equipe do João' criado ({conversa_grupo.mensagens.count()} mensagens)")

    # ============================================================
    # 4. GRUPO — Equipe Técnica (coordenador + andre + ana)
    # ============================================================
    conversa_grupo2, created = Conversa.objects.get_or_create(
        projeto=projeto, tipo='grupo', nome='Equipe Técnica - Futebol',
        defaults={'criada_por': andre}
    )
    if created and andre:
        for prof in [u for u in [coordenador, andre, ana] if u]:
            ParticipanteConversa.objects.get_or_create(conversa=conversa_grupo2, usuario=prof)

        Mensagem.objects.create(
            conversa=conversa_grupo2, autor=andre,
            conteudo='Alguém viu o jogo de ontem? Precisamos rever a preparação física dos meninos.'
        )
        if ana:
            Mensagem.objects.create(
                conversa=conversa_grupo2, autor=ana,
                conteudo='Concordo. Vou reforçar o trabalho de propriocepção essa semana.'
            )
        print(f"   ✅ Grupo 'Equipe Técnica' criado ({conversa_grupo2.mensagens.count()} mensagens)")

    print(f"\n🎉 Mensageria populada com sucesso!")
    print(f"   Total de conversas: {Conversa.objects.filter(projeto=projeto).count()}")
    print(f"   Total de mensagens: {Mensagem.objects.filter(conversa__projeto=projeto).count()}")


if __name__ == '__main__' or True:
    main()
