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
    if not request.user.is_authenticated:
        messages.info(request, 'Faça login para criar um projeto.')
        return redirect('login')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        tipo = request.POST.get('tipo')
        descricao = request.POST.get('descricao')
        plano_id = request.POST.get('plano')
        
        if not nome or not tipo or not plano_id:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('criar_projeto')
        
        plano = get_object_or_404(Plano, id=plano_id, ativo=True)
        
        with transaction.atomic():
            projeto = Projeto.objects.create(
                nome=nome,
                tipo=tipo,
                descricao=descricao,
                plano=plano,
                coordenador=request.user,
                publico=False
            )
            
            MembroProjeto.objects.create(
                projeto=projeto,
                usuario=request.user,
                tipo='coordenador'
            )
        
        set_projeto_ativo(request, projeto.id)
        messages.success(request, f'Projeto "{nome}" criado com sucesso!')
        return redirect('dashboard_coordenador')
    
    planos = Plano.objects.filter(ativo=True)
    return render(request, 'projetos/criar_projeto.html', {'planos': planos})


@login_required
def entrar_projeto(request, projeto_id):
    """Entra em um projeto (redireciona para a dashboard correta)."""
    projeto = get_object_or_404(Projeto, id=projeto_id, ativo=True)
    membro = get_object_or_404(MembroProjeto, projeto=projeto, usuario=request.user, ativo=True)
    
    set_projeto_ativo(request, projeto.id)
    
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


# =========== FUNÇÃO AUXILIAR ===========
def get_projeto_ativo(request):
    projeto_id = request.session.get('projeto_id')
    if projeto_id:
        try:
            projeto = Projeto.objects.get(id=projeto_id, ativo=True)
            if MembroProjeto.objects.filter(projeto=projeto, usuario=request.user, ativo=True).exists():
                return projeto
        except Projeto.DoesNotExist:
            pass
    return None

def set_projeto_ativo(request, projeto_id):
    request.session['projeto_id'] = projeto_id


# =========== GERENCIAMENTO DE MEMBROS ===========

@login_required
@perfil_required('coordenador')
def convidar_membro(request):
    """Coordenador convida um novo membro para o projeto."""
    if request.method == 'POST':
        email = request.POST.get('email')
        tipo = request.POST.get('tipo')
        projeto = get_projeto_ativo(request)
        
        if not projeto:
            messages.error(request, 'Nenhum projeto ativo.')
            return redirect('dashboard_coordenador')
        
        # Verifica se o coordenador é deste projeto
        if projeto.coordenador != request.user:
            messages.error(request, 'Você não tem permissão para gerenciar este projeto.')
            return redirect('dashboard_coordenador')
        
        try:
            user = User.objects.get(email=email)
            if MembroProjeto.objects.filter(projeto=projeto, usuario=user).exists():
                messages.error(request, 'Este usuário já é membro do projeto.')
                return redirect('coordenador_membros')
            
            MembroProjeto.objects.create(projeto=projeto, usuario=user, tipo=tipo)
            messages.success(request, f'Usuário {user.get_full_name()} adicionado ao projeto.')
            
        except User.DoesNotExist:
            token = uuid.uuid4().hex
            expiracao = timezone.now() + timedelta(days=7)
            ConviteProjeto.objects.create(
                projeto=projeto,
                email=email,
                tipo_membro=tipo,
                token=token,
                expiracao=expiracao
            )
            
            link = request.build_absolute_uri(f'/projetos/aceitar-convite/{token}/')
            send_mail(
                'Convite para o Projeto REABITECH',
                f'''Você foi convidado para participar do projeto "{projeto.nome}".
                
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
        
        return redirect('coordenador_membros')
    
    return redirect('dashboard_coordenador')


def aceitar_convite(request, token):
    """Aceita um convite e cria o usuário se necessário."""
    convite = get_object_or_404(ConviteProjeto, token=token, aceito=False)
    
    if convite.expiracao < timezone.now():
        messages.error(request, 'Este convite expirou. Solicite um novo convite ao coordenador.')
        return redirect('landing')
    
    if request.method == 'POST':
        senha = request.POST.get('senha')
        senha_confirm = request.POST.get('senha_confirm')
        
        if not senha or len(senha) < 6:
            messages.error(request, 'A senha deve ter pelo menos 6 caracteres.')
            return render(request, 'projetos/aceitar_convite.html', {'convite': convite})
        
        if senha != senha_confirm:
            messages.error(request, 'As senhas não coincidem.')
            return render(request, 'projetos/aceitar_convite.html', {'convite': convite})
        
        with transaction.atomic():
            username = convite.email.split('@')[0] + str(uuid.uuid4().hex[:4])
            user = User.objects.create_user(
                username=username,
                email=convite.email,
                password=senha,
                first_name=request.POST.get('first_name', ''),
                last_name=request.POST.get('last_name', ''),
            )
            
            Perfil.objects.create(usuario=user, tipo=convite.tipo_membro, senha_temporaria=False)
            
            if convite.tipo_membro == 'atleta':
                rm = request.POST.get('rm', '')
                if not rm:
                    messages.error(request, 'Atletas precisam informar o RM.')
                    user.delete()
                    return render(request, 'projetos/aceitar_convite.html', {'convite': convite})
                Atleta.objects.create(usuario=user, rm=rm)
            
            MembroProjeto.objects.create(
                projeto=convite.projeto,
                usuario=user,
                tipo=convite.tipo_membro
            )
            
            convite.aceito = True
            convite.save()
        
        user_auth = authenticate(request, username=user.username, password=senha)
        if user_auth:
            login(request, user_auth)
            set_projeto_ativo(request, convite.projeto.id)
            messages.success(request, 'Conta criada com sucesso! Bem-vindo ao REABITECH.')
            return redirect('dashboard')
    
    return render(request, 'projetos/aceitar_convite.html', {'convite': convite})