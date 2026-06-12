from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta
from usuarios.models import Perfil, Atleta, ModalidadeEsportiva
from fisioterapia.models import Lesao, EvolucaoFisica, TratamentoFisioterapico, ExercicioRecuperacao
from psicologia.models import AvaliacaoPsicologica, QuestionarioPeriodico

def home(request):
    return render(request, 'dashboard/home.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Verificar se o usuário existe
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Verificar o tipo de login baseado no formato do username
            if '@' in username:
                # Login com EMAIL - Profissionais (Coordenador, Técnico, Estagiários)
                if hasattr(user, 'perfil'):
                    if user.perfil.tipo == 'coordenador':
                        messages.success(request, f'Bem-vindo, Coordenador {user.get_full_name() or user.username}!')
                    elif user.perfil.tipo == 'tecnico':
                        messages.success(request, f'Bem-vindo, Técnico {user.get_full_name() or user.username}!')
                    elif user.perfil.tipo == 'estagiario_fisio':
                        messages.success(request, f'Bem-vindo, Estagiário de Fisioterapia {user.get_full_name() or user.username}!')
                    elif user.perfil.tipo == 'estagiario_psico':
                        messages.success(request, f'Bem-vindo, Estagiário de Psicologia {user.get_full_name() or user.username}!')
                    else:
                        messages.error(request, 'Email não autorizado para acesso profissional.')
                        return redirect('login')
                else:
                    messages.error(request, 'Perfil não encontrado para este email.')
                    return redirect('login')
            else:
                # Login com RM - Somente ATLETA
                if hasattr(user, 'perfil') and user.perfil.tipo == 'atleta':
                    messages.success(request, f'Bem-vindo, Atleta {user.get_full_name() or user.username}!')
                else:
                    messages.error(request, 'RM inválido. Apenas atletas podem acessar com RM.')
                    return redirect('login')
            
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuário ou senha inválidos. Verifique suas credenciais.')
    
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
        total_atletas = Atleta.objects.count()
        atletas_ativos = Atleta.objects.filter(usuario__is_active=True).count()
        total_lesoes = Lesao.objects.count()
        lesoes_ativas = Lesao.objects.filter(tratamentos__ativo=True).distinct().count()
        total_avaliacoes_psico = AvaliacaoPsicologica.objects.count()
        
        evolucoes_recentes = EvolucaoFisica.objects.all().order_by('-data_registro')[:10]
        taxa_recuperacao_media = 75
        if evolucoes_recentes:
            total = 0
            for ev in evolucoes_recentes:
                total += ev.percentual_recuperacao
            taxa_recuperacao_media = int(total / len(evolucoes_recentes))
        
        modalidades_count = Atleta.objects.values('modalidade__nome').annotate(total=Count('id'))
        ultimos_atletas = Atleta.objects.all().order_by('-data_ingresso')[:5]
        proximos_tratamentos = TratamentoFisioterapico.objects.filter(
            ativo=True, 
            data_previsao_termino__gte=datetime.now().date()
        ).order_by('data_previsao_termino')[:5]
        
        context = {
            'total_atletas': total_atletas,
            'atletas_ativos': atletas_ativos,
            'total_lesoes': total_lesoes,
            'lesoes_ativas': lesoes_ativas,
            'total_avaliacoes_psico': total_avaliacoes_psico,
            'taxa_recuperacao_media': taxa_recuperacao_media,
            'modalidades_count': list(modalidades_count),
            'ultimos_atletas': ultimos_atletas,
            'proximos_tratamentos': proximos_tratamentos,
            'evolucoes_recentes': evolucoes_recentes,
        }
        
    elif perfil.tipo == 'tecnico':
        meus_atletas = Atleta.objects.filter(tecnico_responsavel=request.user)
        total_meus_atletas = meus_atletas.count()
        meus_atletas_lesionados = meus_atletas.filter(lesoes__tratamentos__ativo=True).distinct().count()
        
        desempenho_medio = 0
        evolucoes = EvolucaoFisica.objects.filter(atleta__in=meus_atletas)
        if evolucoes:
            total = 0
            for ev in evolucoes:
                total += ev.desempenho
            desempenho_medio = int(total / len(evolucoes))
        
        context = {
            'meus_atletas': meus_atletas,
            'total_meus_atletas': total_meus_atletas,
            'meus_atletas_lesionados': meus_atletas_lesionados,
            'desempenho_medio': desempenho_medio,
        }
        
    elif perfil.tipo == 'atleta':
        atleta = request.user.atleta
        evolucoes = EvolucaoFisica.objects.filter(atleta=atleta).order_by('-data_registro')[:10]
        ultima_evolucao = evolucoes.first()
        
        lesoes = Lesao.objects.filter(atleta=atleta)
        lesoes_ativas = lesoes.filter(tratamentos__ativo=True)
        tratamentos_ativos = TratamentoFisioterapico.objects.filter(lesao__atleta=atleta, ativo=True)
        exercicios = ExercicioRecuperacao.objects.filter(tratamento__lesao__atleta=atleta, tratamento__ativo=True)[:5]
        
        avaliacoes_psico = AvaliacaoPsicologica.objects.filter(atleta=atleta).order_by('-data')[:5]
        ultima_avaliacao = avaliacoes_psico.first()
        
        if ultima_evolucao:
            progresso_recuperacao = ultima_evolucao.percentual_recuperacao
            ultimo_desempenho = ultima_evolucao.desempenho
        else:
            progresso_recuperacao = 0
            ultimo_desempenho = 0
        
        if ultima_avaliacao:
            score_mental = ultima_avaliacao.score_total
            status_mental = ultima_avaliacao.status_emocional
        else:
            score_mental = 0
            status_mental = "Não avaliado"
        
        context = {
            'atleta': atleta,
            'evolucoes': evolucoes,
            'ultima_evolucao': ultima_evolucao,
            'lesoes': lesoes,
            'lesoes_ativas': lesoes_ativas,
            'tratamentos_ativos': tratamentos_ativos,
            'exercicios': exercicios,
            'avaliacoes_psico': avaliacoes_psico,
            'progresso_recuperacao': progresso_recuperacao,
            'ultimo_desempenho': ultimo_desempenho,
            'score_mental': score_mental,
            'status_mental': status_mental,
        }
        
    elif perfil.tipo == 'estagiario_fisio':
        atletas_em_atendimento = Atleta.objects.filter(lesoes__tratamentos__ativo=True).distinct()
        total_atendimentos = TratamentoFisioterapico.objects.filter(ativo=True).count()
        context = {
            'atletas_em_atendimento': atletas_em_atendimento,
            'total_atendimentos': total_atendimentos,
        }
        
    elif perfil.tipo == 'estagiario_psico':
        atletas_com_avaliacao = Atleta.objects.filter(avaliacoes_psicologicas__isnull=False).distinct()
        total_avaliacoes = AvaliacaoPsicologica.objects.count()
        context = {
            'atletas_com_avaliacao': atletas_com_avaliacao,
            'total_avaliacoes': total_avaliacoes,
        }
    
    return render(request, 'dashboard/dashboard.html', context)


# ========== VIEWS DO COORDENADOR ==========
@login_required
def coordenador_atletas(request):
    if request.user.perfil.tipo != 'coordenador':
        messages.error(request, 'Acesso não autorizado.')
        return redirect('dashboard')
    atletas = Atleta.objects.all().select_related('usuario', 'modalidade')
    return render(request, 'dashboard/coordenador/atletas.html', {'atletas': atletas})

@login_required
def coordenador_fisioterapia(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    lesoes = Lesao.objects.all().select_related('atleta__usuario')
    return render(request, 'dashboard/coordenador/fisioterapia.html', {'lesoes': lesoes})

@login_required
def coordenador_psicologia(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    avaliacoes = AvaliacaoPsicologica.objects.all().select_related('atleta__usuario')
    return render(request, 'dashboard/coordenador/psicologia.html', {'avaliacoes': avaliacoes})

@login_required
def coordenador_relatorios(request):
    if request.user.perfil.tipo != 'coordenador':
        return redirect('dashboard')
    total_atletas = Atleta.objects.count()
    total_lesoes = Lesao.objects.count()
    total_avaliacoes = AvaliacaoPsicologica.objects.count()
    return render(request, 'dashboard/coordenador/relatorios.html', {
        'total_atletas': total_atletas,
        'total_lesoes': total_lesoes,
        'total_avaliacoes': total_avaliacoes,
    })


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
    return render(request, 'dashboard/atleta/recuperacao.html', {'evolucoes': evolucoes, 'lesoes': lesoes, 'atleta': atleta})

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