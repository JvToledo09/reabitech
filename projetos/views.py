# ==============================================================================
# REABITECH — APP PROJETOS
# Views: landing, signup, criar_projeto, entrar_projeto, convites
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.db import transaction

from .models import Projeto, Plano, MembroProjeto, ConviteProjeto
from usuarios.models import Perfil, Atleta
from usuarios.decorators import perfil_required


# ==============================================================================
# LANDING PAGE PÚBLICA
# ==============================================================================
def landing_page(request):
    """
    Página inicial pública do SaaS REABITECH.
    Exibe:
    - Vitrine de projetos parceiros (públicos)
    - Seção de planos de assinatura
    - CTAs para login e cadastro
    """
    # Se já estiver logado, redireciona para o dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    # Projetos parceiros (públicos e ativos)
    projetos_parceiros = Projeto.objects.filter(
        ativo=True,
        publico=True
    ).order_by('-criado_em')[:6]

    # Garante que existam planos cadastrados (cria automaticamente se vazio)
    if not Plano.objects.exists():
        Plano.objects.create(
            tipo='trial',
            nome='Trial Grátis',
            descricao='Ideal para começar e testar a plataforma por 30 dias.',
            preco_mensal=0,
            max_usuarios=5,
            max_projetos=1,
            modulos_inclusos=['fisioterapia'],
            destaque=False,
            ordem=1,
            ativo=True,
        )
        Plano.objects.create(
            tipo='profissional',
            nome='Profissional',
            descricao='Para clínicas, times e projetos que precisam de múltiplos módulos.',
            preco_mensal=149.90,
            max_usuarios=100,
            max_projetos=3,
            modulos_inclusos=['fisioterapia', 'psicologia', 'tecnico'],
            destaque=True,
            ordem=2,
            ativo=True,
        )
        Plano.objects.create(
            tipo='empresarial',
            nome='Empresarial',
            descricao='Sem limites. Todos os módulos, usuários e suporte prioritário.',
            preco_mensal=399.90,
            max_usuarios=10000,
            max_projetos=999,
            modulos_inclusos=['fisioterapia', 'psicologia', 'tecnico'],
            destaque=False,
            ordem=3,
            ativo=True,
        )

    planos = Plano.objects.filter(ativo=True).order_by('ordem', 'preco_mensal')

    context = {
        'projetos_parceiros': projetos_parceiros,
        'projetos': projetos_parceiros,  # alias para compatibilidade
        'planos': planos,
    }
    return render(request, 'projetos/landing.html', context)


# Alias para compatibilidade com código antigo
def lista_projetos_publicos(request):
    """
    Alias de `landing_page` para compatibilidade.
    Alguns templates/urls antigos chamam por este nome.
    """
    return landing_page(request)


# ==============================================================================
# SIGNUP SAAS — Cria conta, projeto e vincula plano
# ==============================================================================
def signup_saas(request):
    """
    Fluxo completo de cadastro público:
    1. Cria usuário (User do Django)
    2. Cria Perfil (coordenador)
    3. Cria Projeto com plano escolhido
    4. Vincula usuário como coordenador do projeto
    5. Faz login automático
    """
    # Se já estiver logado, vai direto para o dashboard
    if request.user.is_authenticated:
        return redirect('dashboard:dashboard')

    # Planos disponíveis para o dropdown
    planos = Plano.objects.filter(ativo=True).order_by('ordem', 'preco_mensal')

    # Plano vindo por GET (?plano=X)
    plano_selecionado_id = request.GET.get('plano')

    if request.method == 'POST':
        # ----- Coleta de dados -----
        nome_responsavel = request.POST.get('nome_responsavel', '').strip()
        email = request.POST.get('email', '').strip().lower()
        senha = request.POST.get('senha', '')
        senha_confirm = request.POST.get('senha_confirm', '')
        nome_projeto = request.POST.get('nome_projeto', '').strip()
        tipo_projeto = request.POST.get('tipo_projeto', 'clinica')
        plano_id = request.POST.get('plano_id')

        # ----- Validações -----
        erros = []

        if not nome_responsavel:
            erros.append('Informe seu nome completo.')
        if not email:
            erros.append('Informe um e-mail válido.')
        if not nome_projeto:
            erros.append('Informe o nome do projeto.')
        if not plano_id:
            erros.append('Escolha um plano.')
        if len(senha) < 6:
            erros.append('A senha deve ter pelo menos 6 caracteres.')
        if senha != senha_confirm:
            erros.append('As senhas não coincidem.')

        if User.objects.filter(email=email).exists():
            erros.append('Este e-mail já está cadastrado.')

        if erros:
            for erro in erros:
                messages.error(request, erro)
            return render(request, 'projetos/signup.html', {
                'planos': planos,
                'plano_selecionado_id': int(plano_id) if plano_id and plano_id.isdigit() else None,
            })

        plano = get_object_or_404(Plano, id=plano_id)

        try:
            with transaction.atomic():
                # 1. Gera username único
                username_base = email.split('@')[0][:20]
                username = username_base
                contador = 1
                while User.objects.filter(username=username).exists():
                    username = f"{username_base}{contador}"
                    contador += 1

                # 2. Cria o User
                partes = nome_responsavel.split(' ', 1)
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=senha,
                    first_name=partes[0] if partes else '',
                    last_name=partes[1] if len(partes) > 1 else '',
                )

                # 3. Cria o Perfil (coordenador)
                Perfil.objects.create(
                    usuario=user,
                    tipo='coordenador',
                    senha_temporaria=False,
                )

                # 4. Cria o Projeto
                projeto = Projeto.objects.create(
                    nome=nome_projeto,
                    tipo=tipo_projeto,
                    plano=plano,
                    coordenador=user,
                    modulos_ativos=plano.modulos_inclusos or [],
                    publico=False,
                    ativo=True,
                )

                # 5. Vincula como membro (coordenador)
                MembroProjeto.objects.create(
                    projeto=projeto,
                    usuario=user,
                    tipo='coordenador',
                    ativo=True,
                )

            # 6. Login automático
            user_auth = authenticate(request, username=user.username, password=senha)
            if user_auth:
                login(request, user_auth)
                set_projeto_ativo(request, projeto.id)
                messages.success(
                    request,
                    f'Conta e projeto "{nome_projeto}" criados com sucesso! '
                    f'Bem-vindo ao REABITECH, {user.first_name}!'
                )
                return redirect('dashboard:dashboard_coordenador')

        except Exception as e:
            messages.error(request, f'Erro ao processar o cadastro: {e}')

    context = {
        'planos': planos,
        'plano_selecionado_id': int(plano_selecionado_id) if plano_selecionado_id else None,
    }
    return render(request, 'projetos/signup.html', context)


# ==============================================================================
# CRIAR PROJETO (usuário já logado)
# ==============================================================================
@login_required
def criar_projeto(request):
    """
    Permite que um usuário logado crie um novo projeto.
    (Útil para coordenadores que querem ter múltiplos projetos.)
    """
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipo = request.POST.get('tipo', 'outro')
        descricao = request.POST.get('descricao', '').strip()
        plano_id = request.POST.get('plano')

        # Validações
        if not nome or not tipo or not plano_id:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('projetos:criar_projeto')

        plano = get_object_or_404(Plano, id=plano_id, ativo=True)

        try:
            with transaction.atomic():
                projeto = Projeto.objects.create(
                    nome=nome,
                    tipo=tipo,
                    descricao=descricao,
                    plano=plano,
                    coordenador=request.user,
                    modulos_ativos=plano.modulos_inclusos or [],
                    publico=False,
                    ativo=True,
                )

                MembroProjeto.objects.create(
                    projeto=projeto,
                    usuario=request.user,
                    tipo='coordenador',
                    ativo=True,
                )

            set_projeto_ativo(request, projeto.id)
            messages.success(request, f'Projeto "{nome}" criado com sucesso!')
            return redirect('dashboard:dashboard_coordenador')

        except Exception as e:
            messages.error(request, f'Erro ao criar projeto: {e}')

    planos = Plano.objects.filter(ativo=True).order_by('ordem', 'preco_mensal')
    return render(request, 'projetos/criar_projeto.html', {'planos': planos})


# ==============================================================================
# ENTRAR EM UM PROJETO (selecionar como ativo)
# ==============================================================================
@login_required
def entrar_projeto(request, projeto_id):
    """
    Define o projeto como ativo na sessão e redireciona para o
    dashboard correspondente ao papel do usuário.
    """
    projeto = get_object_or_404(Projeto, id=projeto_id, ativo=True)

    # Verifica se o usuário é membro
    membro = get_object_or_404(
        MembroProjeto,
        projeto=projeto,
        usuario=request.user,
        ativo=True
    )

    # Define como ativo na sessão
    set_projeto_ativo(request, projeto.id)

    # Redireciona para o dashboard do papel
    tipo = membro.tipo
    if tipo == 'coordenador':
        return redirect('dashboard:dashboard_coordenador')
    elif tipo == 'tecnico':
        return redirect('dashboard:dashboard_tecnico')
    elif tipo == 'fisioterapeuta':
        return redirect('dashboard:dashboard_fisioterapeuta')
    elif tipo == 'psicologo':
        return redirect('dashboard:dashboard_psicologo')
    elif tipo == 'atleta':
        return redirect('dashboard:dashboard_atleta')
    return redirect('dashboard:dashboard')


# ==============================================================================
# FUNÇÕES AUXILIARES DE SESSÃO
# ==============================================================================
def get_projeto_ativo(request):
    """
    Retorna o projeto ativo na sessão, verificando se o usuário
    ainda é membro válido dele.
    """
    projeto_id = request.session.get('projeto_id')

    if projeto_id and request.user.is_authenticated:
        try:
            projeto = Projeto.objects.get(id=projeto_id, ativo=True)
            if MembroProjeto.objects.filter(
                projeto=projeto,
                usuario=request.user,
                ativo=True
            ).exists():
                return projeto
        except Projeto.DoesNotExist:
            pass

    return None


def set_projeto_ativo(request, projeto_id):
    """Define o projeto ativo na sessão."""
    request.session['projeto_id'] = projeto_id


# ==============================================================================
# CONVIDAR MEMBRO
# ==============================================================================
@login_required
@perfil_required('coordenador')
def convidar_membro(request):
    """
    Coordenador convida um novo membro para o projeto.
    - Se o e-mail já tem conta, adiciona direto.
    - Se não, cria um convite e envia por email.
    """
    if request.method != 'POST':
        return redirect('dashboard:dashboard_coordenador')

    email = request.POST.get('email', '').strip().lower()
    tipo = request.POST.get('tipo', 'atleta')
    projeto = get_projeto_ativo(request)

    # Validações
    if not projeto:
        messages.error(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard_coordenador')

    if projeto.coordenador != request.user:
        messages.error(request, 'Você não tem permissão para gerenciar este projeto.')
        return redirect('dashboard:dashboard_coordenador')

    if not email:
        messages.error(request, 'Informe um e-mail.')
        return redirect('dashboard:coordenador_membros')

    # Caso 1: Usuário já existe
    try:
        user = User.objects.get(email=email)

        if MembroProjeto.objects.filter(projeto=projeto, usuario=user).exists():
            messages.warning(request, 'Este usuário já é membro do projeto.')
            return redirect('dashboard:coordenador_membros')

        MembroProjeto.objects.create(
            projeto=projeto,
            usuario=user,
            tipo=tipo,
            ativo=True,
        )
        messages.success(
            request,
            f'Usuário {user.get_full_name() or user.username} adicionado ao projeto.'
        )

    # Caso 2: Usuário não existe → cria convite
    except User.DoesNotExist:
        token = uuid.uuid4().hex
        expiracao = timezone.now() + timedelta(days=7)

        ConviteProjeto.objects.create(
            projeto=projeto,
            email=email,
            tipo_membro=tipo,
            token=token,
            expiracao=expiracao,
        )

        # Envia email
        link = request.build_absolute_uri(f'/projetos/aceitar-convite/{token}/')
        try:
            send_mail(
                'Convite para o Projeto REABITECH',
                f'''Olá!

Você foi convidado para participar do projeto "{projeto.nome}" no REABITECH.

Clique no link abaixo para aceitar o convite e criar sua conta:
{link}

Este convite é válido por 7 dias.

Atenciosamente,
Equipe REABITECH''',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            messages.success(request, f'Convite enviado para {email}.')
        except Exception as e:
            messages.warning(
                request,
                f'Convite criado, mas erro no envio de email: {e}'
            )

    return redirect('dashboard:coordenador_membros')


# ==============================================================================
# ACEITAR CONVITE
# ==============================================================================
def aceitar_convite(request, token):
    """
    Aceita um convite de projeto. Cria a conta do usuário se necessário.
    """
    convite = get_object_or_404(ConviteProjeto, token=token, aceito=False)

    # Verifica expiração
    if convite.expiracao and convite.expiracao < timezone.now():
        messages.error(request, 'Este convite expirou. Solicite um novo ao coordenador.')
        return redirect('landing')

    if request.method == 'POST':
        senha = request.POST.get('senha')
        senha_confirm = request.POST.get('senha_confirm')

        # Validações
        if not senha or len(senha) < 6:
            messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
            return render(request, 'projetos/aceitar_convite.html', {'convite': convite})

        if senha != senha_confirm:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'projetos/aceitar_convite.html', {'convite': convite})

        try:
            with transaction.atomic():
                # Gera username único
                username = convite.email.split('@')[0] + str(uuid.uuid4().hex[:4])

                # Cria o User
                user = User.objects.create_user(
                    username=username,
                    email=convite.email,
                    password=senha,
                    first_name=request.POST.get('first_name', ''),
                    last_name=request.POST.get('last_name', ''),
                )

                # Cria o Perfil
                Perfil.objects.create(
                    usuario=user,
                    tipo=convite.tipo_membro,
                    senha_temporaria=False,
                )

                # Se for atleta, cria o registro de Atleta com RM
                if convite.tipo_membro == 'atleta':
                    rm = request.POST.get('rm', '').strip()
                    if not rm:
                        messages.error(request, 'Atletas precisam informar o RM ou matrícula.')
                        user.delete()
                        return render(request, 'projetos/aceitar_convite.html', {'convite': convite})

                    Atleta.objects.create(usuario=user, rm=rm)

                # Vincula ao projeto
                MembroProjeto.objects.create(
                    projeto=convite.projeto,
                    usuario=user,
                    tipo=convite.tipo_membro,
                    ativo=True,
                )

                # Marca convite como aceito
                convite.aceito = True
                convite.save()

            # Login automático
            user_auth = authenticate(request, username=user.username, password=senha)
            if user_auth:
                login(request, user_auth)
                set_projeto_ativo(request, convite.projeto.id)
                messages.success(request, 'Conta criada com sucesso! Bem-vindo ao REABITECH.')
                return redirect('dashboard:dashboard')

        except Exception as e:
            messages.error(request, f'Erro ao aceitar convite: {e}')

    return render(request, 'projetos/aceitar_convite.html', {'convite': convite})