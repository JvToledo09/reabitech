from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg
from datetime import datetime
from usuarios.models import Perfil, Atleta
from fisioterapia.models import Lesao, EvolucaoFisica, TratamentoFisioterapico, ExercicioRecuperacao
from psicologia.models import AvaliacaoPsicologica

def home(request):
    return render(request, 'dashboard/home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if '@' in username:
                if hasattr(user, 'perfil'):
                    if user.perfil.tipo in ['coordenador', 'tecnico', 'estagiario_fisio', 'estagiario_psico']:
                        messages.success(request, f'Bem-vindo(a), {user.get_full_name() or user.username}!')
                    else:
                        messages.error(request, 'Email não autorizado.')
                        return redirect('login')
                else:
                    messages.error(request, 'Perfil não encontrado.')
                    return redirect('login')
            else:
                if hasattr(user, 'perfil') and user.perfil.tipo == 'atleta':
                    messages.success(request, f'Bem-vindo, Atleta {user.get_full_name() or user.username}!')
                else:
                    messages.error(request, 'Apenas atletas podem acessar com RM.')
                    return redirect('login')
            
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    
    return render(request, 'dashboard/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'Você saiu do sistema.')
    return redirect('home')

@login_required
def dashboard(request):
    perfil = request.user.perfil
    context = {}
    
    if perfil.tipo == 'coordenador':
        context = {
            'total_atletas': Atleta.objects.count(),
            'lesoes_ativas': Lesao.objects.filter(tratamentos__ativo=True).distinct().count(),
            'taxa_recuperacao_media': 85,
            'total_avaliacoes_psico': AvaliacaoPsicologica.objects.count(),
        }
        
    elif perfil.tipo == 'tecnico':
        meus_atletas = Atleta.objects.filter(tecnico_responsavel=request.user)
        context = {
            'meus_atletas': meus_atletas,
            'total_meus_atletas': meus_atletas.count(),
            'meus_atletas_lesionados': meus_atletas.filter(lesoes__tratamentos__ativo=True).distinct().count(),
            'desempenho_medio': 7,
        }
        
    elif perfil.tipo == 'atleta':
        atleta = request.user.atleta
        evolucoes = EvolucaoFisica.objects.filter(atleta=atleta).order_by('-data_registro')[:5]
        exercicios = ExercicioRecuperacao.objects.filter(tratamento__lesao__atleta=atleta, tratamento__ativo=True)[:3]
        avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=atleta).order_by('-data')[:5]
        
        context = {
            'atleta': atleta,
            'evolucoes': evolucoes,
            'exercicios': exercicios,
            'avaliacoes_psico': avaliacoes,
            'progresso_recuperacao': 75,
            'ultimo_desempenho': 7,
            'score_mental': 8,
            'status_mental': 'Bom',
        }
        
    elif perfil.tipo in ['estagiario_fisio', 'estagiario_psico']:
        context = {
            'atletas_em_atendimento': Atleta.objects.filter(lesoes__tratamentos__ativo=True).distinct(),
            'total_atendimentos': TratamentoFisioterapico.objects.filter(ativo=True).count(),
        }
    
    return render(request, 'dashboard/dashboard.html', context)


# ========== VIEWS DO COORDENADOR ==========
@login_required
def coordenador_atletas(request):
    if request.user.perfil.tipo != 'coordenador':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('dashboard')
    atletas = Atleta.objects.all()
    return render(request, 'dashboard/coordenador/atletas.html', {'atletas': atletas})

@login_required
def coordenador_fisioterapia(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    return render(request, 'dashboard/coordenador/fisioterapia.html')

@login_required
def coordenador_psicologia(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    return render(request, 'dashboard/coordenador/psicologia.html')

@login_required
def coordenador_relatorios(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    return render(request, 'dashboard/coordenador/relatorios.html')


# ========== VIEWS DO TÉCNICO ==========
@login_required
def tecnico_atletas(request):
    if request.user.perfil.tipo != 'tecnico':
        return redirect('dashboard')
    atletas = Atleta.objects.filter(tecnico_responsavel=request.user)
    return render(request, 'dashboard/tecnico/atletas.html', {'atletas': atletas})

@login_required
def tecnico_desempenho(request):
    return render(request, 'dashboard/tecnico/desempenho.html')

@login_required
def tecnico_recuperacao(request):
    return render(request, 'dashboard/tecnico/recuperacao.html')


# ========== VIEWS DO ATLETA ==========
@login_required
def atleta_recuperacao(request):
    if request.user.perfil.tipo != 'atleta':
        return redirect('dashboard')
    atleta = request.user.atleta
    evolucoes = EvolucaoFisica.objects.filter(atleta=atleta).order_by('-data_registro')
    lesoes = Lesao.objects.filter(atleta=atleta)
    return render(request, 'dashboard/atleta/recuperacao.html', {'evolucoes': evolucoes, 'lesoes': lesoes})

@login_required
def atleta_psicologico(request):
    if request.user.perfil.tipo != 'atleta':
        return redirect('dashboard')
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=request.user.atleta).order_by('-data')
    return render(request, 'dashboard/atleta/psicologico.html', {'avaliacoes': avaliacoes})

@login_required
def atleta_exercicios(request):
    if request.user.perfil.tipo != 'atleta':
        return redirect('dashboard')
    exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=request.user.atleta,
        tratamento__ativo=True
    )
    return render(request, 'dashboard/atleta/exercicios.html', {'exercicios': exercicios})


# ========== VIEWS DOS ESTAGIÁRIOS ==========
@login_required
def estagiario_atletas(request):
    if request.user.perfil.tipo not in ['estagiario_fisio', 'estagiario_psico']:
        return redirect('dashboard')
    return render(request, 'dashboard/estagiario/atletas.html')

@login_required
def estagiario_fisioterapia(request):
    if request.user.perfil.tipo != 'estagiario_fisio':
        return redirect('dashboard')
    return render(request, 'dashboard/estagiario/fisioterapia.html')

@login_required
def estagiario_psicologia(request):
    if request.user.perfil.tipo != 'estagiario_psico':
        return redirect('dashboard')
    return render(request, 'dashboard/estagiario/psicologia.html')

@login_required
def estagiario_relatorios(request):
    if request.user.perfil.tipo not in ['estagiario_fisio', 'estagiario_psico']:
        return redirect('dashboard')
    return render(request, 'dashboard/estagiario/relatorios.html')

@login_required
def estagiario_agenda(request):
    if request.user.perfil.tipo not in ['estagiario_fisio', 'estagiario_psico']:
        return redirect('dashboard')
    return render(request, 'dashboard/estagiario/agenda.html')