"""
Testes do módulo consultas:
- Criação válida
- Validação de conflito de horário
- Regra: atleta só vê suas consultas
"""
import pytest
from django.utils import timezone
from datetime import timedelta, time
from consultas.models import Consulta
from consultas.forms import ConsultaForm


@pytest.mark.django_db
class TestConsultaModel:

    def test_consulta_criada(self, atleta, projeto_a, usuario_fisio,
                              membro_fisio_projeto_a):
        amanha = timezone.localdate() + timedelta(days=1)
        c = Consulta.objects.create(
            projeto=projeto_a,
            atleta=atleta,
            profissional=usuario_fisio,
            tipo='fisioterapia',
            data=amanha,
            hora_inicio=time(14, 0),
            hora_fim=time(15, 0),
        )
        c.refresh_from_db()
        assert c.pk is not None
        assert c.status == 'agendada'
        assert c.duracao_minutos == 60
        assert c.cor_status == 'info'
        assert c.icone_tipo == 'fa-dumbbell'

    def test_acoes_status(self, atleta, projeto_a, usuario_fisio):
        c = Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='retorno', data=timezone.localdate() + timedelta(days=1),
            hora_inicio='10:00', hora_fim='10:30',
        )
        c.confirmar()
        assert c.status == 'confirmada'
        c.marcar_realizada()
        assert c.status == 'realizada'
        assert c.realizada_em is not None
        c.cancelar(motivo='Paciente desmarcou')
        assert c.status == 'cancelada'
        assert c.motivo_cancelamento == 'Paciente desmarcou'


@pytest.mark.django_db
class TestValidacaoConflito:

    def test_horario_fim_antes_inicio_falha(self, atleta, projeto_a, usuario_fisio,
                                              membro_fisio_projeto_a,
                                              membro_atleta_projeto_a):
        form = ConsultaForm(
            data={
                'atleta': atleta.id,
                'profissional': usuario_fisio.id,
                'tipo': 'fisioterapia',
                'prioridade': 'normal',
                'modalidade': 'presencial',
                'data': (timezone.localdate() + timedelta(days=1)).isoformat(),
                'hora_inicio': '15:00',
                'hora_fim': '14:00',  # antes do início
            },
            projeto=projeto_a,
        )
        assert not form.is_valid()
        assert 'horário de término' in str(form.errors).lower() or 'posterior' in str(form.errors).lower()

    def test_data_passada_falha(self, atleta, projeto_a, usuario_fisio,
                                 membro_fisio_projeto_a, membro_atleta_projeto_a):
        form = ConsultaForm(
            data={
                'atleta': atleta.id,
                'profissional': usuario_fisio.id,
                'tipo': 'fisioterapia',
                'prioridade': 'normal',
                'modalidade': 'presencial',
                'data': (timezone.localdate() - timedelta(days=1)).isoformat(),
                'hora_inicio': '14:00',
                'hora_fim': '15:00',
            },
            projeto=projeto_a,
        )
        assert not form.is_valid()
        assert 'passad' in str(form.errors).lower()

    def test_conflito_mesmo_profissional_falha(
        self, atleta, projeto_a, usuario_fisio,
        membro_fisio_projeto_a, membro_atleta_projeto_a,
    ):
        amanha = timezone.localdate() + timedelta(days=1)
        # Consulta existente
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        # Nova consulta com sobreposição
        form = ConsultaForm(
            data={
                'atleta': atleta.id,
                'profissional': usuario_fisio.id,
                'tipo': 'retorno',
                'prioridade': 'normal',
                'modalidade': 'presencial',
                'data': amanha.isoformat(),
                'hora_inicio': '14:30',  # sobrepõe
                'hora_fim': '15:30',
            },
            projeto=projeto_a,
        )
        assert not form.is_valid()
        assert 'conflito' in str(form.errors).lower()

    def test_sem_conflito_horarios_distintos(
        self, atleta, projeto_a, usuario_fisio,
        membro_fisio_projeto_a, membro_atleta_projeto_a,
    ):
        amanha = timezone.localdate() + timedelta(days=1)
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        # Nova consulta no mesmo dia, horário diferente — deve passar
        form = ConsultaForm(
            data={
                'atleta': atleta.id,
                'profissional': usuario_fisio.id,
                'tipo': 'retorno',
                'prioridade': 'normal',
                'modalidade': 'presencial',
                'data': amanha.isoformat(),
                'hora_inicio': '16:00',
                'hora_fim': '17:00',
            },
            projeto=projeto_a,
        )
        assert form.is_valid(), f'Erros: {form.errors}'


@pytest.mark.django_db
class TestVisibilidadeConsultas:

    def test_atleta_ve_somente_suas_consultas(
        self, atleta, projeto_a, usuario_fisio, usuario_atleta,
        membro_fisio_projeto_a, membro_atleta_projeto_a,
    ):
        """Atleta só vê consultas em que ele é o `atleta`."""
        from django.contrib.auth.models import User
        from usuarios.models import Atleta, Perfil

        # 2º atleta
        u2 = User.objects.create_user('outro_atleta', password='x')
        Perfil.objects.create(usuario=u2, tipo='atleta')
        from usuarios.models import ModalidadeEsportiva
        mod = ModalidadeEsportiva.objects.first() or ModalidadeEsportiva.objects.create(nome='X')
        a2 = Atleta.objects.create(usuario=u2, rm='99999', modalidade=mod)

        amanha = timezone.localdate() + timedelta(days=1)
        c1 = Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        c2 = Consulta.objects.create(
            projeto=projeto_a, atleta=a2, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='16:00', hora_fim='17:00',
        )

        # Simula o filtro que a view faz
        minhas = Consulta.objects.filter(atleta=atleta)
        assert c1 in minhas
        assert c2 not in minhas
