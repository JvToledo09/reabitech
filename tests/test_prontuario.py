"""
Testes do módulo prontuário:
- Geração automática de número PR-YYYY-NNNN
- Ciclo de compartilhamento fisio → técnico
"""
import pytest
from django.utils import timezone
from prontuario.models import (
    Prontuario, CompartilhamentoProntuario, ObservacaoTecnico,
)


@pytest.mark.django_db
class TestNumeroProntuario:

    def test_numero_gerado_automaticamente(self, atleta, projeto_a, usuario_fisio):
        """Prontuário novo recebe número PR-YYYY-NNNN."""
        pront = Prontuario.objects.create(
            atleta=atleta,
            projeto=projeto_a,
            fisioterapeuta_responsavel=usuario_fisio,
        )
        ano = timezone.now().year
        assert pront.numero_prontuario.startswith(f'PR-{ano}-')
        assert pront.numero_prontuario.endswith('0001')

    def test_numeros_incrementam(
        self, atleta, projeto_a, modalidade_futebol,
        membro_atleta_projeto_a,
    ):
        """Segundo prontuário recebe número 0002."""
        from django.contrib.auth.models import User
        from usuarios.models import Atleta, Perfil, ModalidadeEsportiva

        u2 = User.objects.create_user('atleta2_teste', password='x')
        Perfil.objects.create(usuario=u2, tipo='atleta')
        mod = ModalidadeEsportiva.objects.first() or ModalidadeEsportiva.objects.create(nome='Teste')
        atleta2 = Atleta.objects.create(usuario=u2, rm='99999', modalidade=mod)

        pront1 = Prontuario.objects.create(atleta=atleta, projeto=projeto_a)
        pront2 = Prontuario.objects.create(atleta=atleta2, projeto=projeto_a)

        n1 = int(pront1.numero_prontuario.split('-')[-1])
        n2 = int(pront2.numero_prontuario.split('-')[-1])
        assert n2 == n1 + 1


@pytest.mark.django_db
class TestCompartilhamento:

    def test_fisio_compartilha_com_tecnico(
        self, atleta, projeto_a, usuario_fisio, usuario_tecnico,
        membro_fisio_projeto_a, membro_tecnico_projeto_a,
    ):
        """Fisio cria compartilhamento; técnico passa a ter acesso."""
        pront = Prontuario.objects.create(
            atleta=atleta, projeto=projeto_a,
            fisioterapeuta_responsavel=usuario_fisio,
        )
        comp = CompartilhamentoProntuario.objects.create(
            prontuario=pront,
            tecnico=usuario_tecnico,
            liberado_por=usuario_fisio,
            ativo=True,
            pode_comentar=True,
        )
        assert comp.ativo is True
        assert comp.pode_comentar is True
        assert pront.compartilhamentos.count() == 1

    def test_tecnico_so_ve_compartilhados(
        self, atleta, projeto_a, usuario_fisio, usuario_tecnico,
        membro_fisio_projeto_a, membro_tecnico_projeto_a,
    ):
        """Sem compartilhamento, técnico não tem vínculo."""
        pront = Prontuario.objects.create(
            atleta=atleta, projeto=projeto_a,
            fisioterapeuta_responsavel=usuario_fisio,
        )
        # Nenhum compartilhamento criado
        compartilhados = Prontuario.objects.filter(
            compartilhamentos__tecnico=usuario_tecnico,
            compartilhamentos__ativo=True,
        )
        assert pront not in compartilhados

    def test_observacao_tecnico_vinculada_ao_compartilhamento(
        self, atleta, projeto_a, usuario_fisio, usuario_tecnico,
        membro_fisio_projeto_a, membro_tecnico_projeto_a,
    ):
        """Técnico registra observação; fica ligada ao compartilhamento."""
        pront = Prontuario.objects.create(
            atleta=atleta, projeto=projeto_a,
            fisioterapeuta_responsavel=usuario_fisio,
        )
        comp = CompartilhamentoProntuario.objects.create(
            prontuario=pront,
            tecnico=usuario_tecnico,
            liberado_por=usuario_fisio,
            ativo=True,
            pode_comentar=True,
        )
        obs = ObservacaoTecnico.objects.create(
            compartilhamento=comp,
            prontuario=pront,
            tecnico=usuario_tecnico,
            tipo='treino',
            nivel_impacto='positivo',
            titulo='Ótimo treino',
            descricao='Atleta completou tudo sem dor.',
            desempenho_treino=9,
        )
        assert obs.cor_impacto == 'success'
        assert obs.icone_tipo == 'fa-running'
        assert comp.observacoes.count() == 1

    def test_impacto_critico_gera_cor_danger(self, atleta, projeto_a,
                                              usuario_fisio, usuario_tecnico,
                                              membro_fisio_projeto_a,
                                              membro_tecnico_projeto_a):
        pront = Prontuario.objects.create(atleta=atleta, projeto=projeto_a)
        comp = CompartilhamentoProntuario.objects.create(
            prontuario=pront, tecnico=usuario_tecnico,
            liberado_por=usuario_fisio, ativo=True,
        )
        obs = ObservacaoTecnico.objects.create(
            compartilhamento=comp, prontuario=pront, tecnico=usuario_tecnico,
            tipo='ocorrencia', nivel_impacto='critico',
            titulo='Lesão no joelho', descricao='...',
            dor_relatada=9,
        )
        assert obs.cor_impacto == 'danger'
        assert obs.icone_tipo == 'fa-exclamation-triangle'
