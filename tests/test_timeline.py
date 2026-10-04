"""
Testes da timeline clínica unificada.
"""
import pytest
from datetime import date
from django.utils import timezone

from prontuario.timeline_utils import (
    coletar_eventos, agrupar_por_mes, contagem_por_tipo, TIPOS_EVENTO,
)
from consultas.models import Consulta
from prontuario.models import Prontuario


@pytest.mark.django_db
class TestTimelineUtils:

    def test_timeline_vazia_retorna_lista(
        self, atleta, projeto_a, membro_atleta_projeto_a
    ):
        eventos = coletar_eventos(atleta, projeto_a)
        assert isinstance(eventos, list)
        # Pode estar vazia ou não — só garante que não quebra

    def test_timeline_inclui_consulta(
        self, atleta, projeto_a, usuario_fisio, membro_fisio_projeto_a,
    ):
        from datetime import timedelta
        amanha = timezone.localdate() + timedelta(days=1)
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        eventos = coletar_eventos(atleta, projeto_a)
        tipos = [e['tipo'] for e in eventos]
        assert 'consulta' in tipos

    def test_filtro_por_tipo(
        self, atleta, projeto_a, usuario_fisio, membro_fisio_projeto_a,
    ):
        from datetime import timedelta
        amanha = timezone.localdate() + timedelta(days=1)
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        apenas_consultas = coletar_eventos(atleta, projeto_a, tipos_desejados=['consulta'])
        for e in apenas_consultas:
            assert e['tipo'] == 'consulta'

    def test_agrupamento_por_mes(
        self, atleta, projeto_a, usuario_fisio, membro_fisio_projeto_a,
    ):
        from datetime import timedelta
        amanha = timezone.localdate() + timedelta(days=1)
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        eventos = coletar_eventos(atleta, projeto_a)
        grupos = agrupar_por_mes(eventos)
        assert isinstance(grupos, list)
        if grupos:
            assert 'mes_ano' in grupos[0]
            assert 'eventos' in grupos[0]
            assert isinstance(grupos[0]['eventos'], list)

    def test_contagem_por_tipo(
        self, atleta, projeto_a, usuario_fisio, membro_fisio_projeto_a,
    ):
        from datetime import timedelta
        amanha = timezone.localdate() + timedelta(days=1)
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='fisioterapia', data=amanha,
            hora_inicio='14:00', hora_fim='15:00',
        )
        Consulta.objects.create(
            projeto=projeto_a, atleta=atleta, profissional=usuario_fisio,
            tipo='retorno', data=amanha + timedelta(days=1),
            hora_inicio='14:00', hora_fim='15:00',
        )
        eventos = coletar_eventos(atleta, projeto_a)
        contagem = contagem_por_tipo(eventos)
        assert isinstance(contagem, dict)
        assert contagem.get('consulta', 0) >= 2

    def test_tipos_evento_tem_estrutura_correta(self):
        """Cada tipo de evento tem label, icone, cor."""
        for tipo, meta in TIPOS_EVENTO.items():
            assert 'label' in meta
            assert 'icone' in meta
            assert 'cor' in meta
            assert meta['icone'].startswith('fa-')


@pytest.mark.django_db
class TestTimelineViews:

    def test_timeline_global_exige_login(self, client):
        from django.urls import reverse
        resp = client.get(reverse('prontuario:timeline_global'))
        assert resp.status_code == 302
        assert 'login' in resp.url.lower() or resp.url.startswith('/login')

    def test_timeline_atleta_view(
        self, client_fisio, atleta, projeto_a, usuario_fisio,
        membro_fisio_projeto_a, membro_atleta_projeto_a,
    ):
        from django.urls import reverse
        resp = client_fisio.get(
            reverse('prontuario:timeline_atleta', args=[atleta.id])
        )
        assert resp.status_code == 200
        assert 'Timeline' in resp.content.decode() or 'timeline' in resp.content.decode().lower()
