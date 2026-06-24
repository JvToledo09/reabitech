from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from .models import Projeto, Plano, Parceria, ProfissionalProjeto, AtletaProjeto
from usuarios.models import Perfil, Atleta
from datetime import datetime, timedelta

def landing_page(request):
    """Página inicial com projetos parceiros e planos"""
    planos = Plano.objects.all()
    projetos_parceiros = Projeto.objects.filter(status='ativo', ativo=True)
    return render(request, 'projetos/index.html', {
        'planos': planos,
        'projetos_parceiros': projetos_parceiros,
    })

def selecionar_projeto(request):
    """Tela para selecionar ou criar um projeto"""
    if request.user.is_authenticated:
        projetos = []
        if hasattr(request.user, 'perfil'):
            if request.user.perfil.tipo == 'coordenador':
                projetos = Projeto.objects.filter(coordenador=request.user, status='ativo')
            elif request.user.perfil.tipo == 'tecnico':
                profissionais = ProfissionalProjeto.objects.filter(usuario=request.user, ativo=True)
                projetos = [p.projeto for p in profissionais if p.projeto.status == 'ativo']
            elif request.user.perfil.tipo == 'atleta':
                atleta_projetos = AtletaProjeto.objects.filter(atleta__usuario=request.user, ativo=True)
                projetos = [a.projeto for a in atleta_projetos if a.projeto.status == 'ativo']
        
        if len(projetos) == 1:
            request.session['projeto_atual'] = projetos[0].id
            return redirect('dashboard')
        elif len(projetos) > 1:
            return render(request, 'projetos/selecionar.html', {'projetos': projetos})
    
    return redirect('login')

def nova_parceria(request):
    """Formulário para solicitar nova parceria"""
    if request.method == 'POST':
        nome_projeto = request.POST.get('nome_projeto')
        nome_parceiro = request.POST.get('nome_parceiro')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        plano_id = request.POST.get('plano')
        mensagem = request.POST.get('mensagem')
        
        plano = None
        if plano_id:
            plano = get_object_or_404(Plano, id=plano_id)
        
        parceria = Parceria.objects.create(
            nome_projeto=nome_projeto,
            nome_parceiro=nome_parceiro,
            email=email,
            telefone=telefone,
            plano_interesse=plano,
            mensagem=mensagem,
            status='pendente'
        )
        
        messages.success(request, 'Solicitação de parceria enviada com sucesso! Entraremos em contato em breve.')
        return redirect('landing_page')
    
    planos = Plano.objects.all()
    return render(request, 'projetos/nova_parceria.html', {'planos': planos})

@login_required
def criar_projeto(request):
    """Criar um novo projeto (apenas coordenador)"""
    if request.user.perfil.tipo != 'coordenador':
        messages.error(request, 'Apenas coordenadores podem criar projetos.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        email_contato = request.POST.get('email_contato')
        plano_id = request.POST.get('plano')
        
        plano = get_object_or_404(Plano, id=plano_id)
        
        projeto = Projeto.objects.create(
            nome=nome,
            slug=nome.lower().replace(' ', '-'),
            descricao=descricao,
            plano=plano,
            coordenador=request.user,
            status='ativo',
            email_contato=email_contato,
            data_vencimento=datetime.now().date() + timedelta(days=30)
        )
        
        messages.success(request, f'Projeto {nome} criado com sucesso!')
        return redirect('selecionar_projeto')
    
    planos = Plano.objects.all()
    return render(request, 'projetos/criar.html', {'planos': planos})

@login_required
def projeto_dashboard(request, projeto_id):
    """Dashboard específico de um projeto"""
    projeto = get_object_or_404(Projeto, id=projeto_id, ativo=True)
    
    if not tem_acesso_projeto(request.user, projeto):
        messages.error(request, 'Você não tem acesso a este projeto.')
        return redirect('selecionar_projeto')
    
    request.session['projeto_atual'] = projeto.id
    return redirect('dashboard')

def tem_acesso_projeto(usuario, projeto):
    """Verifica se um usuário tem acesso a um projeto"""
    if not usuario.is_authenticated:
        return False
    
    if not hasattr(usuario, 'perfil'):
        return False
    
    if usuario.perfil.tipo == 'coordenador':
        return projeto.coordenador == usuario
    
    if usuario.perfil.tipo == 'tecnico':
        return ProfissionalProjeto.objects.filter(projeto=projeto, usuario=usuario, ativo=True).exists()
    
    if usuario.perfil.tipo == 'atleta':
        return AtletaProjeto.objects.filter(projeto=projeto, atleta__usuario=usuario, ativo=True).exists()
    
    if usuario.perfil.tipo in ['estagiario_fisio', 'estagiario_psico']:
        return ProfissionalProjeto.objects.filter(projeto=projeto, usuario=usuario, ativo=True).exists()
    
    return False

def login_projeto(request, projeto_id):
    """Tela de login específica para um projeto parceiro"""
    projeto = get_object_or_404(Projeto, id=projeto_id, ativo=True)
    
    if request.user.is_authenticated:
        if tem_acesso_projeto(request.user, projeto):
            request.session['projeto_atual'] = projeto.id
            return redirect('dashboard')
        else:
            messages.warning(request, 'Você não tem acesso a este projeto.')
            return redirect('landing_page')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not hasattr(user, 'perfil'):
                messages.error(request, 'Usuário sem perfil definido. Contate o administrador.')
                return render(request, 'projetos/login_projeto.html', {'projeto': projeto})
            
            if tem_acesso_projeto(user, projeto):
                login(request, user)
                request.session['projeto_atual'] = projeto.id
                
                if user.perfil.tipo == 'coordenador':
                    messages.success(request, f'Bem-vindo, Coordenador {user.get_full_name() or user.username}!')
                elif user.perfil.tipo == 'tecnico':
                    messages.success(request, f'Bem-vindo, Técnico {user.get_full_name() or user.username}!')
                elif user.perfil.tipo == 'atleta':
                    messages.success(request, f'Bem-vindo, Atleta {user.get_full_name() or user.username}!')
                elif user.perfil.tipo in ['estagiario_fisio', 'estagiario_psico']:
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                else:
                    messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')
                
                return redirect('dashboard')
            else:
                messages.error(request, 'Você não tem acesso a este projeto.')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'projetos/login_projeto.html', {'projeto': projeto})