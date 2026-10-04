# ==============================================================================
# REABITECH — VIEWS DA MENSAGERIA
# Chat interno entre profissionais do mesmo projeto
# ==============================================================================

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from projetos.models import Projeto, MembroProjeto
from .models import Conversa, ParticipanteConversa, Mensagem
from .forms import NovaConversaForm, MensagemForm


# ==============================================================================
# UTILITÁRIO — projeto ativo
# ==============================================================================
def _get_projeto_ativo(request):
    """Retorna o projeto ativo da sessão (validando vínculo do usuário)."""
    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return None
    try:
        projeto = Projeto.objects.get(id=projeto_id, ativo=True)
    except Projeto.DoesNotExist:
        return None

    if not MembroProjeto.objects.filter(
        projeto=projeto, usuario=request.user, ativo=True
    ).exists():
        return None
    return projeto


def _eh_profissional(request, projeto):
    """Retorna True se o usuário NÃO é atleta no projeto (pode usar mensageria)."""
    m = MembroProjeto.objects.filter(
        projeto=projeto, usuario=request.user, ativo=True
    ).first()
    return bool(m and m.tipo != 'atleta')


# ==============================================================================
# 1. LISTA DE CONVERSAS
# ==============================================================================
@login_required
def lista_conversas(request):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo selecionado.')
        return redirect('dashboard:dashboard')

    if not _eh_profissional(request, projeto):
        messages.error(request, 'A mensageria é exclusiva para profissionais da equipe.')
        return redirect('dashboard:dashboard')

    participacoes = ParticipanteConversa.objects.filter(
        usuario=request.user,
        conversa__projeto=projeto,
    ).select_related('conversa', 'conversa__criada_por').order_by('-conversa__atualizada_em')

    conversas_data = []
    total_nao_lidas = 0
    for p in participacoes:
        conv = p.conversa
        nao_lidas = conv.total_nao_lidas_para(request.user)
        total_nao_lidas += nao_lidas
        conversas_data.append({
            'conversa': conv,
            'titulo': conv.titulo_para(request.user),
            'ultima': conv.ultima_mensagem(),
            'nao_lidas': nao_lidas,
            'is_grupo': conv.tipo == 'grupo',
        })

    membros_disponiveis = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True
    ).exclude(tipo='atleta').exclude(usuario=request.user).select_related(
        'usuario', 'modalidade'
    ).order_by('usuario__first_name')

    context = {
        'projeto': projeto,
        'conversas_data': conversas_data,
        'total_conversas': len(conversas_data),
        'total_nao_lidas': total_nao_lidas,
        'membros_disponiveis': membros_disponiveis,
    }
    return render(request, 'mensageria/lista.html', context)


# ==============================================================================
# 2. VER CONVERSA (thread)
# ==============================================================================
@login_required
def ver_conversa(request, conversa_id):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        return redirect('dashboard:dashboard')

    if not _eh_profissional(request, projeto):
        return redirect('dashboard:dashboard')

    conversa = get_object_or_404(
        Conversa,
        id=conversa_id,
        projeto=projeto,
        participantes__usuario=request.user,
    )

    # Marca como lida
    try:
        p = conversa.participantes.get(usuario=request.user)
        p.marcar_como_lida()
    except ParticipanteConversa.DoesNotExist:
        pass

    form = MensagemForm()
    if request.method == 'POST':
        form = MensagemForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.conversa = conversa
            msg.autor = request.user
            msg.save()
            # Atualiza timestamp da conversa
            conversa.save(update_fields=['atualizada_em'])
            return redirect('mensageria:ver_conversa', conversa_id=conversa.id)

    mensagens = conversa.mensagens.filter(
        deletada=False
    ).select_related('autor').order_by('criada_em')

    participantes = conversa.participantes.select_related('usuario').order_by('entrou_em')

    # Sidebar: outras conversas
    outras = ParticipanteConversa.objects.filter(
        usuario=request.user,
        conversa__projeto=projeto,
    ).exclude(conversa=conversa).select_related('conversa').order_by('-conversa__atualizada_em')[:15]

    outras_data = []
    for p in outras:
        c = p.conversa
        outras_data.append({
            'conversa': c,
            'titulo': c.titulo_para(request.user),
            'nao_lidas': c.total_nao_lidas_para(request.user),
            'is_grupo': c.tipo == 'grupo',
        })

    context = {
        'projeto': projeto,
        'conversa': conversa,
        'titulo_conversa': conversa.titulo_para(request.user),
        'mensagens': mensagens,
        'form': form,
        'participantes': participantes,
        'outras_conversas': outras_data,
        'total_participantes': participantes.count(),
    }
    return render(request, 'mensageria/thread.html', context)


# ==============================================================================
# 3. NOVA CONVERSA
# ==============================================================================
@login_required
def nova_conversa(request):
    projeto = _get_projeto_ativo(request)
    if not projeto:
        messages.warning(request, 'Nenhum projeto ativo.')
        return redirect('dashboard:dashboard')

    if not _eh_profissional(request, projeto):
        messages.error(request, 'A mensageria é exclusiva para profissionais da equipe.')
        return redirect('dashboard:dashboard')

    # Se só tem 1 profissional (você), não dá pra conversar
    total_prof = MembroProjeto.objects.filter(
        projeto=projeto, ativo=True
    ).exclude(tipo='atleta').exclude(usuario=request.user).count()

    if total_prof == 0:
        messages.warning(request, 'Não há outros profissionais neste projeto para conversar.')
        return redirect('mensageria:lista_conversas')

    if request.method == 'POST':
        form = NovaConversaForm(request.POST, projeto=projeto, user_atual=request.user)
        if form.is_valid():
            tipo = form.cleaned_data['tipo']
            nome = (form.cleaned_data.get('nome') or '').strip()
            destinatarios = form.cleaned_data['destinatarios']

            # DM: se já existe conversa com o mesmo cara, redireciona pra ela
            if tipo == 'dm' and destinatarios.count() == 1:
                outro = destinatarios.first()
                existente = Conversa.objects.filter(
                    projeto=projeto, tipo='dm',
                    participantes__usuario=request.user,
                ).filter(participantes__usuario=outro).distinct().first()
                if existente:
                    return redirect('mensageria:ver_conversa', conversa_id=existente.id)

            conversa = Conversa.objects.create(
                projeto=projeto,
                criada_por=request.user,
                tipo=tipo,
                nome=nome if tipo == 'grupo' else '',
            )
            ParticipanteConversa.objects.create(conversa=conversa, usuario=request.user)
            for d in destinatarios:
                ParticipanteConversa.objects.get_or_create(conversa=conversa, usuario=d)

            messages.success(request, 'Conversa criada com sucesso!')
            return redirect('mensageria:ver_conversa', conversa_id=conversa.id)
    else:
        form = NovaConversaForm(projeto=projeto, user_atual=request.user)

    return render(request, 'mensageria/nova_conversa.html', {
        'projeto': projeto,
        'form': form,
    })


# ==============================================================================
# 4. API — TOTAL DE NÃO LIDAS (polling global do base.html)
# ==============================================================================
@login_required
def api_conversas_nao_lidas(request):
    """JSON: {total: int, por_conversa: {id: qtd}}"""
    projeto_id = request.session.get('projeto_id')
    if not projeto_id:
        return JsonResponse({'total': 0, 'por_conversa': {}})

    participacoes = ParticipanteConversa.objects.filter(
        usuario=request.user,
        conversa__projeto_id=projeto_id,
    ).select_related('conversa')

    total = 0
    por_conversa = {}
    for p in participacoes:
        n = p.conversa.total_nao_lidas_para(request.user)
        if n > 0:
            por_conversa[str(p.conversa_id)] = n
            total += n

    return JsonResponse({'total': total, 'por_conversa': por_conversa})


# ==============================================================================
# 5. API — MENSAGENS NOVAS (polling da thread, 5s)
# ==============================================================================
@login_required
def api_mensagens_novas(request, conversa_id):
    """JSON: {mensagens: [...]} com id > after_id"""
    projeto = _get_projeto_ativo(request)
    if not projeto:
        return JsonResponse({'erro': 'sem projeto'}, status=400)

    conversa = Conversa.objects.filter(
        id=conversa_id,
        projeto=projeto,
        participantes__usuario=request.user,
    ).distinct().first()

    if not conversa:
        return JsonResponse({'erro': 'conversa nao encontrada'}, status=404)

    try:
        after_id = int(request.GET.get('after_id', 0) or 0)
    except (TypeError, ValueError):
        after_id = 0

    msgs = conversa.mensagens.filter(
        deletada=False, id__gt=after_id
    ).select_related('autor').order_by('id')

    data = []
    for m in msgs:
        data.append({
            'id': m.id,
            'autor': m.autor.get_full_name() or m.autor.username,
            'autor_id': m.autor_id,
            'conteudo': m.conteudo,
            'criada_em': m.criada_em.strftime('%d/%m %H:%M'),
            'tem_anexo': m.tem_anexo,
            'anexo_url': m.anexo.url if m.anexo else '',
            'is_imagem': m.is_imagem,
            'is_pdf': m.is_pdf,
        })

    # Marca como lida (usuário está com a thread aberta)
    try:
        p = conversa.participantes.get(usuario=request.user)
        p.marcar_como_lida()
    except ParticipanteConversa.DoesNotExist:
        pass

    return JsonResponse({'mensagens': data})
