# ==============================================================================
# REABITECH — GERADOR DE PDF DO PRONTUÁRIO
# Usa reportlab para gerar PDF profissional
# ==============================================================================

from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)


# ==============================================================================
# PALETA DE CORES (mesma do sistema)
# ==============================================================================
COR_VERDE = colors.HexColor('#2BA181')
COR_VERDE_ESCURO = colors.HexColor('#1f8768')
COR_VERDE_CLARO = colors.HexColor('#d1fae5')
COR_CINZA = colors.HexColor('#64748b')
COR_CINZA_CLARO = colors.HexColor('#f1f5f9')
COR_TEXTO = colors.HexColor('#0f172a')
COR_BORDA = colors.HexColor('#e2e8f0')
COR_ROXO = colors.HexColor('#6f42c1')
COR_VERMELHO = colors.HexColor('#dc2626')
COR_AMARELO = colors.HexColor('#d97706')


# ==============================================================================
# ESTILOS
# ==============================================================================
def get_estilos():
    styles = getSampleStyleSheet()

    return {
        'capa_titulo': ParagraphStyle(
            'CapaTitulo',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=28,
            textColor=COR_VERDE,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        'capa_subtitulo': ParagraphStyle(
            'CapaSub',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=12,
            textColor=COR_CINZA,
            alignment=TA_CENTER,
            spaceAfter=30,
        ),
        'capa_info': ParagraphStyle(
            'CapaInfo',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=COR_TEXTO,
            alignment=TA_LEFT,
            leading=16,
        ),
        'section_title': ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=COR_VERDE_ESCURO,
            spaceBefore=20,
            spaceAfter=10,
            borderColor=COR_VERDE,
            borderWidth=0,
            borderPadding=0,
            backColor=None,
        ),
        'label': ParagraphStyle(
            'Label',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=9,
            textColor=COR_CINZA,
            spaceAfter=2,
        ),
        'value': ParagraphStyle(
            'Value',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=COR_TEXTO,
            spaceAfter=8,
            leading=14,
        ),
        'body': ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            textColor=COR_TEXTO,
            alignment=TA_JUSTIFY,
            leading=13,
        ),
        'small': ParagraphStyle(
            'Small',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            textColor=COR_CINZA,
            leading=11,
        ),
        'empty': ParagraphStyle(
            'Empty',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            textColor=COR_CINZA,
            spaceAfter=10,
        ),
    }


# ==============================================================================
# CABEÇALHO E RODAPÉ DAS PÁGINAS
# ==============================================================================
def desenhar_cabecalho_rodape(canvas, doc):
    """Desenha o cabeçalho e o rodapé em cada página."""
    canvas.saveState()
    largura, altura = A4

    # Cabeçalho
    canvas.setFillColor(COR_VERDE)
    canvas.rect(0, altura - 1.2 * cm, largura, 1.2 * cm, fill=1, stroke=0)

    canvas.setFillColor(colors.white)
    canvas.setFont('Helvetica-Bold', 11)
    canvas.drawString(2 * cm, altura - 0.8 * cm, 'REABITECH')

    canvas.setFont('Helvetica', 8)
    canvas.drawRightString(
        largura - 2 * cm,
        altura - 0.8 * cm,
        f'Prontuário Clínico — Emitido em {datetime.now().strftime("%d/%m/%Y às %H:%M")}'
    )

    # Rodapé
    canvas.setFillColor(COR_CINZA)
    canvas.setFont('Helvetica', 8)
    canvas.drawString(
        2 * cm,
        1 * cm,
        'Documento gerado eletronicamente — Arquivamento por 20 anos (COFFITO / Lei 13.787/2018)'
    )
    canvas.drawRightString(largura - 2 * cm, 1 * cm, f'Página {doc.page}')

    canvas.restoreState()


# ==============================================================================
# FUNÇÕES AUXILIARES
# ==============================================================================
def criar_bloco_info(label, valor, estilos):
    """Cria um bloco com label + valor."""
    return [
        Paragraph(label, estilos['label']),
        Paragraph(str(valor) if valor else '—', estilos['value']),
    ]


def criar_tabela_simples(cabecalhos, linhas, estilos):
    """Cria uma tabela com estilo consistente."""
    if not linhas:
        return Paragraph('Nenhum registro.', estilos['empty'])

    data = [cabecalhos] + linhas
    tabela = Table(data, repeatRows=1)
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), COR_VERDE_CLARO),
        ('TEXTCOLOR', (0, 0), (-1, 0), COR_VERDE_ESCURO),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TEXTCOLOR', (0, 1), (-1, -1), COR_TEXTO),
    ]))
    return tabela


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================
def gerar_pdf_prontuario(prontuario):
    """
    Gera o PDF completo do prontuário.
    Retorna um BytesIO com o conteúdo binário.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=1.8 * cm,
        title=f'Prontuário {prontuario.numero_prontuario}',
        author='REABITECH',
    )

    estilos = get_estilos()
    story = []
    atleta = prontuario.atleta

    # ==========================================================
    # CAPA
    # ==========================================================
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph('REABITECH', estilos['capa_titulo']))
    story.append(Paragraph('Plataforma de Reabilitação', estilos['capa_subtitulo']))

    story.append(Spacer(1, 1.5 * cm))

    story.append(Paragraph('<b>PRONTUÁRIO CLÍNICO</b>', ParagraphStyle(
        'CapaDoc', parent=estilos['capa_titulo'],
        fontSize=20, textColor=COR_TEXTO
    )))

    story.append(Spacer(1, 1 * cm))

    # Caixa com dados do paciente
    info_paciente = [
        ['Número do Prontuário:', prontuario.numero_prontuario],
        ['Paciente:', atleta.usuario.get_full_name() or atleta.usuario.username],
        ['RM / Registro:', atleta.rm or '—'],
        ['Modalidade:', atleta.modalidade.nome if atleta.modalidade else '—'],
        ['Status:', prontuario.get_status_display()],
        ['Projeto:', prontuario.projeto.nome],
        ['Data de Abertura:', prontuario.data_abertura.strftime('%d/%m/%Y') if prontuario.data_abertura else '—'],
        ['Fisioterapeuta Responsável:', prontuario.fisioterapeuta_responsavel.get_full_name() if prontuario.fisioterapeuta_responsavel else '—'],
        ['Arquivamento Previsto:', prontuario.data_arquivamento_previsto.strftime('%d/%m/%Y') if prontuario.data_arquivamento_previsto else '—'],
    ]

    tabela_capa = Table(info_paciente, colWidths=[6 * cm, 10 * cm])
    tabela_capa.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), COR_CINZA),
        ('TEXTCOLOR', (1, 0), (1, -1), COR_TEXTO),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -2), 0.3, COR_BORDA),
    ]))
    story.append(tabela_capa)

    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph(
        f'Documento gerado em {datetime.now().strftime("%d/%m/%Y às %H:%M")}',
        estilos['small']
    ))

    story.append(PageBreak())

    # ==========================================================
    # 1. TRIAGENS
    # ==========================================================
    story.append(Paragraph('1. Triagens', estilos['section_title']))

    triagens = prontuario.triagens.all()
    if triagens:
        for t in triagens:
            bloco = [
                Paragraph(f'<b>Data:</b> {t.data_triagem.strftime("%d/%m/%Y")} — <b>Queixa:</b> {t.get_queixa_principal_display()}', estilos['body']),
                Spacer(1, 4),
                Paragraph(f'<b>Descrição:</b> {t.descricao_queixa}', estilos['body']),
            ]

            vitais = []
            if t.pressao_arterial:
                vitais.append(f'PA: {t.pressao_arterial}')
            if t.frequencia_cardiaca:
                vitais.append(f'FC: {t.frequencia_cardiaca} bpm')
            if t.frequencia_respiratoria:
                vitais.append(f'FR: {t.frequencia_respiratoria} irpm')
            if t.temperatura:
                vitais.append(f'Temp: {t.temperatura}°C')
            if t.saturacao_o2:
                vitais.append(f'SpO₂: {t.saturacao_o2}%')
            if t.peso:
                vitais.append(f'Peso: {t.peso} kg')
            if t.altura:
                vitais.append(f'Altura: {t.altura} cm')

            if vitais:
                bloco.append(Spacer(1, 4))
                bloco.append(Paragraph(f'<b>Sinais Vitais:</b> {" | ".join(vitais)}', estilos['body']))

            bloco.append(Spacer(1, 12))
            story.append(KeepTogether(bloco))
    else:
        story.append(Paragraph('Nenhuma triagem registrada.', estilos['empty']))

    # ==========================================================
    # 2. OBJETIVOS
    # ==========================================================
    story.append(Paragraph('2. Objetivos Terapêuticos', estilos['section_title']))

    objetivos = prontuario.objetivos.all()
    if objetivos:
        linhas = [
            [
                o.get_prazo_display().split(' ')[0],
                Paragraph(o.titulo, estilos['small']),
                o.get_status_display(),
                f'{o.percentual_alcancado}%',
            ]
            for o in objetivos
        ]
        tabela = criar_tabela_simples(
            ['Prazo', 'Objetivo', 'Status', 'Progresso'],
            linhas,
            estilos
        )
        story.append(tabela)
    else:
        story.append(Paragraph('Nenhum objetivo cadastrado.', estilos['empty']))

    # ==========================================================
    # 3. MEDICAMENTOS
    # ==========================================================
    story.append(Paragraph('3. Medicamentos em Uso', estilos['section_title']))

    medicamentos = prontuario.medicamentos.filter(status='ativo')
    if medicamentos:
        linhas = [
            [
                Paragraph(f'<b>{m.nome}</b>', estilos['small']),
                f'{m.dosagem} ({m.quantidade})',
                m.get_via_display(),
                m.get_frequencia_display(),
                m.prescritor or '—',
            ]
            for m in medicamentos
        ]
        tabela = criar_tabela_simples(
            ['Medicamento', 'Dose', 'Via', 'Frequência', 'Prescritor'],
            linhas,
            estilos
        )
        story.append(tabela)
    else:
        story.append(Paragraph('Nenhum medicamento em uso.', estilos['empty']))

    story.append(PageBreak())

    # ==========================================================
    # 4. AVALIAÇÃO CIF
    # ==========================================================
    story.append(Paragraph('4. Avaliação CIF', estilos['section_title']))

    avaliacoes_cif = prontuario.avaliacoes_cif.all()
    if avaliacoes_cif:
        for cif in avaliacoes_cif:
            bloco = [
                Paragraph(
                    f'<b>Data:</b> {cif.data_avaliacao.strftime("%d/%m/%Y")} — '
                    f'<b>Pontuação:</b> {cif.pontuacao_global} pts — '
                    f'<b>Classificação:</b> {cif.classificacao_global}',
                    estilos['body']
                ),
                Spacer(1, 6),
            ]

            # Tabela resumo dos 3 componentes
            dados_cif = [
                ['Componente', 'Subtotal'],
                ['Funções e Estruturas do Corpo', str(cif.pontuacao_funcoes_corpo)],
                ['Atividades e Participação', str(cif.pontuacao_atividades)],
                ['Fatores Ambientais', str(cif.pontuacao_fatores_ambientais)],
                ['TOTAL', str(cif.pontuacao_global)],
            ]
            tabela = Table(dados_cif, colWidths=[10 * cm, 4 * cm])
            tabela.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), COR_VERDE_CLARO),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('BACKGROUND', (0, -1), (-1, -1), COR_VERDE_CLARO),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, COR_BORDA),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            bloco.append(tabela)

            if cif.perfil_funcionalidade:
                bloco.append(Spacer(1, 8))
                bloco.append(Paragraph('<b>Perfil Funcional:</b>', estilos['label']))
                bloco.append(Paragraph(cif.perfil_funcionalidade, estilos['body']))

            bloco.append(Spacer(1, 16))
            story.append(KeepTogether(bloco))
    else:
        story.append(Paragraph('Nenhuma avaliação CIF registrada.', estilos['empty']))

    # ==========================================================
    # 5. CARDIORRESPIRATÓRIO
    # ==========================================================
    avaliacoes_cardio = prontuario.avaliacoes_cardiorrespiratorias.all()
    if avaliacoes_cardio:
        story.append(Paragraph('5. Avaliações Cardiorrespiratórias', estilos['section_title']))

        for c in avaliacoes_cardio:
            bloco = [
                Paragraph(
                    f'<b>Data:</b> {c.data_avaliacao.strftime("%d/%m/%Y")} — '
                    f'<b>Condição:</b> {c.get_condicao_principal_display()} — '
                    f'<b>Dispneia:</b> {c.frequencia_dispneia}/4',
                    estilos['body']
                ),
            ]

            if c.spo2_reouso:
                bloco.append(Spacer(1, 4))
                bloco.append(Paragraph(f'<b>SpO₂ repouso:</b> {c.spo2_reouso}%', estilos['body']))

            if c.plano_cardiorrespiratorio:
                bloco.append(Spacer(1, 6))
                bloco.append(Paragraph('<b>Plano:</b>', estilos['label']))
                bloco.append(Paragraph(c.plano_cardiorrespiratorio, estilos['body']))

            bloco.append(Spacer(1, 12))
            story.append(KeepTogether(bloco))

    # ==========================================================
    # 6. ESCALAS DE RISCO
    # ==========================================================
    escalas = prontuario.escalas_risco.all()
    if escalas:
        story.append(Paragraph('6. Escalas de Risco', estilos['section_title']))
        linhas = [
            [
                e.get_tipo_display(),
                e.data_aplicacao.strftime('%d/%m/%Y'),
                f'{e.pontuacao}/{e.pontuacao_maxima}',
                e.get_nivel_risco_display(),
            ]
            for e in escalas
        ]
        tabela = criar_tabela_simples(
            ['Escala', 'Data', 'Pontuação', 'Nível'],
            linhas,
            estilos
        )
        story.append(tabela)

    story.append(PageBreak())

    # ==========================================================
    # 7. RELATÓRIOS DE SESSÃO
    # ==========================================================
    story.append(Paragraph('7. Relatórios de Sessão', estilos['section_title']))

    relatorios = prontuario.relatorios_diarios.all()[:30]
    if relatorios:
        for r in relatorios:
            bloco = [
                Paragraph(
                    f'<b>Sessão de {r.data_sessao.strftime("%d/%m/%Y")}</b> — '
                    f'{r.horario_inicio.strftime("%H:%M")} às {r.horario_fim.strftime("%H:%M")}'
                    f'{" — " + str(r.duracao_minutos) + " min" if r.duracao_minutos else ""}',
                    estilos['body']
                ),
                Spacer(1, 4),
                Paragraph(f'<b>Dor:</b> {r.dor_inicio}/10 → {r.dor_fim}/10', estilos['body']),
                Spacer(1, 4),
                Paragraph(f'<b>Procedimentos:</b> {r.procedimentos}', estilos['body']),
            ]

            if r.plano_proxima_sessao:
                bloco.append(Spacer(1, 4))
                bloco.append(Paragraph(f'<b>Plano próxima sessão:</b> {r.plano_proxima_sessao}', estilos['body']))

            bloco.append(Spacer(1, 12))
            story.append(KeepTogether(bloco))
    else:
        story.append(Paragraph('Nenhum relatório de sessão registrado.', estilos['empty']))

    # ==========================================================
    # 8. EVOLUÇÕES
    # ==========================================================
    evolucoes = prontuario.evolucoes_fisioterapeuticas.all()[:30]
    if evolucoes:
        story.append(Paragraph('8. Evoluções Fisioterapêuticas', estilos['section_title']))

        for e in evolucoes:
            bloco = [
                Paragraph(
                    f'<b>{e.get_tipo_display()}</b> — {e.data.strftime("%d/%m/%Y")}',
                    estilos['body']
                ),
            ]

            if e.escala_dor is not None:
                bloco.append(Paragraph(f'<b>Dor:</b> {e.escala_dor}/10', estilos['body']))

            if e.avaliacao:
                bloco.append(Spacer(1, 4))
                bloco.append(Paragraph(f'<b>Avaliação:</b> {e.avaliacao}', estilos['body']))

            bloco.append(Spacer(1, 12))
            story.append(KeepTogether(bloco))

    # ==========================================================
    # 9. ENCAMINHAMENTOS
    # ==========================================================
    encaminhamentos = prontuario.encaminhamentos.all()
    if encaminhamentos:
        story.append(Paragraph('9. Encaminhamentos Médicos', estilos['section_title']))
        linhas = [
            [
                e.data_encaminhamento.strftime('%d/%m/%Y'),
                e.get_especialidade_display(),
                Paragraph(e.motivo[:100], estilos['small']),
                e.get_status_display(),
            ]
            for e in encaminhamentos
        ]
        tabela = criar_tabela_simples(
            ['Data', 'Especialidade', 'Motivo', 'Status'],
            linhas,
            estilos
        )
        story.append(tabela)

    # ==========================================================
    # 10. EXAMES
    # ==========================================================
    exames = prontuario.exames.all()
    if exames:
        story.append(Paragraph('10. Exames Complementares', estilos['section_title']))
        linhas = [
            [
                e.data_solicitacao.strftime('%d/%m/%Y'),
                e.get_tipo_display(),
                Paragraph(e.descricao[:80], estilos['small']),
                e.get_status_display(),
            ]
            for e in exames
        ]
        tabela = criar_tabela_simples(
            ['Data', 'Tipo', 'Descrição', 'Status'],
            linhas,
            estilos
        )
        story.append(tabela)

    # ==========================================================
    # GERAR PDF
    # ==========================================================
    doc.build(story, onFirstPage=desenhar_cabecalho_rodape, onLaterPages=desenhar_cabecalho_rodape)

    buffer.seek(0)
    return buffer