"""
Testes de isolamento multi-tenant.
Garante que dados de um projeto NÃO vazam para outro.
"""
import pytest
from consultas.models import Consulta
from projetos.models import MembroProjeto
from django.utils import timezone


@pytest.mark.django_db
class TestIsolamentoMultiTenant:

    def test_membro_projeto_a_nao_ve_dados_projeto_b(
        self, usuario_coordenador, usuario_fisio, atleta,
        projeto_a, projeto_b, membro_coord_projeto_a, membro_fisio_projeto_a,
        membro_atleta_projeto_a,
    ):
        """Consulta criada no projeto A não aparece se filtrar por projeto B."""
        # Cria consulta no projeto A
        consulta_a = Consulta.objects.create(
            projeto=projeto_a,
            atleta=atleta,
            profissional=usuario_fisio,
            tipo='fisioterapia',
            data=timezone.localdate(),
            hora_inicio='14:00',
            hora_fim='15:00',
        )

        # Consulta do projeto B não deve incluir a do projeto A
        consultas_b = Consulta.objects.filter(projeto=projeto_b)
        assert consulta_a not in consultas_b
        assert consultas_b.count() == 0

    def test_usuario_pode_estar_em_multiplos_projetos(
        self, usuario_fisio, projeto_a, projeto_b, membro_fisio_projeto_a,
    ):
        """Mesmo usuário pode ter papéis diferentes em projetos diferentes."""
        MembroProjeto.objects.create(
            projeto=projeto_b,
            usuario=usuario_fisio,
            tipo='coordenador',  # aqui é coordenador
            ativo=True,
        )
        vinculos = MembroProjeto.objects.filter(usuario=usuario_fisio)
        assert vinculos.count() == 2
        tipos = set(vinculos.values_list('tipo', flat=True))
        assert tipos == {'fisioterapeuta', 'coordenador'}

    def test_atleta_projeto_a_nao_aparece_no_projeto_b(
        self, atleta, projeto_a, projeto_b, membro_atleta_projeto_a,
    ):
        """Atleta do projeto A não aparece na lista de membros do projeto B."""
        membros_b = MembroProjeto.objects.filter(projeto=projeto_b)
        assert atleta.usuario not in [m.usuario for m in membros_b]

    def test_filtro_por_projeto_isolado(
        self, usuario_fisio, usuario_atleta,
        projeto_a, projeto_b,
        membro_fisio_projeto_a, membro_atleta_projeto_a,
    ):
        """Query filtrando por projeto=projeto_a não retorna nada do projeto_b."""
        membros_a = MembroProjeto.objects.filter(projeto=projeto_a)
        membros_b = MembroProjeto.objects.filter(projeto=projeto_b)

        assert membros_a.count() == 2
        assert membros_b.count() == 0
