from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Avg
from datetime import datetime

from usuarios.models import Perfil, Atleta, ModalidadeEsportiva
from fisioterapia.models import Lesao, EvolucaoFisica, TratamentoFisioterapico, ExercicioRecuperacao
from psicologia.models import AvaliacaoPsicologica, QuestionarioPeriodico
from projetos.models import Projeto, MembroProjeto
from usuarios.decorators import perfil_required


# ==============================================
# UTILITÁRIO: Projeto ativo na sessão
# ==============================================
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


# ==============================================
# 1. LOGIN (aceita username, email, RM)
# ==============================================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        login_input = request.POST.get('username')
        password = request.POST.get('password')
        user = None

        print(f"🔑 Tentativa de login: {login_input}")

        # 1. Tenta por username (coordenador, tecnico, etc)
        try:
            user_obj = User.objects.get(username=login_input)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                print(f"   ✅ Login via username: {login_input}")
        except User.DoesNotExist:
            pass

        # 2. Tenta por email
        if not user and '@' in login_input:
            try:
                user_obj = User.objects.get(email=login_input)
                user = authenticate(request, username=user_obj.username, password=password)
                if user:
                    print(f"   ✅ Login via email: {login_input}")
            except User.DoesNotExist:
                pass

        # 3. Tenta por RM (atleta)
        if not user:
            try:
                atleta = Atleta.objects.get(rm=login_input)
                user = authenticate(request, username=atleta.usuario.username, password=password)
                if user:
                    print(f"   ✅ Login via RM: {login_input}")
            except Atleta.DoesNotExist:
                print(f"   ❌ RM não encontrado: {login_input}")

        if user is not None:
            auth_login(request, user)

            # Verifica se o usuário tem perfil, se não tiver, cria um padrão
            if not hasattr(user, 'perfil'):
                print(f"   ⚠️ Usuário {user.username} sem perfil. Criando perfil 'atleta'.")
                Perfil.objects.create(usuario=user, tipo='atleta', senha_temporaria=False)

            # Define projeto ativo
            membros = MembroProjeto.objects.filter(usuario=user, ativo=True)
            if membros.count() == 1:
                set_projeto_ativo(request, membros.first().projeto.id)

            # Verifica senha temporária
            if user.perfil.senha_temporaria:
                messages.warning(request, 'Você está usando uma senha temporária. Por favor, altere sua senha.')
                return redirect('alterar_senha')

            tipo = user.perfil.tipo
            messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')

            # Redireciona conforme o perfil
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
            else:
                return redirect('dashboard')
        else:
            print(f"   ❌ Falha no login para: {login_input}")
            messages.error(request, 'RM/E-mail ou senha inválidos.')

    return render(request, 'dashboard/login.html')


# ==============================================
# 2. LOGOUT
# ==============================================
def logout_view(request):
    logout(request)
    request.session.flush()
    messages.info(request, 'Você saiu do sistema.')
    return redirect('landing')


# ==============================================
# 3. DASHBOARD GENÉRICA
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
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # Verifica se o usuário tem um Atleta vinculado
    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Seu perfil de atleta não está configurado. Contate o coordenador.')
        return redirect('dashboard')

    atleta = request.user.atleta

    evolucoes = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_registro')[:5]
    exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=atleta,
        tratamento__ativo=True,
        tratamento__lesao__projeto=projeto
    )[:3]
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data')[:5]
    lesoes = Lesao.objects.filter(atleta=atleta, projeto=projeto, tratamentos__ativo=True).distinct()

    ultima_evolucao = evolucoes.first()
    progresso = ultima_evolucao.percentual_recuperacao if ultima_evolucao else 0

    ultima_avaliacao = avaliacoes.first()
    score_mental = ultima_avaliacao.score_total if ultima_avaliacao else 0
    status_mental = ultima_avaliacao.status_emocional if ultima_avaliacao else "Não avaliado"

    context = {
        'atleta': atleta,
        'projeto': projeto,
        'evolucoes': evolucoes,
        'exercicios': exercicios,
        'avaliacoes': avaliacoes,
        'lesoes': lesoes,
        'progresso_recuperacao': progresso,
        'score_mental': score_mental,
        'status_mental': status_mental,
        'ultimo_desempenho': ultima_evolucao.desempenho if ultima_evolucao else 0,
    }
    return render(request, 'dashboard/atleta/dashboard.html', context)


@login_required
@perfil_required('tecnico')
def dashboard_tecnico(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # CORREÇÃO: Usar subconsulta para evitar erro de OneToOneField
    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    meus_atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        usuario__in=membros_usuario_ids
    ).distinct()
    
    total = meus_atletas.count()
    lesionados = meus_atletas.filter(lesoes__tratamentos__ativo=True).distinct().count()

    desempenho_medio = EvolucaoFisica.objects.filter(
        atleta__in=meus_atletas,
        projeto=projeto
    ).aggregate(Avg('desempenho'))['desempenho__avg'] or 0

    context = {
        'projeto': projeto,
        'meus_atletas': meus_atletas,
        'total_meus_atletas': total,
        'meus_atletas_lesionados': lesionados,
        'desempenho_medio': round(desempenho_medio, 1),
    }
    return render(request, 'dashboard/tecnico/dashboard.html', context)


@login_required
@perfil_required('coordenador')
def dashboard_coordenador(request):
    projetos = Projeto.objects.filter(coordenador=request.user, ativo=True)

    if not projetos:
        messages.info(request, 'Você não possui nenhum projeto ativo. Crie um novo.')
        return redirect('criar_projeto')

    if not request.session.get('projeto_id') and projetos.exists():
        set_projeto_ativo(request, projetos.first().id)

    projeto = get_projeto_ativo(request)

    if projeto:
        # CORREÇÃO: Usar subconsulta para evitar erro de OneToOneField
        membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
        atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()
        
        lesoes_ativas = Lesao.objects.filter(projeto=projeto, tratamentos__ativo=True).distinct().count()
        avaliacoes_psico = AvaliacaoPsicologica.objects.filter(projeto=projeto).count()

        evolucoes = EvolucaoFisica.objects.filter(projeto=projeto)
        if evolucoes.exists():
            taxa_media = sum(e.percentual_recuperacao for e in evolucoes) / evolucoes.count()
        else:
            taxa_media = 0
    else:
        atletas = []
        lesoes_ativas = 0
        avaliacoes_psico = 0
        taxa_media = 0

    context = {
        'projetos': projetos,
        'projeto_ativo': projeto,
        'total_atletas': atletas.count() if projeto else 0,
        'lesoes_ativas': lesoes_ativas,
        'total_avaliacoes_psico': avaliacoes_psico,
        'taxa_recuperacao_media': round(taxa_media, 1),
    }
    return render(request, 'dashboard/coordenador/dashboard.html', context)


@login_required
@perfil_required('fisioterapeuta')
def dashboard_fisioterapeuta(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # CORREÇÃO: Usar subconsulta
    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        usuario__in=membros_usuario_ids,
        lesoes__tratamentos__ativo=True
    ).distinct()

    tratamentos_ativos = TratamentoFisioterapico.objects.filter(
        ativo=True,
        lesao__projeto=projeto
    ).count()

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

    # CORREÇÃO: Usar subconsulta (o "ativo=True" não é obrigatório aqui, apenas para garantir integridade)
    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto).values_list('usuario', flat=True)
    atletas_com_psico = Atleta.objects.filter(
        avaliacoes_psicologicas__isnull=False,
        usuario__in=membros_usuario_ids
    ).distinct().count()

    context = {
        'projeto': projeto,
        'avaliacoes_recentes': avaliacoes,
        'total_avaliacoes': total_avaliacoes,
        'atletas_acompanhados': atletas_com_psico,
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

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()
    
    return render(request, 'dashboard/coordenador/atletas.html', {
        'atletas': atletas,
        'projeto': projeto
    })

@login_required
@perfil_required('coordenador')
def coordenador_fisioterapia(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    lesoes = Lesao.objects.filter(projeto=projeto)
    return render(request, 'dashboard/coordenador/fisioterapia.html', {
        'lesoes': lesoes,
        'projeto': projeto
    })

@login_required
@perfil_required('coordenador')
def coordenador_psicologia(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).order_by('-data')
    return render(request, 'dashboard/coordenador/psicologia.html', {
        'avaliacoes': avaliacoes,
        'projeto': projeto
    })

@login_required
@perfil_required('coordenador')
def coordenador_relatorios(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto).values_list('usuario', flat=True)
    total_atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct().count()
    
    total_lesoes = Lesao.objects.filter(projeto=projeto).count()
    total_avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).count()

    evolucoes = EvolucaoFisica.objects.filter(projeto=projeto)
    taxa_recuperacao = sum(e.percentual_recuperacao for e in evolucoes) / evolucoes.count() if evolucoes.exists() else 0

    context = {
        'projeto': projeto,
        'total_atletas': total_atletas,
        'total_lesoes': total_lesoes,
        'total_avaliacoes': total_avaliacoes,
        'taxa_recuperacao': round(taxa_recuperacao, 1),
    }
    return render(request, 'dashboard/coordenador/relatorios.html', context)

# ==============================================
# 5.1 VIEWS DE MEMBROS DO COORDENADOR (COM AS NOVAS ADIÇÕES)
# ==============================================

@login_required
@perfil_required('coordenador')
def coordenador_membros(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # 🔥 ADIÇÃO 1: Adicionei o .order_by para organizar por perfil e depois alfabeticamente
    membros = MembroProjeto.objects.filter(projeto=projeto, ativo=True).select_related('usuario', 'usuario__perfil').order_by(
        'usuario__perfil__tipo',      # Agrupa por tipo de perfil (Coordenador, Técnico, etc)
        'usuario__first_name',        # Ordem alfabética por nome
        'usuario__last_name'          # E por sobrenome
    )
    
    return render(request, 'dashboard/coordenador/membros.html', {
        'projeto': projeto,
        'membros': membros,
    })

# 🔥 ADIÇÃO 2: Nova view para o botão "Adicionar Membro"
@login_required
@perfil_required('coordenador')
def coordenador_adicionar_membro(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        if usuario_id:
            try:
                usuario = User.objects.get(id=usuario_id)
                # get_or_create evita duplicatas
                membro, created = MembroProjeto.objects.get_or_create(
                    projeto=projeto,
                    usuario=usuario
                )
                if not created and not membro.ativo:
                    membro.ativo = True
                    membro.save()
                    messages.success(request, f'{usuario.get_full_name()} foi reativado no projeto!')
                elif not created and membro.ativo:
                    messages.info(request, f'{usuario.get_full_name()} já é um membro ativo deste projeto.')
                else:
                    messages.success(request, f'{usuario.get_full_name()} foi adicionado ao projeto com sucesso!')
                
                return redirect('coordenador_membros')
            except User.DoesNotExist:
                messages.error(request, 'Usuário não encontrado.')

    # Pega apenas os usuários que NÃO são membros ativos deste projeto
    membros_ativos_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario_id', flat=True)
    usuarios_disponiveis = User.objects.exclude(id__in=membros_ativos_ids).order_by('first_name', 'last_name')

    return render(request, 'dashboard/coordenador/adicionar_membro.html', {
        'projeto': projeto,
        'usuarios_disponiveis': usuarios_disponiveis,
    })


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

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        usuario__in=membros_usuario_ids
    ).distinct()
    
    return render(request, 'dashboard/tecnico/atletas.html', {
        'atletas': atletas,
        'projeto': projeto
    })

@login_required
@perfil_required('tecnico')
def tecnico_desempenho(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        usuario__in=membros_usuario_ids
    ).distinct()
    
    return render(request, 'dashboard/tecnico/desempenho.html', {
        'atletas': atletas,
        'projeto': projeto
    })

@login_required
@perfil_required('tecnico')
def tecnico_recuperacao(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        usuario__in=membros_usuario_ids,
        lesoes__tratamentos__ativo=True
    ).distinct()

    return render(request, 'dashboard/tecnico/recuperacao.html', {
        'atletas': atletas,
        'projeto': projeto
    })


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

    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
        return redirect('dashboard')

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

    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
        return redirect('dashboard')

    avaliacoes = AvaliacaoPsicologica.objects.filter(
        atleta=request.user.atleta,
        projeto=projeto
    ).order_by('-data')

    questionarios = QuestionarioPeriodico.objects.filter(
        atleta=request.user.atleta,
        projeto=projeto
    ).order_by('-data')

    return render(request, 'dashboard/atleta/psicologico.html', {
        'avaliacoes': avaliacoes,
        'questionarios': questionarios,
        'projeto': projeto
    })

@login_required
@perfil_required('atleta')
def atleta_exercicios(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
        return redirect('dashboard')

    exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=request.user.atleta,
        tratamento__ativo=True,
        tratamento__lesao__projeto=projeto
    )

    return render(request, 'dashboard/atleta/exercicios.html', {
        'exercicios': exercicios,
        'projeto': projeto
    })


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

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        usuario__in=membros_usuario_ids,
        lesoes__tratamentos__ativo=True
    ).distinct()

    return render(request, 'dashboard/fisioterapeuta/atletas.html', {
        'atletas': atletas,
        'projeto': projeto
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_tratamentos(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    tratamentos = TratamentoFisioterapico.objects.filter(
        ativo=True,
        lesao__projeto=projeto
    ).select_related('lesao', 'lesao__atleta')

    return render(request, 'dashboard/fisioterapeuta/tratamentos.html', {
        'tratamentos': tratamentos,
        'projeto': projeto
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_evolucoes(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    evolucoes = EvolucaoFisica.objects.filter(projeto=projeto).order_by('-data_registro')[:20]
    return render(request, 'dashboard/fisioterapeuta/evolucoes.html', {
        'evolucoes': evolucoes,
        'projeto': projeto
    })


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
    return render(request, 'dashboard/psicologo/avaliacoes.html', {
        'avaliacoes': avaliacoes,
        'projeto': projeto
    })

@login_required
@perfil_required('psicologo')
def psicologo_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(
        avaliacoes_psicologicas__isnull=False,
        usuario__in=membros_usuario_ids
    ).distinct()

    return render(request, 'dashboard/psicologo/atletas.html', {
        'atletas': atletas,
        'projeto': projeto
    })