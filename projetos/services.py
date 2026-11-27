from django.core.exceptions import ValidationError
from .models import Projeto, MembroProjeto


def validar_capacidade_usuarios(projeto, quantidade=1):
    """Valida a disponibilidade de vagas no projeto."""

    if not projeto.esta_ativo():
        raise ValidationError(
            "Este projeto esta inativo ou expirado."
        )

    if not projeto.plano:
        raise ValidationError(
            "Este projeto nao possui um plano contratado."
        )

    limite = projeto.plano.max_usuarios

    if limite < 0:
        raise ValidationError(
            "O limite do plano esta configurado incorretamente."
        )

    if quantidade < 1:
        raise ValidationError(
            "Quantidade de vagas invalida."
        )

    if limite == 0:
        return

    total = MembroProjeto.objects.filter(
        projeto=projeto,
        ativo=True,
    ).count()

    if total + quantidade > limite:
        raise ValidationError(
            f"Limite de {limite} usuarios atingido. "
            "Desative um membro ou altere seu plano."
        )


def validar_capacidade_projetos(usuario, plano):
    """Valida a capacidade de criacao de projetos."""

    if not plano.ativo:
        raise ValidationError(
            "Este plano nao esta disponivel."
        )

    limite = plano.max_projetos

    if limite < 0:
        raise ValidationError(
            "Limite de projetos invalido."
        )

    if limite == 0:
        return

    total = Projeto.objects.filter(
        coordenador=usuario
    ).count()

    if total >= limite:
        raise ValidationError(
            f"Limite de {limite} projetos atingido."
        )


def validar_funcao_membro(tipo):
    """Impede cargos invalidos enviados pelo navegador."""

    tipos_validos = dict(MembroProjeto.TIPO_MEMBRO)

    if tipo not in tipos_validos:
        raise ValidationError(
            "Funcao de membro invalida."
        )


def validar_gestao_projeto(usuario, projeto):
    """Exige autorizacao ativa de coordenador."""

    if not projeto or not projeto.esta_ativo():
        raise ValidationError(
            "Projeto indisponivel."
        )

    autorizado = MembroProjeto.objects.filter(
        projeto=projeto,
        usuario=usuario,
        tipo="coordenador",
        ativo=True,
    ).exists()

    if not autorizado:
        raise ValidationError(
            "Voce nao possui permissao para gerenciar este projeto."
        )
