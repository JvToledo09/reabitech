from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from django.core.exceptions import ValidationError
from django.utils import timezone

from projetos.models import Projeto
from projetos.services import (
    validar_capacidade_usuarios,
    validar_capacidade_projetos,
    validar_funcao_membro,
)


def projeto_fake(limite=5, ativo=True):
    return SimpleNamespace(
        plano=SimpleNamespace(max_usuarios=limite),
        esta_ativo=lambda: ativo,
    )


def test_vagas_disponiveis():
    projeto = projeto_fake(5)

    with patch(
        "projetos.services.MembroProjeto.objects.filter"
    ) as filtro:
        filtro.return_value.count.return_value = 4
        validar_capacidade_usuarios(projeto)


def test_limite_usuarios_atingido():
    projeto = projeto_fake(5)

    with patch(
        "projetos.services.MembroProjeto.objects.filter"
    ) as filtro:
        filtro.return_value.count.return_value = 5

        with pytest.raises(ValidationError):
            validar_capacidade_usuarios(projeto)


def test_usuarios_ilimitados():
    validar_capacidade_usuarios(projeto_fake(0))


def test_projeto_inativo():
    with pytest.raises(ValidationError):
        validar_capacidade_usuarios(
            projeto_fake(ativo=False)
        )


def test_projeto_sem_plano():
    projeto = SimpleNamespace(
        plano=None,
        esta_ativo=lambda: True,
    )

    with pytest.raises(ValidationError):
        validar_capacidade_usuarios(projeto)


def test_trial_expirado():
    projeto = Projeto(
        ativo=True,
        data_expiracao_trial=(
            timezone.now() - timedelta(days=1)
        ),
    )

    assert projeto.esta_ativo() is False

    with pytest.raises(ValidationError):
        validar_capacidade_usuarios(projeto)


@pytest.mark.parametrize("cargo", [
    "inexistente",
    "superadmin",
    "",
    None,
])
def test_cargo_invalido(cargo):
    with pytest.raises(ValidationError):
        validar_funcao_membro(cargo)


@pytest.mark.parametrize("cargo", [
    "coordenador",
    "fisioterapeuta",
    "psicologo",
    "tecnico",
    "atleta",
])
def test_cargo_valido(cargo):
    validar_funcao_membro(cargo)


def test_limite_projetos_atingido():
    plano = SimpleNamespace(
        ativo=True,
        max_projetos=5,
    )

    with patch(
        "projetos.services.Projeto.objects.filter"
    ) as filtro:
        filtro.return_value.count.return_value = 5

        with pytest.raises(ValidationError):
            validar_capacidade_projetos(
                object(), plano
            )


def test_projetos_ilimitados():
    plano = SimpleNamespace(
        ativo=True,
        max_projetos=0,
    )

    validar_capacidade_projetos(
        object(), plano
    )


def test_plano_inativo():
    plano = SimpleNamespace(
        ativo=False,
        max_projetos=5,
    )

    with pytest.raises(ValidationError):
        validar_capacidade_projetos(
            object(), plano
        )


def test_modulo_nao_contratado():
    from projetos.models import Plano

    projeto = Projeto(
        ativo=True,
        plano=Plano(
            modulos_inclusos=["fisioterapia"]
        ),
        modulos_ativos=[
            "fisioterapia", "psicologia"
        ],
    )

    assert projeto.tem_modulo("fisioterapia")
    assert not projeto.tem_modulo("psicologia")


def test_modulo_desativado():
    from projetos.models import Plano

    projeto = Projeto(
        ativo=True,
        plano=Plano(
            modulos_inclusos=[
                "fisioterapia", "psicologia"
            ]
        ),
        modulos_ativos=["fisioterapia"],
    )

    assert not projeto.tem_modulo("psicologia")
