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
from .models import Projeto, Plano, MembroProjeto, ConviteProjeto
from usuarios.models import Perfil, Atleta
from usuarios.decorators import perfil_required

def lista_projetos_publicos(request):
    """Página inicial com projetos parceiros."""
    projetos = Projeto.objects.filter(publico=True, ativo=True)
    planos = Plano.objects.filter(ativo=True)
    return render(request, 'projetos/landing.html', {
        'projetos': projetos,
        'planos': planos,
    })

def criar_projeto(request):
    """Cria um novo projeto e define o usuário como coordenador."""
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        plano_id = request.POST.get('plano')
        plano = get_object_or_404(Plano, id=plano_id)

        # Cria o projeto
        projeto = Projeto.objects.create(
            nome=nome,
            tipo=tipo,
            descricao=descricao,
            plano=plano,
            coordenador=request.user,
            publico=False
        )
        # Adiciona o coordenador como membro
        MembroProjeto.objects.create(
            projeto=projeto,
            usuario=request.user,
            tipo='coordenador'
        )
        messages.success(request, f'Projeto "{nome}" criado com sucesso!')
        return redirect('dashboard_coordenador')
    else:
        planos = Plano.objects.filter(ativo=True)
        return render(request, 'projetos/criar_projeto.html', {'planos': planos})

@login_required
def entrar_projeto(request, projeto_id):
    """Entra em um projeto (redireciona para a dashboard correta)."""
    projeto = get_object_or_404(Projeto, id=projeto_id, ativo=True)
    membro = get_object_or_404(MembroProjeto, projeto=projeto, usuario=request.user, ativo=True)
    request.session['projeto_id'] = projeto.id  # Guarda o projeto ativo na sessão
    tipo = membro.tipo
    if tipo == 'coordenador':
        return redirect('dashboard_coordenador')
    elif tipo == 'tecnico':
        return redirect('dashboard_tecnico')
    elif tipo == 'fisioterapeuta':
        return redirect('dashboard_fisioterapeuta')
    elif tipo == 'psicologo':
        return redirect('dashboard_psicologo')
    elif tipo == 'atleta':
        return redirect('dashboard_atleta')
    return redirect('dashboard')

# =========== Gerenciamento de Membros (Coordenador) ===========

@login_required
@perfil_required('coordenador')
def convidar_membro(request):
    """Coordenador convida um novo membro para o projeto."""
    if request.method == 'POST':
        email = request.POST.get('email')
        tipo = request.POST.get('tipo')
        projeto_id = request.session.get('projeto_id')
        projeto = get_object_or_404(Projeto, id=projeto_id, coordenador=request.user)

        # Verifica se o usuário já existe
        try:
            user = User.objects.get(email=email)
            # Se existe, adiciona diretamente
            if MembroProjeto.objects.filter(projeto=projeto, usuario=user).exists():
                messages.error(request, 'Este usuário já é membro do projeto.')
                return redirect('coordenador_membros')
            MembroProjeto.objects.create(projeto=projeto, usuario=user, tipo=tipo)
            messages.success(request, f'Usuário {user.username} adicionado ao projeto.')
        except User.DoesNotExist:
            # Cria um convite
            token = uuid.uuid4().hex
            expiracao = timezone.now() + timedelta(days=7)
            ConviteProjeto.objects.create(
                projeto=projeto,
                email=email,
                tipo_membro=tipo,
                token=token,
                expiracao=expiracao
            )
            # Envia e-mail (simplificado)
            link = request.build_absolute_uri(f'/projetos/aceitar-convite/{token}/')
            send_mail(
                'Convite para o Projeto REABITECH',
                f'Você foi convidado para participar do projeto "{projeto.nome}". Clique no link para aceitar: {link}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=True,
            )
            messages.success(request, f'Convite enviado para {email}.')
        return redirect('coordenador_membros')
    return redirect('dashboard_coordenador')

def aceitar_convite(request, token):
    """Aceita um convite e cria o usuário se necessário."""
    convite = get_object_or_404(ConviteProjeto, token=token, aceito=False)
    if convite.expiracao < timezone.now():
        messages.error(request, 'Este convite expirou.')
        return redirect('home')

    if request.method == 'POST':
        senha = request.POST.get('senha')
        # Cria o usuário com a senha fornecida
        user = User.objects.create_user(
            username=convite.email.split('@')[0] + str(uuid.uuid4().hex[:4]),
            email=convite.email,
            password=senha
        )
        # Cria perfil
        Perfil.objects.create(usuario=user, tipo=convite.tipo_membro)
        # Se for atleta, criar Atleta com RM (aqui pode ser preenchido depois)
        if convite.tipo_membro == 'atleta':
            Atleta.objects.create(usuario=user, rm='')
        # Adiciona ao projeto
        MembroProjeto.objects.create(
            projeto=convite.projeto,
            usuario=user,
            tipo=convite.tipo_membro
        )
        convite.aceito = True
        convite.save()
        # Autentica e loga
        user = authenticate(request, username=user.username, password=senha)
        if user:
            login(request, user)
            messages.success(request, 'Conta criada com sucesso!')
            return redirect('dashboard')
    return render(request, 'projetos/aceitar_convite.html', {'convite': convite})