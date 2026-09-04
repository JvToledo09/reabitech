from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q, Avg
from datetime import datetime

# 🔥 Imports novos (para Notificações e envio de e-mail)
import secrets
from django.core.mail import send_mail
from django.conf import settings

from usuarios.models import Perfil, Atleta, ModalidadeEsportiva, Notificacao
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

# 🔥 Função auxiliar para criar notificações
def criar_notificacao(usuario, titulo, mensagem):
    Notificacao.objects.create(usuario=usuario, titulo=titulo, mensagem=mensagem)

# ==============================================
# 1. LOGIN (aceita username, email, RM)
# ==============================================
def login_view(request):
    if request.user.is_authenticated:
        if hasattr(request.user, 'perfil'):
            tipo = request.user.perfil.tipo
            if tipo == 'coordenador': return redirect('dashboard:dashboard_coordenador')
            elif tipo == 'tecnico': return redirect('dashboard:dashboard_tecnico')
            elif tipo == 'atleta': return redirect('dashboard:dashboard_atleta')
            elif tipo == 'fisioterapeuta': return redirect('dashboard:dashboard_fisioterapeuta')
            elif tipo == 'psicologo': return redirect('dashboard:dashboard_psicologo')
            else: return redirect('landing')
        else:
            return redirect('landing')

    if request.method == 'POST':
        login_input = request.POST.get('username')
        password = request.POST.get('password')
        user = None

        print(f"🔑 Tentativa de login: {login_input}")

        # 1. Tenta por username
        try:
            user_obj = User.objects.get(username=login_input)
            user = authenticate(request, username=user_obj.username, password=password)
            if user:
                print(f"   ✅ Login via username: {login_input}")
        except User.DoesNotExist:
            pass

        # 2. Tenta por email (CORRIGIDO para evitar erro de duplicidade)
        if not user and '@' in login_input:
            try:
                user_obj = User.objects.filter(email=login_input).first()
                if user_obj:
                    user = authenticate(request, username=user_obj.username, password=password)
                    if user:
                        print(f"   ✅ Login via email: {login_input}")
            except Exception as e:
                print(f"   ❌ Erro ao buscar email: {e}")

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
                Perfil.objects.create(usuario=user, tipo='atleta', senha_temporaria=False)

            # Define projeto ativo
            membros = MembroProjeto.objects.filter(usuario=user, ativo=True)
            if membros.count() == 1:
                set_projeto_ativo(request, membros.first().projeto.id)

            # Verifica senha temporária
            if user.perfil.senha_temporaria:
                messages.warning(request, 'Você está usando uma senha temporária. Por favor, altere sua senha.')
                return redirect('dashboard:alterar_senha')

            tipo = user.perfil.tipo
            messages.success(request, f'Bem-vindo, {user.get_full_name() or user.username}!')

            # Redireciona conforme o perfil (CORRIGIDO com dashboard:)
            if tipo == 'atleta':
                return redirect('dashboard:dashboard_atleta')
            elif tipo == 'tecnico':
                return redirect('dashboard:dashboard_tecnico')
            elif tipo == 'coordenador':
                return redirect('dashboard:dashboard_coordenador')
            elif tipo == 'fisioterapeuta':
                return redirect('dashboard:dashboard_fisioterapeuta')
            elif tipo == 'psicologo':
                return redirect('dashboard:dashboard_psicologo')
            else:
                return redirect('landing')
        else:
            print(f"   ❌ Falha no login para: {login_input}")
            messages.error(request, 'RM/E-mail ou senha inválidos.')

    return render(request, 'dashboard/login.html')

# ==============================================
# 2. LOGOUT (Rota na raiz, sem dashboard:)
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
        if tipo == 'atleta': return redirect('dashboard:dashboard_atleta')
        elif tipo == 'tecnico': return redirect('dashboard:dashboard_tecnico')
        elif tipo == 'coordenador': return redirect('dashboard:dashboard_coordenador')
        elif tipo == 'fisioterapeuta': return redirect('dashboard:dashboard_fisioterapeuta')
        elif tipo == 'psicologo': return redirect('dashboard:dashboard_psicologo')
        else:
            return redirect('landing')
    else:
        # Segurança: Se não tiver perfil, cria um padrão de atleta
        Perfil.objects.create(usuario=request.user, tipo='atleta', senha_temporaria=False)
        return redirect('dashboard:dashboard_atleta')

# ==============================================
# 3.5 NOTIFICAÇÕES (NOVA FUNCIONALIDADE)
# ==============================================
@login_required
def notificacoes(request):
    notificacoes = request.user.notificacoes.filter(lida=False).order_by('-criada_em')[:10]
    return render(request, 'dashboard/notificacoes.html', {'notificacoes': notificacoes})

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

    # ✅ CORREÇÃO DO LOOP: Vai para a página inicial se não tiver ficha
    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Seu perfil de atleta não está configurado. Contate o coordenador.')
        return redirect('landing')

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
        atletas = MembroProjeto.objects.filter(projeto=projeto, ativo=True, tipo='atleta')
        lesoes_ativas = Lesao.objects.filter(projeto=projeto, tratamentos__ativo=True).distinct().count()
        avaliacoes_psico = AvaliacaoPsicologica.objects.filter(projeto=projeto).count()
        evolucoes = EvolucaoFisica.objects.filter(projeto=projeto).order_by('-data_registro')[:6]
        chart_labels = [e.data_registro.strftime('%d/%m') for e in evolucoes]
        chart_data = [e.desempenho for e in evolucoes]
        if evolucoes.exists():
            taxa_media = sum(e.percentual_recuperacao for e in evolucoes) / evolucoes.count()
        else:
            taxa_media = 0
    else:
        atletas, lesoes_ativas, avaliacoes_psico, taxa_media = [], 0, 0, 0
        chart_labels, chart_data = [], []

    context = {
        'projetos': projetos,
        'projeto_ativo': projeto,
        'total_atletas': atletas.count() if projeto else 0,
        'lesoes_ativas': lesoes_ativas,
        'total_avaliacoes_psico': avaliacoes_psico,
        'taxa_recuperacao_media': round(taxa_media, 1),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    }
    return render(request, 'dashboard/coordenador/dashboard.html', context)

@login_required
@perfil_required('fisioterapeuta')
def dashboard_fisioterapeuta(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

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

    atletas = MembroProjeto.objects.filter(projeto=projeto, ativo=True, tipo='atleta').select_related('usuario')
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

    total_atletas = MembroProjeto.objects.filter(projeto=projeto, tipo='atleta').count()
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

@login_required
@perfil_required('coordenador')
def coordenador_membros(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    todos = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True
    ).select_related('usuario', 'modalidade').order_by(
        'tipo', 'usuario__first_name', 'usuario__last_name'
    )

    membros_unicos = []
    ids_ja_vistos = set()
    for m in todos:
        if m.usuario_id not in ids_ja_vistos:
            membros_unicos.append(m)
            ids_ja_vistos.add(m.usuario_id)

    query = request.GET.get('q', '')
    filtro_tipo = request.GET.get('tipo', '')
    filtro_sexo = request.GET.get('sexo', '')
    filtro_modalidade = request.GET.get('modalidade', '')

    if query:
        membros_unicos = [m for m in membros_unicos if
                          query.lower() in m.usuario.get_full_name().lower() or
                          query.lower() in m.usuario.username.lower() or
                          query.lower() in (m.usuario.email or '').lower()]
    if filtro_tipo:
        membros_unicos = [m for m in membros_unicos if m.tipo == filtro_tipo]
    if filtro_sexo:
        membros_unicos = [m for m in membros_unicos if m.sexo == filtro_sexo]
    if filtro_modalidade:
        membros_unicos = [m for m in membros_unicos if str(m.modalidade_id) == filtro_modalidade]

    modalidades = ModalidadeEsportiva.objects.all()
    tipos = MembroProjeto.TIPO_MEMBRO
    sexos = MembroProjeto.SEXO_CHOICES

    return render(request, 'dashboard/coordenador/membros.html', {
        'projeto': projeto,
        'membros': membros_unicos,
        'modalidades': modalidades,
        'tipos': tipos,
        'sexos': sexos,
        'query': query,
        'filtro_tipo': filtro_tipo,
        'filtro_sexo': filtro_sexo,
        'filtro_modalidade': filtro_modalidade,
    })

@login_required
@perfil_required('coordenador')
def coordenador_adicionar_membro(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    funcoes = MembroProjeto.TIPO_MEMBRO
    modalidades = ModalidadeEsportiva.objects.all()
    sexos = MembroProjeto.SEXO_CHOICES

    if request.method == 'POST':
        if 'membro_id' in request.POST:
            membro_id = request.POST.get('membro_id')
            nova_funcao = request.POST.get('nova_funcao')
            novo_sexo = request.POST.get('novo_sexo')
            nova_modalidade = request.POST.get('nova_modalidade')

            try:
                membro = MembroProjeto.objects.get(id=membro_id, projeto=projeto)
                if membro.usuario == request.user:
                    messages.error(request, 'Você não pode alterar a sua própria função de Coordenador!')
                    return redirect('dashboard:coordenador_adicionar_membro')

                membro.tipo = nova_funcao
                membro.sexo = novo_sexo if novo_sexo else membro.sexo
                membro.modalidade_id = nova_modalidade if nova_modalidade else None
                membro.save()
                messages.success(request, 'Dados do membro atualizados com sucesso!')
                return redirect('dashboard:coordenador_membros')

            except MembroProjeto.DoesNotExist:
                messages.error(request, 'Membro não encontrado.')

        elif 'novo_username' in request.POST:
            novo_username = request.POST.get('novo_username')
            novo_email = request.POST.get('novo_email')
            novo_nome = request.POST.get('novo_nome')
            novo_sobrenome = request.POST.get('novo_sobrenome')
            novo_senha = request.POST.get('novo_senha')
            nova_funcao = request.POST.get('nova_funcao')
            novo_sexo = request.POST.get('novo_sexo')
            nova_modalidade = request.POST.get('nova_modalidade')

            if not novo_username or not nova_funcao:
                messages.error(request, 'Preencha os campos obrigatórios.')
            elif User.objects.filter(username=novo_username).exists():
                messages.error(request, 'Usuário já existe.')
            else:
                if novo_senha:
                    senha_definida = novo_senha
                else:
                    senha_definida = secrets.token_urlsafe(8)

                novo_user = User.objects.create_user(
                    username=novo_username, email=novo_email, password=senha_definida,
                    first_name=novo_nome, last_name=novo_sobrenome
                )

                Perfil.objects.create(usuario=novo_user, tipo=nova_funcao, senha_temporaria=True)
                MembroProjeto.objects.update_or_create(
                    projeto=projeto,
                    usuario=novo_user,
                    defaults={'tipo': nova_funcao, 'sexo': novo_sexo, 'modalidade_id': nova_modalidade, 'ativo': True}
                )

                try:
                    send_mail(
                        'Bem-vindo ao REABITECH - Senha Temporária',
                        f'Olá {novo_nome},\n\nSua conta foi criada com sucesso!\n\nLogin: {novo_username}\nSenha Temporária: {senha_definida}\n\nPor favor, altere sua senha após o primeiro acesso.',
                        settings.DEFAULT_FROM_EMAIL,
                        [novo_email],
                        fail_silently=False,
                    )
                    messages.success(request, f'Usuário criado! Senha enviada para {novo_email}.')
                except Exception as e:
                    messages.success(request, f'Usuário criado! Senha temporária: {senha_definida} (Verifique o terminal)')

                return redirect('dashboard:coordenador_membros')

    membros_ativos = MembroProjeto.objects.filter(projeto=projeto, ativo=True).select_related('usuario')
    return render(request, 'dashboard/coordenador/adicionar_membro.html', {
        'projeto': projeto,
        'membros_ativos': membros_ativos,
        'funcoes': funcoes,
        'modalidades': modalidades,
        'sexos': sexos,
    })

@login_required
@perfil_required('coordenador')
def coordenador_detalhes_membro(request, membro_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')

    membro = get_object_or_404(MembroProjeto, id=membro_id, projeto=projeto)
    evolucoes = EvolucaoFisica.objects.filter(atleta__usuario=membro.usuario, projeto=projeto).order_by('-data_registro')[:5]
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta__usuario=membro.usuario, projeto=projeto).order_by('-data')[:5]

    context = {
        'membro': membro,
        'projeto': projeto,
        'evolucoes': evolucoes,
        'avaliacoes': avaliacoes,
    }
    return render(request, 'dashboard/coordenador/detalhes_membro.html', context)

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

    # ✅ CORREÇÃO DO LOOP
    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
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

    # ✅ CORREÇÃO DO LOOP
    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
        return redirect('landing')

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

    # ✅ CORREÇÃO DO LOOP
    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Perfil de atleta não configurado.')
        return redirect('landing')

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

# ==============================================
# 🔥 FUNÇÃO EXTRA: ALTERAR SENHA (CORRIGIDA - FORA DE OUTRA FUNÇÃO)
# ==============================================
@login_required
def alterar_senha(request):
    if request.method == 'POST':
        nova_senha = request.POST.get('nova_senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        
        if nova_senha and nova_senha == confirmar_senha and len(nova_senha) >= 6:
            request.user.set_password(nova_senha)
            request.user.save()
            
            if hasattr(request.user, 'perfil'):
                request.user.perfil.senha_temporaria = False
                request.user.perfil.save()
            
            messages.success(request, 'Senha alterada com sucesso!')
            return redirect('dashboard:dashboard')
        else:
            messages.error(request, 'As senhas não coincidem ou são muito curtas.')
    
    return render(request, 'dashboard/alterar_senha.html')