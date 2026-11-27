import pytest

from django.urls import reverse

from prontuario.models import (
    Prontuario,
    CompartilhamentoProntuario,
)
from projetos.models import MembroProjeto


pytestmark = pytest.mark.django_db


def autenticar(client, usuario, projeto):
    client.force_login(usuario)
    session = client.session
    session["projeto_id"] = projeto.pk
    session.save()
    return client


def test_fisio_nao_acessa_prontuario_externo(
    client, atleta, projeto_a, projeto_b,
    usuario_fisio, membro_fisio_projeto_a
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_b,
    )

    autenticar(client, usuario_fisio, projeto_a)

    response = client.get(
        reverse(
            "prontuario:dashboard_prontuario",
            args=[prontuario.pk]
        )
    )

    assert response.status_code in (403, 404)


def test_tecnico_sem_compartilhamento(
    client, atleta, projeto_a,
    usuario_tecnico, membro_tecnico_projeto_a
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_a,
    )

    autenticar(client, usuario_tecnico, projeto_a)

    response = client.get(
        reverse(
            "prontuario:tecnico_ver_prontuario",
            args=[prontuario.pk]
        )
    )

    assert response.status_code in (403, 404)


@pytest.mark.parametrize("rota", [
    "criar_objetivo",
    "imprimir_prontuario",
    "exportar_pdf_prontuario",
])
def test_tecnico_nao_altera_nem_exporta(
    client, atleta, projeto_a,
    usuario_tecnico, membro_tecnico_projeto_a,
    rota
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_a,
    )

    CompartilhamentoProntuario.objects.create(
        prontuario=prontuario,
        tecnico=usuario_tecnico,
        ativo=True,
        pode_comentar=True,
    )

    autenticar(client, usuario_tecnico, projeto_a)

    response = client.get(
        reverse(
            f"prontuario:{rota}",
            args=[prontuario.pk]
        )
    )

    assert response.status_code == 403


def test_compartilhamento_revogado_bloqueia_acesso(
    client, atleta, projeto_a,
    usuario_tecnico, membro_tecnico_projeto_a
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_a,
    )

    CompartilhamentoProntuario.objects.create(
        prontuario=prontuario,
        tecnico=usuario_tecnico,
        ativo=False,
    )

    autenticar(client, usuario_tecnico, projeto_a)

    response = client.get(
        reverse(
            "prontuario:tecnico_ver_prontuario",
            args=[prontuario.pk]
        )
    )

    assert response.status_code in (403, 404)


def test_membro_inativo_nao_acessa(
    client, atleta, projeto_a,
    usuario_fisio, membro_fisio_projeto_a
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_a,
    )

    membro_fisio_projeto_a.ativo = False
    membro_fisio_projeto_a.save()

    autenticar(client, usuario_fisio, projeto_a)

    response = client.get(
        reverse(
            "prontuario:imprimir_prontuario",
            args=[prontuario.pk]
        )
    )

    assert response.status_code == 403


def test_atleta_nao_acessa_arquivamento(
    client, atleta, projeto_a,
    usuario_atleta, membro_atleta_projeto_a
):
    prontuario = Prontuario.objects.create(
        atleta=atleta,
        projeto=projeto_a,
    )

    autenticar(client, usuario_atleta, projeto_a)

    response = client.post(
        reverse(
            "prontuario:arquivar_prontuario_coffito",
            args=[prontuario.pk]
        )
    )

    assert response.status_code == 403
