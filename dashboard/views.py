from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q

# Models do projeto
from usuarios.models import Perfil, Atleta
from fisioterapia.models import Lesao, EvolucaoFisica, TratamentoFisioterapico, ExercicioRecuperacao
from psicologia.models import AvaliacaoPsicologica
from projetos.models import Projeto, MembroProjeto   # <-- NOVO

# Decorator de permissão
from usuarios.decorators import perfil_required


# ==============================================
# UTILITÁRIO: Projeto ativo na sessão
# ==============================================
def get_projeto_ativo(request):
    """
    Retorna o projeto ativo da sessão, se existir e se o usuário for membro.
    """
    projeto_id = request.session.get('projeto_id')
    if projeto_id:
        try:
            projeto = Projeto.objects.get(id=projeto_id, ativo=True)
            # Verifica se o usuário é membro deste projeto
            if MembroProjeto.objects.filter(projeto=projeto, usuario=request.user, ativo=True).exists():
                return projeto
        except Projeto.DoesNotExist:
            pass
    return None


def set_projeto_ativo(request, projeto_id):
    """Define o projeto ativo na sessão."""
    request.session['projeto_id'] = projeto_id


# ==============================================
# 1. LOGIN (aceita RM ou E-mail)
# ==============================================
def login_view(request):
    if request.method == 'POST':
        login_input = request.POST.get('username')
        password = request.POST.get('password')
        user = None

        if '@' in login_input:
            try:
                user_obj = User.objects.get(email=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        else:
            try:
                atleta = Atleta.objects.get(rm=login_input)
                user = authenticate(request, username=atleta.usuario.username, password=password)
            except Atleta.DoesNotExist:
                user = None

        if user is not None:
            auth_login(request, user)

            # Após login, tenta definir um projeto ativo
            # Se o usuário for coordenador e tiver vários projetos, deixamos sem projeto (será escolhido depois)
            membros = MembroProjeto.objects.filter(usuario=user, ativo=True)
            if membros.count() == 1:
                set_projeto_ativo(request, membros.first().projeto.id)
            elif membros.count() > 1:
                # Se for coordenador, redireciona para uma tela de escolha (opcional)
                # Por enquanto, não define projeto ativo
                pass

            if hasattr(user, 'perfil'):
                tipo = user.perfil.tipo
                if tipo == 'atleta':
                    messages.success(request, f'Bem-vindo, Atleta {user.get_full_name() or user.username}!')
                    return redirect('dashboard_atleta')
                elif tipo == 'tecnico':
                    messages.success(request, f'Bem-vindo, Técnico {user.get_full_name() or user.username}!')
                    return redirect('dashboard_tecnico')
                elif tipo == 'coordenador':
                    messages.success(request, f'Bem-vindo, Coordenador {user.get_full_name() or user.username}!')
                    return redirect('dashboard_coordenador')
                elif tipo == 'fisioterapeuta':
                    messages.success(request, f'Bem-vindo, Fisioterapeuta {user.get_full_name() or user.username}!')
                    return redirect('dashboard_fisioterapeuta')
                elif tipo == 'psicologo':
                    messages.success(request, f'Bem-vindo, Psicólogo {user.get_full_name() or user.username}!')
                    return redirect('dashboard_psicologo')
                else:
                    return redirect('dashboard')
            else:
                messages.warning(request, 'Perfil não definido. Contate o administrador.')
                return redirect('dashboard')
        else:
            messages.error(request, 'RM/E-mail ou senha inválidos.')

    return render(request, 'dashboard/login.html')


# ==============================================
# 2. LOGOUT
# ==============================================
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, 'Você saiu do sistema.')
    return redirect('landing')   # Redireciona para a landing page (app projetos)


# ==============================================
# 3. DASHBOARD GENÉRICA (REDIRECIONA)
# ==============================================
@login_required
def dashboard(request):
    if hasattr(request.user, 'perfil'):
        tipo = request.user.perfil.tipo
        if tipo == 'atleta':
            return redirect('dashboard_atleta')
        elif tipo == 'tecnico':
            return redirect('dashboard_tecnico')
        elif tipo == 'coordenador':
            return redirect('dashboard_coordenador')
        elif tipo == 'fisioterapeuta':
            return redirect('dashboard_fisioterapeuta')
        elif tipo == 'psicologo':
            return redirect('dashboard_psicologo')
    return render(request, 'dashboard/dashboard.html')


# ==============================================
# 4. DASHBOARDS ESPECÍFICAS POR PERFIL
# ==============================================

@login_required
@perfil_required('atleta')
def dashboard_atleta(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo. Selecione um projeto.')
        # Redireciona para uma tela de escolha de projetos (criar depois)
        return redirect('landing')

    atleta = request.user.atleta
    # Filtra evoluções, exercícios e avaliações apenas deste projeto
    evolucoes = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_registro')[:5]
    exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=atleta,
        tratamento__ativo=True,
        tratamento__lesao__projeto=projeto
    )[:3]
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data')[:5]

    context = {
        'atleta': atleta,
        'projeto': projeto,
        'evolucoes': evolucoes,
        'exercicios': exercicios,
        'avaliacoes_psico': avaliacoes,
        'progresso_recuperacao': 75,
        'ultimo_desempenho': 7,
        'score_mental': 8,
        'status_mental': 'Bom',
    }
    return render(request, 'dashboard/atleta/dashboard.html', context)


@login_required
@perfil_required('tecnico')
def dashboard_tecnico(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    meus_atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        membros_projeto__projeto=projeto
    )
    total = meus_atletas.count()
    lesionados = meus_atletas.filter(lesoes__tratamentos__ativo=True).distinct().count()

    context = {
        'projeto': projeto,
        'meus_atletas': meus_atletas,
        'total_meus_atletas': total,
        'meus_atletas_lesionados': lesionados,
        'desempenho_medio': 7.2,
    }
    return render(request, 'dashboard/tecnico/dashboard.html', context)


@login_required
@perfil_required('coordenador')
def dashboard_coordenador(request):
    # O coordenador vê todos os seus projetos
    projetos = Projeto.objects.filter(coordenador=request.user, ativo=True)
    if not projetos:
        messages.info(request, 'Você não possui nenhum projeto ativo. Crie um novo.')
        return redirect('criar_projeto')

    # Se não houver projeto ativo na sessão, define o primeiro
    if not request.session.get('projeto_id') and projetos.exists():
        set_projeto_ativo(request, projetos.first().id)

    projeto = get_projeto_ativo(request)

    context = {
        'projetos': projetos,
        'projeto_ativo': projeto,
        'total_atletas': Atleta.objects.filter(membros_projeto__projeto=projeto).count() if projeto else 0,
        'lesoes_ativas': Lesao.objects.filter(tratamentos__ativo=True, projeto=projeto).distinct().count() if projeto else 0,
        'total_avaliacoes_psico': AvaliacaoPsicologica.objects.filter(projeto=projeto).count() if projeto else 0,
        'taxa_recuperacao_media': 85,
    }
    return render(request, 'dashboard/coordenador/dashboard.html', context)


@login_required
@perfil_required('fisioterapeuta')
def dashboard_fisioterapeuta(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    atletas = Atleta.objects.filter(membros_projeto__projeto=projeto, lesoes__tratamentos__ativo=True).distinct()
    tratamentos_ativos = TratamentoFisioterapico.objects.filter(ativo=True, lesao__projeto=projeto).count()

    context = {
        'projeto': projeto,
        'atletas_em_atendimento': atletas,
        'total_tratamentos_ativos': tratamentos_ativos,
    }
    return render(request, 'dashboard/fisioterapeuta/dashboard.html', context)


@login_required
@perfil_required('psicologo')
def dashboard_psicologo(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).order_by('-data')[:10]
    total_avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).count()

    context = {
        'projeto': projeto,
        'avaliacoes_recentes': avaliacoes,
        'total_avaliacoes': total_avaliacoes,
    }
    return render(request, 'dashboard/psicologo/dashboard.html', context)


# ==============================================
# 5. VIEWS DO COORDENADOR
# ==============================================

@login_required
@perfil_required('coordenador')
def coordenador_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    atletas = Atleta.objects.filter(membros_projeto__projeto=projeto)
    return render(request, 'dashboard/coordenador/atletas.html', {'atletas': atletas, 'projeto': projeto})


@login_required
@perfil_required('coordenador')
def coordenador_fisioterapia(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    lesoes = Lesao.objects.filter(projeto=projeto)
    return render(request, 'dashboard/coordenador/fisioterapia.html', {'lesoes': lesoes, 'projeto': projeto})


@login_required
@perfil_required('coordenador')
def coordenador_psicologia(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto)
    return render(request, 'dashboard/coordenador/psicologia.html', {'avaliacoes': avaliacoes, 'projeto': projeto})


@login_required
@perfil_required('coordenador')
def coordenador_relatorios(request):
    projeto = get_projeto_ativo(request)
    return render(request, 'dashboard/coordenador/relatorios.html', {'projeto': projeto})


# ==============================================
# 6. VIEWS DO TÉCNICO
# ==============================================

@login_required
@perfil_required('tecnico')
def tecnico_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    atletas = Atleta.objects.filter(tecnico_responsavel=request.user, membros_projeto__projeto=projeto)
    return render(request, 'dashboard/tecnico/atletas.html', {'atletas': atletas, 'projeto': projeto})


@login_required
@perfil_required('tecnico')
def tecnico_desempenho(request):
    projeto = get_projeto_ativo(request)
    return render(request, 'dashboard/tecnico/desempenho.html', {'projeto': projeto})


@login_required
@perfil_required('tecnico')
def tecnico_recuperacao(request):
    projeto = get_projeto_ativo(request)
    return render(request, 'dashboard/tecnico/recuperacao.html', {'projeto': projeto})


# ==============================================
# 7. VIEWS DO ATLETA
# ==============================================

@login_required
@perfil_required('atleta')
def atleta_recuperacao(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    atleta = request.user.atleta
    evolucoes = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_registro')
    lesoes = Lesao.objects.filter(atleta=atleta, projeto=projeto)
    return render(request, 'dashboard/atleta/recuperacao.html', {
        'evolucoes': evolucoes,
        'lesoes': lesoes,
        'projeto': projeto,
    })


@login_required
@perfil_required('atleta')
def atleta_psicologico(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=request.user.atleta, projeto=projeto).order_by('-data')
    return render(request, 'dashboard/atleta/psicologico.html', {'avaliacoes': avaliacoes, 'projeto': projeto})


@login_required
@perfil_required('atleta')
def atleta_exercicios(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=request.user.atleta,
        tratamento__ativo=True,
        tratamento__lesao__projeto=projeto
    )
    return render(request, 'dashboard/atleta/exercicios.html', {'exercicios': exercicios, 'projeto': projeto})


# ==============================================
# 8. VIEWS DO FISIOTERAPEUTA
# ==============================================

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    atletas = Atleta.objects.filter(membros_projeto__projeto=projeto, lesoes__tratamentos__ativo=True).distinct()
    return render(request, 'dashboard/fisioterapeuta/atletas.html', {'atletas': atletas, 'projeto': projeto})


@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_tratamentos(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    tratamentos = TratamentoFisioterapico.objects.filter(ativo=True, lesao__projeto=projeto)
    return render(request, 'dashboard/fisioterapeuta/tratamentos.html', {'tratamentos': tratamentos, 'projeto': projeto})


@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_evolucoes(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    evolucoes = EvolucaoFisica.objects.filter(projeto=projeto).order_by('-data_registro')[:20]
    return render(request, 'dashboard/fisioterapeuta/evolucoes.html', {'evolucoes': evolucoes, 'projeto': projeto})


# ==============================================
# 9. VIEWS DO PSICÓLOGO
# ==============================================

@login_required
@perfil_required('psicologo')
def psicologo_avaliacoes(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).order_by('-data')
    return render(request, 'dashboard/psicologo/avaliacoes.html', {'avaliacoes': avaliacoes, 'projeto': projeto})


@login_required
@perfil_required('psicologo')
def psicologo_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')
    atletas = Atleta.objects.filter(avaliacaopsicologica__isnull=False, membros_projeto__projeto=projeto).distinct()
    return render(request, 'dashboard/psicologo/atletas.html', {'atletas': atletas, 'projeto': projeto})