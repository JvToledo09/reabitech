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

from usuarios.models import Perfil, Atleta, ModalidadeEsportiva, Notificacao, Alerta
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
def criar_notificacao(usuario, titulo, mensagem, link=None):
    """Cria uma notificação de forma padronizada."""
    return Notificacao.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensagem=mensagem,
        link=link
    )

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

    if not hasattr(request.user, 'atleta'):
        messages.error(request, 'Seu perfil de atleta não está configurado. Contate o coordenador.')
        return redirect('landing')

    atleta = request.user.atleta

    # ==============================================
    # Dados de Fisioterapia
    # ==============================================
    evolucoes = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_registro')
    lesoes = Lesao.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_ocorrencia')
    lesoes_ativas = lesoes.filter(tratamentos__ativo=True).distinct()
    tratamentos_ativos = TratamentoFisioterapico.objects.filter(
        lesao__atleta=atleta, ativo=True
    )
    ultimas_evolucoes = evolucoes[:5]

    # Exercícios pendentes e concluídos
    exercicios_pendentes = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=atleta,
        tratamento__ativo=True,
        check_realizado=False
    ).order_by('id')[:5]
    exercicios_concluidos = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=atleta,
        check_realizado=True
    ).count()
    total_exercicios = ExercicioRecuperacao.objects.filter(
        tratamento__lesao__atleta=atleta
    ).count()

    # ==============================================
    # Dados de Psicologia
    # ==============================================
    avaliacoes = AvaliacaoPsicologica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data')
    ultima_avaliacao = avaliacoes.first()
    questionarios = QuestionarioPeriodico.objects.filter(atleta=atleta, projeto=projeto).order_by('-data')
    ultimo_questionario = questionarios.first()

    # ==============================================
    # Cálculos de Progresso
    # ==============================================
    ultima_evolucao = ultimas_evolucoes.first() if ultimas_evolucoes else None
    progresso = ultima_evolucao.percentual_recuperacao if ultima_evolucao else 0
    score_mental = ultima_avaliacao.score_total if ultima_avaliacao else 0
    status_mental = ultima_avaliacao.status_emocional if ultima_avaliacao else "Não avaliado"

    # Taxa de adesão aos exercícios
    if total_exercicios > 0:
        adesao = round((exercicios_concluidos / total_exercicios) * 100, 1)
    else:
        adesao = 0

    # ==============================================
    # Dados para Gráficos (últimos 6 registros)
    # ==============================================
    ultimos_6 = list(evolucoes[:6])[::-1]

    chart_labels = [e.data_registro.strftime('%d/%m') for e in ultimos_6]
    chart_dor = [e.dor for e in ultimos_6]
    chart_mobilidade = [e.mobilidade for e in ultimos_6]
    chart_forca = [e.forca for e in ultimos_6]
    chart_desempenho = [e.desempenho for e in ultimos_6]
    chart_resistencia = [e.resistencia for e in ultimos_6]
    chart_flexibilidade = [e.flexibilidade for e in ultimos_6]
    chart_percentual = [e.percentual_recuperacao for e in ultimos_6]

    # ==============================================
    # Timeline de Eventos (últimos 10)
    # ==============================================
    timeline = []
    for e in evolucoes[:5]:
        timeline.append({
            'tipo': 'evolucao',
            'data': e.data_registro,
            'titulo': 'Evolução Registrada',
            'descricao': f'Dor: {e.dor}/10 | Recuperação: {e.percentual_recuperacao}%',
            'icone': 'fa-chart-line',
            'cor': 'success'
        })
    for lesao in lesoes[:3]:
        timeline.append({
            'tipo': 'lesao',
            'data': lesao.data_ocorrencia,
            'titulo': f'Nova Lesão: {lesao.get_tipo_display()}',
            'descricao': f'{lesao.local} ({lesao.get_gravidade_display()})',
            'icone': 'fa-exclamation-triangle',
            'cor': 'danger'
        })
    for av in avaliacoes[:3]:
        timeline.append({
            'tipo': 'psicologia',
            'data': av.data,
            'titulo': 'Avaliação Psicológica',
            'descricao': f'Score: {av.score_total}/10 - {av.status_emocional}',
            'icone': 'fa-brain',
            'cor': 'info'
        })
    timeline.sort(key=lambda x: x['data'], reverse=True)

    context = {
        'atleta': atleta,
        'projeto': projeto,
        'evolucoes': ultimas_evolucoes,
        'lesoes': lesoes_ativas,
        'total_lesoes': lesoes.count(),
        'tratamentos_ativos': tratamentos_ativos.count(),
        'exercicios': exercicios_pendentes,
        'exercicios_concluidos': exercicios_concluidos,
        'total_exercicios': total_exercicios,
        'adesao': adesao,
        'avaliacoes': avaliacoes[:5],
        'questionarios': questionarios[:3],
        'ultima_avaliacao': ultima_avaliacao,
        'ultimo_questionario': ultimo_questionario,
        'progresso_recuperacao': progresso,
        'score_mental': score_mental,
        'status_mental': status_mental,
        'ultimo_desempenho': ultima_evolucao.desempenho if ultima_evolucao else 0,
        'ultima_evolucao': ultima_evolucao,
        # Dados para gráficos
        'chart_labels': chart_labels,
        'chart_dor': chart_dor,
        'chart_mobilidade': chart_mobilidade,
        'chart_forca': chart_forca,
        'chart_desempenho': chart_desempenho,
        'chart_resistencia': chart_resistencia,
        'chart_flexibilidade': chart_flexibilidade,
        'chart_percentual': chart_percentual,
        # Timeline
        'timeline': timeline[:10],
    }
    return render(request, 'dashboard/atleta/dashboard.html', context)

@login_required
@perfil_required('tecnico')
def dashboard_tecnico(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # ==============================================
    # Busca dos Atletas do Técnico
    # ==============================================
    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)

    meus_atletas = Atleta.objects.filter(
        tecnico_responsavel=request.user,
        usuario__in=membros_usuario_ids
    ).distinct()

    # Se não tiver nenhum atleta vinculado diretamente, mostra todos do projeto
    if not meus_atletas.exists():
        meus_atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()

    total_atletas = meus_atletas.count()

    # ==============================================
    # Estatísticas Gerais
    # ==============================================
    lesionados = meus_atletas.filter(
        lesoes__tratamentos__ativo=True
    ).distinct().count()

    liberados = total_atletas - lesionados

    # Desempenho médio
    desempenho_medio = EvolucaoFisica.objects.filter(
        atleta__in=meus_atletas,
        projeto=projeto
    ).aggregate(Avg('desempenho'))['desempenho__avg'] or 0

    # Recuperação média
    evolucoes = EvolucaoFisica.objects.filter(atleta__in=meus_atletas, projeto=projeto)
    if evolucoes.exists():
        recuperacao_media = sum(e.percentual_recuperacao for e in evolucoes) / evolucoes.count()
    else:
        recuperacao_media = 0

    # ==============================================
    # Atletas com Detalhes para os Cards
    # ==============================================
    atletas_detalhados = []
    for atleta in meus_atletas:
        ultima_evolucao = EvolucaoFisica.objects.filter(
            atleta=atleta, projeto=projeto
        ).order_by('-data_registro').first()

        lesoes_ativas = atleta.lesoes.filter(tratamentos__ativo=True).distinct()

        atletas_detalhados.append({
            'atleta': atleta,
            'ultima_evolucao': ultima_evolucao,
            'progresso': ultima_evolucao.percentual_recuperacao if ultima_evolucao else 0,
            'desempenho': ultima_evolucao.desempenho if ultima_evolucao else 0,
            'dor': ultima_evolucao.dor if ultima_evolucao else 0,
            'lesoes_ativas': lesoes_ativas,
            'total_lesoes': lesoes_ativas.count(),
            'status': 'lesionado' if lesoes_ativas.exists() else 'liberado',
        })

    # Ordena por desempenho (melhores primeiro)
    atletas_detalhados.sort(key=lambda x: x['desempenho'], reverse=True)

    # ==============================================
    # Top 3 Melhores e Atenção
    # ==============================================
    top_atletas = atletas_detalhados[:3]
    atletas_atencao = [a for a in atletas_detalhados if a['status'] == 'lesionado'][:3]

    # ==============================================
    # Dados para Gráficos
    # ==============================================
    # Gráfico 1: Desempenho dos atletas (barras)
    chart_atletas_labels = [a['atleta'].usuario.get_full_name() or a['atleta'].usuario.username for a in atletas_detalhados[:8]]
    chart_atletas_data = [a['desempenho'] for a in atletas_detalhados[:8]]

    # Gráfico 2: Distribuição por status (doughnut)
    chart_status_data = [lesionados, liberados]

    # Gráfico 3: Evolução média do grupo (últimas 6 semanas)
    evolucoes_recentes = EvolucaoFisica.objects.filter(
        atleta__in=meus_atletas,
        projeto=projeto
    ).order_by('-data_registro')[:12]

    # Agrupa por data
    from collections import defaultdict
    agrupado = defaultdict(list)
    for e in evolucoes_recentes:
        agrupado[e.data_registro.strftime('%d/%m')].append(e.desempenho)

    chart_evo_labels = list(agrupado.keys())[::-1]
    chart_evo_data = [round(sum(v)/len(v), 1) for v in list(agrupado.values())[::-1]]

    # ==============================================
    # Timeline de Atividades
    # ==============================================
    timeline = []
    for a in atletas_detalhados[:5]:
        if a['ultima_evolucao']:
            timeline.append({
                'atleta': a['atleta'],
                'data': a['ultima_evolucao'].data_registro,
                'tipo': 'evolucao',
                'descricao': f"Desempenho: {a['ultima_evolucao'].desempenho}/10 | Recuperação: {a['progresso']}%",
                'icone': 'fa-chart-line',
                'cor': 'success' if a['progresso'] >= 70 else ('warning' if a['progresso'] >= 40 else 'danger'),
            })
    timeline.sort(key=lambda x: x['data'], reverse=True)

    context = {
        'projeto': projeto,
        'meus_atletas': meus_atletas,
        'total_meus_atletas': total_atletas,
        'meus_atletas_lesionados': lesionados,
        'atletas_liberados': liberados,
        'desempenho_medio': round(desempenho_medio, 1),
        'recuperacao_media': round(recuperacao_media, 1),
        'atletas_detalhados': atletas_detalhados,
        'top_atletas': top_atletas,
        'atletas_atencao': atletas_atencao,
        'timeline': timeline,
        # Gráficos
        'chart_atletas_labels': chart_atletas_labels,
        'chart_atletas_data': chart_atletas_data,
        'chart_status_data': chart_status_data,
        'chart_evo_labels': chart_evo_labels,
        'chart_evo_data': chart_evo_data,
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
        # 🔥 CORREÇÃO: Pega os IDs dos usuários que são atletas do projeto
        membros_atletas_ids = MembroProjeto.objects.filter(
            projeto=projeto, tipo='atleta', ativo=True
        ).values_list('usuario_id', flat=True)

        total_atletas = len(membros_atletas_ids)
        atletas_ativos = total_atletas
        
        # Atletas com lesão ativa (para gráfico de status)
        atletas_lesionados = Atleta.objects.filter(
            usuario_id__in=membros_atletas_ids, 
            lesoes__tratamentos__ativo=True
        ).distinct().count()
        
        atletas_em_recuperacao = atletas_lesionados
        atletas_liberados = max(total_atletas - atletas_lesionados, 0)

        lesoes_ativas = Lesao.objects.filter(projeto=projeto, tratamentos__ativo=True).distinct().count()
        avaliacoes_psico = AvaliacaoPsicologica.objects.filter(projeto=projeto).count()
        tratamentos_ativos = TratamentoFisioterapico.objects.filter(ativo=True, lesao__projeto=projeto).count()

        # Dados para gráficos
        evolucoes = EvolucaoFisica.objects.filter(projeto=projeto).order_by('-data_registro')[:6]
        
        # Gráfico 1: Evolução dos atletas
        chart_evo_labels = [e.data_registro.strftime('%d/%m') for e in evolucoes]
        chart_evo_data = [e.percentual_recuperacao for e in evolucoes]

        # Gráfico 2: Distribuição por status (Pizza)
        chart_status_labels = ['Lesionados', 'Liberados', 'Em Recuperação']
        chart_status_data = [atletas_lesionados, atletas_liberados, atletas_em_recuperacao]

        # Gráfico 3: Lesões por modalidade (Barras)
        modalidades = ModalidadeEsportiva.objects.all()
        chart_modal_labels = [m.nome for m in modalidades]
        chart_modal_data = [Lesao.objects.filter(projeto=projeto, atleta__modalidade=m).count() for m in modalidades]

        # Gráfico 4: Tipos de lesões mais frequentes (Barras)
        chart_tipos_labels = [t[1] for t in Lesao.TIPO_LESAO]
        chart_tipos_data = [Lesao.objects.filter(projeto=projeto, tipo=t[0]).count() for t in Lesao.TIPO_LESAO]

        # Gráfico 5: Taxa média de recuperação (Doughnut)
        taxa_media = sum(e.percentual_recuperacao for e in evolucoes) / len(evolucoes) if evolucoes else 0
        
        # Gráfico 6: Indicadores psicológicos (Radar)
        ultimas_avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).order_by('-data')[:5]
        if ultimas_avaliacoes:
            chart_psi_labels = ['Ansiedade', 'Motivação', 'Estresse', 'Autoestima', 'Sono']
            chart_psi_data = [
                sum(a.ansiedade for a in ultimas_avaliacoes) / len(ultimas_avaliacoes),
                sum(a.motivacao for a in ultimas_avaliacoes) / len(ultimas_avaliacoes),
                sum(a.estresse for a in ultimas_avaliacoes) / len(ultimas_avaliacoes),
                sum(a.autoestima for a in ultimas_avaliacoes) / len(ultimas_avaliacoes),
                sum(a.qualidade_sono for a in ultimas_avaliacoes) / len(ultimas_avaliacoes),
            ]
        else:
            chart_psi_labels = []
            chart_psi_data = []

        # Gráfico 7: Desempenho por modalidade (Barras)
        chart_perf_labels = [m.nome for m in modalidades]
        chart_perf_data = []
        for m in modalidades:
            perf = EvolucaoFisica.objects.filter(projeto=projeto, atleta__modalidade=m).aggregate(Avg('desempenho'))['desempenho__avg']
            chart_perf_data.append(round(perf, 1) if perf else 0)

        # Alertas e Notificações (últimos 5)
        alertas_recentes = Alerta.objects.filter(resolvido=False).order_by('-criado_em')[:5]

    else:
        # Inicialização de variáveis vazias para evitar erro
        total_atletas = atletas_ativos = atletas_lesionados = atletas_em_recuperacao = atletas_liberados = 0
        lesoes_ativas = avaliacoes_psico = tratamentos_ativos = 0
        chart_evo_labels = chart_evo_data = chart_status_labels = chart_status_data = []
        chart_modal_labels = chart_modal_data = chart_tipos_labels = chart_tipos_data = []
        taxa_media = 0
        chart_psi_labels = chart_psi_data = chart_perf_labels = chart_perf_data = []
        alertas_recentes = []

    context = {
        'projetos': projetos,
        'projeto_ativo': projeto,
        'total_atletas': total_atletas,
        'atletas_ativos': atletas_ativos,
        'atletas_lesionados': atletas_lesionados,
        'atletas_liberados': atletas_liberados,
        'atletas_em_recuperacao': atletas_em_recuperacao,
        'lesoes_ativas': lesoes_ativas,
        'avaliacoes_psico': avaliacoes_psico,
        'tratamentos_ativos': tratamentos_ativos,
        'taxa_recuperacao_media': round(taxa_media, 1),
        # Dados para gráficos
        'chart_evo_labels': chart_evo_labels, 'chart_evo_data': chart_evo_data,
        'chart_status_labels': chart_status_labels, 'chart_status_data': chart_status_data,
        'chart_modal_labels': chart_modal_labels, 'chart_modal_data': chart_modal_data,
        'chart_tipos_labels': chart_tipos_labels, 'chart_tipos_data': chart_tipos_data,
        'chart_psi_labels': chart_psi_labels, 'chart_psi_data': chart_psi_data,
        'chart_perf_labels': chart_perf_labels, 'chart_perf_data': chart_perf_data,
        'alertas_recentes': alertas_recentes,
    }
    return render(request, 'dashboard/coordenador/dashboard.html', context)

@login_required
@perfil_required('fisioterapeuta')
def dashboard_fisioterapeuta(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # ==============================================
    # Atletas em atendimento
    # ==============================================
    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)

    atletas = Atleta.objects.filter(
        usuario__in=membros_usuario_ids,
        lesoes__tratamentos__ativo=True
    ).distinct()

    # ==============================================
    # Tratamentos ativos
    # ==============================================
    tratamentos_ativos = TratamentoFisioterapico.objects.filter(
        ativo=True,
        lesao__projeto=projeto
    ).count()

    # ==============================================
    # 🔥 NOVAS VARIÁVEIS: Evoluções de hoje e Alertas ativos
    # ==============================================
    from datetime import date

    evolucoes_hoje = EvolucaoFisica.objects.filter(
        projeto=projeto,
        data_registro=date.today()
    ).count()

    alertas_ativos = Alerta.objects.filter(
        resolvido=False,
        atleta__in=atletas
    ).count()

    context = {
        'projeto': projeto,
        'atletas_em_atendimento': atletas,
        'total_tratamentos_ativos': tratamentos_ativos,
        'evolucoes_hoje': evolucoes_hoje,      # 🔥 NOVO
        'alertas_ativos': alertas_ativos,      # 🔥 NOVO
    }
    return render(request, 'dashboard/fisioterapeuta/dashboard.html', context)

@login_required
@perfil_required('psicologo')
def dashboard_psicologo(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # ==============================================
    # Dados de Atletas e Avaliações
    # ==============================================
    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)

    atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()
    atletas_total = atletas.count()

    # Avaliações de todos os atletas do projeto
    avaliacoes_geral = AvaliacaoPsicologica.objects.filter(
        projeto=projeto
    ).order_by('-data')

    # Últimas 10 avaliações para a tabela
    avaliacoes_recentes = avaliacoes_geral[:10]

    # ==============================================
    # Cálculos Estatísticos
    # ==============================================
    total_avaliacoes = avaliacoes_geral.count()

    # Atletas com acompanhamento psicológico
    atletas_acompanhados = atletas.filter(
        avaliacoes_psicologicas__isnull=False
    ).distinct().count()

    # Atletas sem acompanhamento (que precisam ser avaliados)
    atletas_sem_avaliacao = atletas_total - atletas_acompanhados

    # Média dos últimos 30 dias
    from datetime import timedelta, date
    data_limite = date.today() - timedelta(days=30)
    avaliacoes_mes = avaliacoes_geral.filter(data__gte=data_limite)

    if avaliacoes_mes.exists():
        media_ansiedade = round(avaliacoes_mes.aggregate(Avg('ansiedade'))['ansiedade__avg'] or 0, 1)
        media_motivacao = round(avaliacoes_mes.aggregate(Avg('motivacao'))['motivacao__avg'] or 0, 1)
        media_estresse = round(avaliacoes_mes.aggregate(Avg('estresse'))['estresse__avg'] or 0, 1)
        media_autoestima = round(avaliacoes_mes.aggregate(Avg('autoestima'))['autoestima__avg'] or 0, 1)
        media_sono = round(avaliacoes_mes.aggregate(Avg('qualidade_sono'))['qualidade_sono__avg'] or 0, 1)
    else:
        media_ansiedade = media_motivacao = media_estresse = media_autoestima = media_sono = 0

    # ==============================================
    # Distribuição por Status Emocional
    # ==============================================
    status_bom = 0
    status_regular = 0
    status_atencao = 0

    # Pega a última avaliação de cada atleta
    for atleta in atletas:
        ultima = atleta.avaliacoes_psicologicas.order_by('-data').first()
        if ultima:
            if ultima.score_total >= 7:
                status_bom += 1
            elif ultima.score_total >= 4:
                status_regular += 1
            else:
                status_atencao += 1

    # ==============================================
    # Atletas que precisam de atenção
    # ==============================================
    atletas_atencao = []
    for atleta in atletas:
        ultima = atleta.avaliacoes_psicologicas.order_by('-data').first()
        if ultima and ultima.score_total < 4:
            atletas_atencao.append({
                'atleta': atleta,
                'ultima_avaliacao': ultima,
                'score': ultima.score_total,
                'status': ultima.status_emocional,
            })

    # ==============================================
    # Questionários Pendentes
    # ==============================================
    questionarios_recentes = QuestionarioPeriodico.objects.filter(
        projeto=projeto
    ).order_by('-data')[:5]

    # ==============================================
    # Timeline de Avaliações (últimos 15 eventos)
    # ==============================================
    timeline = []
    for av in avaliacoes_geral[:10]:
        timeline.append({
            'data': av.data,
            'atleta_nome': av.atleta.usuario.get_full_name() or av.atleta.usuario.username,
            'score': av.score_total,
            'status': av.status_emocional,
            'cor': 'success' if av.score_total >= 7 else ('warning' if av.score_total >= 4 else 'danger'),
        })

    # ==============================================
    # Dados para Gráficos
    # ==============================================
    # Gráfico 1: Evolução dos indicadores (últimas 6 avaliações do projeto)
    ultimas_6 = list(avaliacoes_geral[:6])[::-1]
    chart_labels = [a.data.strftime('%d/%m') for a in ultimas_6]
    chart_ansiedade = [a.ansiedade for a in ultimas_6]
    chart_motivacao = [a.motivacao for a in ultimas_6]
    chart_estresse = [a.estresse for a in ultimas_6]
    chart_autoestima = [a.autoestima for a in ultimas_6]
    chart_sono = [a.qualidade_sono for a in ultimas_6]

    context = {
        'projeto': projeto,
        # Estatísticas
        'atletas_total': atletas_total,
        'atletas_acompanhados': atletas_acompanhados,
        'atletas_sem_avaliacao': atletas_sem_avaliacao,
        'total_avaliacoes': total_avaliacoes,
        # Médias
        'media_ansiedade': media_ansiedade,
        'media_motivacao': media_motivacao,
        'media_estresse': media_estresse,
        'media_autoestima': media_autoestima,
        'media_sono': media_sono,
        # Distribuição
        'status_bom': status_bom,
        'status_regular': status_regular,
        'status_atencao': status_atencao,
        # Listas
        'avaliacoes_recentes': avaliacoes_recentes,
        'questionarios_recentes': questionarios_recentes,
        'atletas_atencao': atletas_atencao,
        'timeline': timeline,
        # Gráficos
        'chart_labels': chart_labels,
        'chart_ansiedade': chart_ansiedade,
        'chart_motivacao': chart_motivacao,
        'chart_estresse': chart_estresse,
        'chart_autoestima': chart_autoestima,
        'chart_sono': chart_sono,
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
# 🔥 NOVAS FUNÇÕES PARA CRUD DE FISIOTERAPIA
# ==============================================

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_todos_atletas(request):
    """Lista todos os atletas do projeto para criar nova lesão"""
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    membros_usuario_ids = MembroProjeto.objects.filter(projeto=projeto, ativo=True, tipo='atleta').values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()

    return render(request, 'dashboard/fisioterapeuta/todos_atletas.html', {
        'atletas': atletas,
        'projeto': projeto
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_criar_lesao(request, atleta_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')

    atleta = get_object_or_404(Atleta, id=atleta_id)

    if request.method == 'POST':
        lesao = Lesao.objects.create(
            atleta=atleta,
            projeto=projeto,
            tipo=request.POST.get('tipo'),
            gravidade=request.POST.get('gravidade'),
            regiao_corporal=request.POST.get('regiao_corporal'),
            lado=request.POST.get('lado'),
            causa=request.POST.get('causa'),
            local=request.POST.get('local'),
            data_ocorrencia=request.POST.get('data_ocorrencia'),
            descricao=request.POST.get('descricao'),
            diagnostico=request.POST.get('diagnostico'),
            previsao_recuperacao=request.POST.get('previsao_recuperacao') or None,
            fisioterapeuta_responsavel=request.user,
        )
        
        # Alerta automático de nova lesão
        Alerta.objects.create(
            atleta=atleta,
            tipo='dor_alta',
            mensagem=f"Nova lesão registrada: {lesao.get_tipo_display()}",
        )
        
        messages.success(request, 'Lesão registrada com sucesso!')
        return redirect('dashboard:fisioterapeuta_atletas')

    tipos = Lesao.TIPO_LESAO
    gravidades = Lesao.GRAVIDADE
    return render(request, 'dashboard/fisioterapeuta/criar_lesao.html', {
        'atleta': atleta,
        'projeto': projeto,
        'tipos': tipos,
        'gravidades': gravidades,
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_criar_tratamento(request, lesao_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')
    
    lesao = get_object_or_404(Lesao, id=lesao_id)
    
    if request.method == 'POST':
        TratamentoFisioterapico.objects.create(
            lesao=lesao,
            descricao=request.POST.get('descricao'),
            data_previsao_termino=request.POST.get('data_previsao_termino') or None
        )
        lesao.status = 'em_tratamento'
        lesao.save()
        
        messages.success(request, 'Tratamento iniciado com sucesso!')
        return redirect('dashboard:fisioterapeuta_detalhes_lesao', lesao_id=lesao.id)
    
    return render(request, 'dashboard/fisioterapeuta/criar_tratamento.html', {'lesao': lesao})

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_detalhes_lesao(request, lesao_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')
    
    lesao = get_object_or_404(Lesao, id=lesao_id)
    tratamentos = lesao.tratamentos.all().order_by('-data_inicio')
    exercicios = ExercicioRecuperacao.objects.filter(tratamento__lesao=lesao)
    
    return render(request, 'dashboard/fisioterapeuta/detalhes_lesao.html', {
        'lesao': lesao,
        'tratamentos': tratamentos,
        'exercicios': exercicios,
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_adicionar_exercicio(request, tratamento_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')
    
    tratamento = get_object_or_404(TratamentoFisioterapico, id=tratamento_id)
    
    if request.method == 'POST':
        exercicio = ExercicioRecuperacao.objects.create(
            tratamento=tratamento,
            nome=request.POST.get('nome'),
            descricao=request.POST.get('descricao'),
            grupo_muscular=request.POST.get('grupo_muscular'),
            dificuldade=request.POST.get('dificuldade'),
            series=request.POST.get('series'),
            repeticoes=request.POST.get('repeticoes'),
            duracao_minutos=request.POST.get('duracao_minutos'),
            frequencia=request.POST.get('frequencia'),
            video_url=request.POST.get('video_url'),
            observacoes=request.POST.get('observacoes'),
        )
        
        Notificacao.objects.create(
            usuario=tratamento.lesao.atleta.usuario,
            titulo='Novo exercício atribuído',
            mensagem=f'Você recebeu um novo exercício: {exercicio.nome}',
            link=f'/dashboard/atleta/exercicios/'
        )
        
        messages.success(request, 'Exercício adicionado com sucesso!')
        return redirect('dashboard:fisioterapeuta_detalhes_lesao', lesao_id=tratamento.lesao.id)
    
    dificuldades = [(1, 'Fácil'), (2, 'Médio'), (3, 'Difícil')]
    return render(request, 'dashboard/fisioterapeuta/adicionar_exercicio.html', {
        'tratamento': tratamento,
        'dificuldades': dificuldades,
    })

@login_required
@perfil_required('fisioterapeuta')
def fisioterapeuta_registrar_evolucao(request, atleta_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        return redirect('landing')
    
    atleta = get_object_or_404(Atleta, id=atleta_id)
    
    if request.method == 'POST':
        evolucao = EvolucaoFisica.objects.create(
            atleta=atleta,
            projeto=projeto,
            dor=request.POST.get('dor'),
            mobilidade=request.POST.get('mobilidade'),
            forca=request.POST.get('forca'),
            desempenho=request.POST.get('desempenho'),
            resistencia=request.POST.get('resistencia'),
            flexibilidade=request.POST.get('flexibilidade'),
            observacoes=request.POST.get('observacoes'),
            estagiario_responsavel=request.user,
        )
        
        if int(evolucao.dor) >= 7:
            Alerta.objects.create(
                atleta=atleta,
                tipo='dor_alta',
                mensagem=f'Dor alta registrada ({evolucao.dor}/10) no dia {evolucao.data_registro}',
            )
        
        ultimas = EvolucaoFisica.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_registro')[:3]
        if len(ultimas) == 3:
            if ultimas[0].percentual_recuperacao == ultimas[1].percentual_recuperacao == ultimas[2].percentual_recuperacao:
                Alerta.objects.create(
                    atleta=atleta,
                    tipo='recuperacao_estagnada',
                    mensagem='A recuperação do atleta está estagnada. Verifique o tratamento.',
                )
        
        messages.success(request, 'Evolução registrada com sucesso!')
        return redirect('dashboard:fisioterapeuta_atletas')
    
    return render(request, 'dashboard/fisioterapeuta/registrar_evolucao.html', {'atleta': atleta})
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

    # Busca com filtro opcional de atleta
    atleta_id = request.GET.get('atleta', '')
    avaliacoes = AvaliacaoPsicologica.objects.filter(projeto=projeto).order_by('-data')

    if atleta_id:
        avaliacoes = avaliacoes.filter(atleta_id=atleta_id)

    # Estatísticas para o header do template
    total_avaliacoes = avaliacoes.count()
    score_medio = avaliacoes.aggregate(Avg('ansiedade'))['ansiedade__avg'] or 0

    # Lista de atletas para o filtro dropdown
    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()

    return render(request, 'dashboard/psicologo/avaliacoes.html', {
        'avaliacoes': avaliacoes,
        'projeto': projeto,
        'total_avaliacoes': total_avaliacoes,
        'atletas': atletas,
        'atleta_filtro': atleta_id,
    })


@login_required
@perfil_required('psicologo')
def psicologo_atletas(request):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    # 🔥 CORREÇÃO: Mostra TODOS os atletas do projeto (não apenas os que já têm avaliação)
    membros_usuario_ids = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True, tipo='atleta'
    ).values_list('usuario', flat=True)
    atletas = Atleta.objects.filter(usuario__in=membros_usuario_ids).distinct()

    return render(request, 'dashboard/psicologo/atletas.html', {
        'atletas': atletas,
        'projeto': projeto,
    })


@login_required
@perfil_required('psicologo')
def psicologo_nova_avaliacao(request, atleta_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    atleta = get_object_or_404(Atleta, id=atleta_id)

    if request.method == 'POST':
        try:
            avaliacao = AvaliacaoPsicologica.objects.create(
                atleta=atleta,
                projeto=projeto,
                ansiedade=int(request.POST.get('ansiedade', 5)),
                motivacao=int(request.POST.get('motivacao', 5)),
                estresse=int(request.POST.get('estresse', 5)),
                autoestima=int(request.POST.get('autoestima', 5)),
                qualidade_sono=int(request.POST.get('qualidade_sono', 5)),
                observacoes=request.POST.get('observacoes', ''),
                psicologo_responsavel=request.user,
            )

            # Alerta automático se score estiver baixo
            if avaliacao.score_total < 4:
                Alerta.objects.create(
                    atleta=atleta,
                    tipo='avaliacao_pendente',
                    mensagem=f'Avaliação psicológica com score baixo ({avaliacao.score_total}/10). Verificar atleta.',
                )

            # Notificação para o atleta
            Notificacao.objects.create(
                usuario=atleta.usuario,
                titulo='Nova Avaliação Psicológica',
                mensagem=f'Uma nova avaliação psicológica foi registrada em {avaliacao.data.strftime("%d/%m/%Y")}.',
                link='/dashboard/atleta/psicologico/'
            )

            messages.success(request, f'Avaliação de {atleta.usuario.get_full_name()} registrada com sucesso!')
            return redirect('dashboard:psicologo_detalhes_avaliacao', avaliacao_id=avaliacao.id)
        except Exception as e:
            messages.error(request, f'Erro ao registrar avaliação: {e}')

    return render(request, 'dashboard/psicologo/nova_avaliacao.html', {
        'atleta': atleta,
        'projeto': projeto,
    })


@login_required
@perfil_required('psicologo')
def psicologo_detalhes_avaliacao(request, avaliacao_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    avaliacao = get_object_or_404(AvaliacaoPsicologica, id=avaliacao_id)
    avaliacoes_anteriores = AvaliacaoPsicologica.objects.filter(
        atleta=avaliacao.atleta
    ).order_by('-data').exclude(id=avaliacao.id)[:5]

    return render(request, 'dashboard/psicologo/detalhes_avaliacao.html', {
        'avaliacao': avaliacao,
        'atleta': avaliacao.atleta,
        'projeto': projeto,
        'avaliacoes_anteriores': avaliacoes_anteriores,
    })


@login_required
@perfil_required('psicologo')
def psicologo_novo_questionario(request, atleta_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    atleta = get_object_or_404(Atleta, id=atleta_id)

    if request.method == 'POST':
        QuestionarioPeriodico.objects.create(
            atleta=atleta,
            projeto=projeto,
            pergunta_1=int(request.POST.get('pergunta_1', 3)),
            pergunta_2=int(request.POST.get('pergunta_2', 3)),
            pergunta_3=int(request.POST.get('pergunta_3', 3)),
            pergunta_4=int(request.POST.get('pergunta_4', 3)),
            pergunta_5=int(request.POST.get('pergunta_5', 3)),
            comentarios=request.POST.get('comentarios', ''),
        )
        messages.success(request, 'Questionário registrado com sucesso!')
        return redirect('dashboard:psicologo_atletas')

    return render(request, 'dashboard/psicologo/novo_questionario.html', {
        'atleta': atleta,
        'projeto': projeto,
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


@login_required
def marcar_notificacao_lida(request, notificacao_id):
    notificacao = get_object_or_404(Notificacao, id=notificacao_id, usuario=request.user)
    notificacao.lida = True
    notificacao.save()
    if notificacao.link:
        return redirect(notificacao.link)
    return redirect('dashboard:notificacoes')


@login_required
def marcar_todas_lidas(request):
    request.user.notificacoes.filter(lida=False).update(lida=True)
    messages.success(request, 'Todas as notificações foram marcadas como lidas.')
    return redirect('dashboard:notificacoes')

    

# ==============================================
# 🔥 VIEW: Detalhes do Atleta para o Técnico
# ==============================================
@login_required
@perfil_required('tecnico')
def tecnico_detalhes_atleta(request, atleta_id):
    projeto = get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('landing')

    atleta = get_object_or_404(Atleta, id=atleta_id)

    evolucoes = EvolucaoFisica.objects.filter(
        atleta=atleta, projeto=projeto
    ).order_by('-data_registro')

    lesoes = Lesao.objects.filter(atleta=atleta, projeto=projeto).order_by('-data_ocorrencia')
    lesoes_ativas = lesoes.filter(tratamentos__ativo=True).distinct()
    tratamentos_ativos = TratamentoFisioterapico.objects.filter(
        lesao__atleta=atleta, ativo=True
    )

    ultima_evolucao = evolucoes.first()
    progresso = ultima_evolucao.percentual_recuperacao if ultima_evolucao else 0

    ultimos_6 = list(evolucoes[:6])[::-1]
    chart_labels = [e.data_registro.strftime('%d/%m') for e in ultimos_6]
    chart_dor = [e.dor for e in ultimos_6]
    chart_mobilidade = [e.mobilidade for e in ultimos_6]
    chart_forca = [e.forca for e in ultimos_6]
    chart_desempenho = [e.desempenho for e in ultimos_6]
    chart_percentual = [e.percentual_recuperacao for e in ultimos_6]

    total_evolucoes = evolucoes.count()
    total_lesoes = lesoes.count()
    total_tratamentos = TratamentoFisioterapico.objects.filter(lesao__atleta=atleta).count()
    media_desempenho = evolucoes.aggregate(Avg('desempenho'))['desempenho__avg'] or 0
    media_dor = evolucoes.aggregate(Avg('dor'))['dor__avg'] or 0

    avaliacoes = AvaliacaoPsicologica.objects.filter(
        atleta=atleta, projeto=projeto
    ).order_by('-data')[:5]
    ultima_avaliacao = avaliacoes.first() if avaliacoes.exists() else None

    timeline = []
    for e in evolucoes[:3]:
        timeline.append({
            'data': e.data_registro,
            'titulo': 'Evolução Registrada',
            'descricao': f'Dor: {e.dor}/10 | Recuperação: {e.percentual_recuperacao}%',
            'icone': 'fa-chart-line',
            'cor': 'success'
        })
    for l in lesoes[:2]:
        timeline.append({
            'data': l.data_ocorrencia,
            'titulo': f'Lesão: {l.get_tipo_display()}',
            'descricao': f'{l.local} - {l.get_gravidade_display()}',
            'icone': 'fa-exclamation-triangle',
            'cor': 'danger'
        })
    timeline.sort(key=lambda x: x['data'], reverse=True)

    context = {
        'atleta': atleta,
        'projeto': projeto,
        'evolucoes': evolucoes[:10],
        'lesoes': lesoes,
        'lesoes_ativas': lesoes_ativas,
        'tratamentos_ativos': tratamentos_ativos,
        'progresso': progresso,
        'ultima_evolucao': ultima_evolucao,
        'total_evolucoes': total_evolucoes,
        'total_lesoes': total_lesoes,
        'total_tratamentos': total_tratamentos,
        'media_desempenho': round(media_desempenho, 1),
        'media_dor': round(media_dor, 1),
        'avaliacoes': avaliacoes,
        'ultima_avaliacao': ultima_avaliacao,
        'timeline': timeline,
        'chart_labels': chart_labels,
        'chart_dor': chart_dor,
        'chart_mobilidade': chart_mobilidade,
        'chart_forca': chart_forca,
        'chart_desempenho': chart_desempenho,
        'chart_percentual': chart_percentual,
    }
    return render(request, 'dashboard/tecnico/detalhes_atleta.html', context)

    

# ==============================================
# 🔥 RESOLVER ALERTA
# ==============================================
@login_required
def resolver_alerta(request, alerta_id):
    """Marca um alerta como resolvido."""
    alerta = get_object_or_404(Alerta, id=alerta_id)
    
    # Verifica se o usuário tem permissão
    if request.user.perfil.tipo not in ['coordenador', 'tecnico', 'fisioterapeuta']:
        messages.error(request, 'Você não tem permissão para resolver este alerta.')
        return redirect('dashboard:dashboard')
    
    alerta.resolvido = True
    alerta.save()
    
    messages.success(request, f'Alerta "{alerta.get_tipo_display()}" resolvido com sucesso!')
    
    # Volta para a página anterior
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('dashboard:dashboard')

    

# ==============================================
# 🔥 PERFIL DO USUÁRIO (Qualquer perfil pode acessar)
# ==============================================
@login_required
def perfil_usuario(request):
    """Página de perfil do usuário logado."""
    perfil = request.user.perfil

    if request.method == 'POST':
        # Atualizar dados do User
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        # Atualizar dados do Perfil
        perfil.telefone = request.POST.get('telefone', '')
        perfil.data_nascimento = request.POST.get('data_nascimento') or None
        perfil.sexo = request.POST.get('sexo') or None

        # Upload de foto
        if request.FILES.get('foto'):
            perfil.foto = request.FILES.get('foto')

        perfil.save()

        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('dashboard:perfil_usuario')

    context = {
        'perfil': perfil,
    }
    return render(request, 'dashboard/perfil.html', context)