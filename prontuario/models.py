from django.db import models

# Create your models here.
# ==============================================================================
# REABITECH — APP PRONTUÁRIO
# Sistema completo de prontuário clínico para fisioterapia (FHO)
# Inclui: Triagem, Objetivos, Medicamentos, Relatórios, CIF, Cardiorrespiratório
# ==============================================================================

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta

from usuarios.models import Atleta
from projetos.models import Projeto


# ==============================================================================
# 1. PRONTUÁRIO (Container do paciente)
# ==============================================================================
class Prontuario(models.Model):
    """
    Container principal do prontuário do paciente.
    Guarda dados gerais e controla o arquivamento por 20 anos (exigência FHO).
    """
    STATUS_CHOICES = [
        ('ativo', 'Ativo'),
        ('alta', 'Alta'),
        ('transferido', 'Transferido'),
        ('desistente', 'Desistente'),
        ('arquivado', 'Arquivado'),
    ]

    # ----- Identificação -----
    atleta = models.OneToOneField(
        Atleta,
        on_delete=models.CASCADE,
        related_name='prontuario',
        verbose_name='Paciente'
    )
    projeto = models.ForeignKey(
        Projeto,
        on_delete=models.CASCADE,
        related_name='prontuarios',
        verbose_name='Projeto'
    )
    numero_prontuario = models.CharField(
        max_length=30,
        unique=True,
        blank=True,
        verbose_name='Número do Prontuário'
    )

    # ----- Responsáveis -----
    fisioterapeuta_responsavel = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prontuarios_fisio',
        verbose_name='Fisioterapeuta Responsável'
    )
    estagiarios = models.ManyToManyField(
        User,
        blank=True,
        related_name='prontuarios_estagiario',
        verbose_name='Estagiários'
    )

    # ----- Status -----
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name='Status'
    )

    # ----- Controle de arquivamento (FHO — 20 anos) -----
    data_abertura = models.DateField(
        auto_now_add=True,
        verbose_name='Data de Abertura'
    )
    data_alta = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Alta'
    )
    data_arquivamento_previsto = models.DateField(
        null=True,
        blank=True,
        verbose_name='Arquivamento Previsto',
        help_text='Data em que o prontuário pode ser arquivado (20 anos após a última movimentação)'
    )
    ultima_movimentacao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Última Movimentação'
    )

    # ----- Auditoria -----
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Prontuário'
        verbose_name_plural = 'Prontuários'
        indexes = [
            models.Index(fields=['atleta', 'status']),
            models.Index(fields=['projeto', 'status']),
        ]

    def __str__(self):
        return f"Prontuário {self.numero_prontuario} — {self.atleta.usuario.get_full_name()}"

    def save(self, *args, **kwargs):
        # Gera número de prontuário automaticamente
        if not self.numero_prontuario:
            ano = timezone.now().year
            ultimo = Prontuario.objects.filter(
                numero_prontuario__startswith=f"PR-{ano}"
            ).count() + 1
            self.numero_prontuario = f"PR-{ano}-{ultimo:04d}"

        # Define arquivamento previsto (20 anos após última movimentação)
        if not self.data_arquivamento_previsto:
            base = self.ultima_movimentacao or timezone.now()
            self.data_arquivamento_previsto = (base + timedelta(days=20*365)).date()

        super().save(*args, **kwargs)

    def registrar_movimentacao(self):
        """Atualiza a última movimentação e o arquivamento previsto."""
        self.ultima_movimentacao = timezone.now()
        self.data_arquivamento_previsto = (
            timezone.now() + timedelta(days=20*365)
        ).date()
        self.save()

    @property
    def dias_ate_arquivamento(self):
        """Quantos dias faltam até o arquivamento."""
        if not self.data_arquivamento_previsto:
            return None
        return (self.data_arquivamento_previsto - timezone.now().date()).days

    @property
    def idade_prontuario(self):
        """Há quantos dias o prontuário existe."""
        return (timezone.now().date() - self.data_abertura).days


# ==============================================================================
# 2. TRIAGEM INICIAL
# ==============================================================================
class Triagem(models.Model):
    """
    Triagem inicial do paciente — queixa principal, histórico, sinais vitais.
    """
    QUEIXA_CHOICES = [
        ('dor', 'Dor'),
        ('limitacao_movimento', 'Limitação de movimento'),
        ('fraqueza', 'Fraqueza muscular'),
        ('edema', 'Edema / Inchaço'),
        ('falta_ar', 'Falta de ar / Dispneia'),
        ('fadiga', 'Fadiga'),
        ('outro', 'Outro'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='triagens',
        verbose_name='Prontuário'
    )
    data_triagem = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Triagem'
    )

    # ----- Queixa principal -----
    queixa_principal = models.CharField(
        max_length=50,
        choices=QUEIXA_CHOICES,
        default='dor',
        verbose_name='Queixa Principal'
    )
    descricao_queixa = models.TextField(
        verbose_name='Descrição da Queixa',
        help_text='Descreva o problema atual do paciente em detalhes'
    )

    # ----- Histórico -----
    historia_doenca_atual = models.TextField(
        blank=True,
        verbose_name='História da Doença Atual (HDA)'
    )
    historia_pregressa = models.TextField(
        blank=True,
        verbose_name='História Patológica Pregressa (HPP)'
    )
    historico_familiar = models.TextField(
        blank=True,
        verbose_name='Histórico Familiar'
    )
    medicamentos_uso = models.TextField(
        blank=True,
        verbose_name='Medicamentos em Uso',
        help_text='Liste os medicamentos ou escreva "Não faz uso"'
    )
    alergias = models.TextField(
        blank=True,
        verbose_name='Alergias',
        help_text='Descreva alergias ou escreva "Não possui"'
    )
    cirurgias_anteriores = models.TextField(
        blank=True,
        verbose_name='Cirurgias Anteriores'
    )

    # ----- Sinais vitais -----
    pressao_arterial = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Pressão Arterial',
        help_text='Ex: 120/80'
    )
    frequencia_cardiaca = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Frequência Cardíaca (bpm)'
    )
    frequencia_respiratoria = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Frequência Respiratória (irpm)'
    )
    temperatura = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        verbose_name='Temperatura (°C)'
    )
    saturacao_o2 = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Saturação de O₂ (%)'
    )
    peso = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso (kg)'
    )
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Altura (cm)'
    )

    # ----- Exame físico geral -----
    inspecao = models.TextField(blank=True, verbose_name='Inspeção')
    palpacao = models.TextField(blank=True, verbose_name='Palpação')
    ausculta = models.TextField(blank=True, verbose_name='Ausculta')

    # ----- Observações -----
    observacoes = models.TextField(blank=True, verbose_name='Observações Gerais')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_triagem']
        verbose_name = 'Triagem'
        verbose_name_plural = 'Triagens'

    def __str__(self):
        return f"Triagem — {self.prontuario.atleta.usuario.get_full_name()} ({self.data_triagem.strftime('%d/%m/%Y')})"


# ==============================================================================
# 3. OBJETIVOS TERAPÊUTICOS
# ==============================================================================
class Objetivo(models.Model):
    """
    Objetivos terapêuticos do paciente (SMART).
    Podem ser de curto, médio ou longo prazo.
    """
    PRAZO_CHOICES = [
        ('curto', 'Curto Prazo (até 2 semanas)'),
        ('medio', 'Médio Prazo (2 a 6 semanas)'),
        ('longo', 'Longo Prazo (mais de 6 semanas)'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('em_andamento', 'Em Andamento'),
        ('alcancado', 'Alcançado'),
        ('parcial', 'Parcialmente Alcançado'),
        ('nao_alcancado', 'Não Alcançado'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='objetivos',
        verbose_name='Prontuário'
    )

    prazo = models.CharField(
        max_length=10,
        choices=PRAZO_CHOICES,
        default='curto',
        verbose_name='Prazo'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Objetivo',
        help_text='Ex: Recuperar 100% da mobilidade do joelho'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição Detalhada',
        help_text='Detalhe como medir este objetivo (específico, mensurável, atingível, relevante, temporal)'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    percentual_alcancado = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='% Alcançado'
    )

    data_definicao = models.DateField(auto_now_add=True, verbose_name='Data de Definição')
    data_prevista = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data Prevista de Conclusão'
    )
    data_conclusao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )

    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='objetivos_criados',
        verbose_name='Criado por'
    )

    class Meta:
        ordering = ['prazo', 'data_definicao']
        verbose_name = 'Objetivo'
        verbose_name_plural = 'Objetivos'

    def __str__(self):
        return f"{self.titulo} — {self.get_status_display()}"


# ==============================================================================
# 4. MEDICAMENTOS
# ==============================================================================
class Medicamento(models.Model):
    """
    Medicamentos em uso pelo paciente.
    Inclui dose, frequência, via de administração e prescritor.
    """
    VIA_CHOICES = [
        ('oral', 'Oral'),
        ('sublingual', 'Sublingual'),
        ('topico', 'Tópico'),
        ('inalatoria', 'Inalatória'),
        ('injetavel', 'Injetável'),
        ('intravenosa', 'Intravenosa'),
        ('intramuscular', 'Intramuscular'),
        ('nasal', 'Nasal'),
        ('ocular', 'Ocular'),
        ('outra', 'Outra'),
    ]

    FREQUENCIA_CHOICES = [
        ('1x_dia', '1 vez ao dia'),
        ('2x_dia', '2 vezes ao dia'),
        ('3x_dia', '3 vezes ao dia'),
        ('4x_dia', '4 vezes ao dia'),
        ('6h_6h', 'De 6 em 6 horas'),
        ('8h_8h', 'De 8 em 8 horas'),
        ('12h_12h', 'De 12 em 12 horas'),
        ('se_necessario', 'Se necessário (SOS)'),
        ('semanal', 'Semanal'),
        ('outra', 'Outra'),
    ]

    STATUS_CHOICES = [
        ('ativo', 'Em uso'),
        ('suspenso', 'Suspenso'),
        ('finalizado', 'Finalizado'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='medicamentos',
        verbose_name='Prontuário'
    )

    # ----- Medicamento -----
    nome = models.CharField(max_length=200, verbose_name='Nome do Medicamento')
    principio_ativo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Princípio Ativo'
    )
    dosagem = models.CharField(
        max_length=100,
        verbose_name='Dosagem',
        help_text='Ex: 500mg, 20mg'
    )
    quantidade = models.CharField(
        max_length=100,
        verbose_name='Quantidade por Dose',
        help_text='Ex: 1 comprimido, 10 gotas, 2 jatos'
    )

    # ----- Administração -----
    via = models.CharField(
        max_length=20,
        choices=VIA_CHOICES,
        default='oral',
        verbose_name='Via de Administração'
    )
    frequencia = models.CharField(
        max_length=20,
        choices=FREQUENCIA_CHOICES,
        default='1x_dia',
        verbose_name='Frequência'
    )
    horarios = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Horários',
        help_text='Ex: 08h, 14h, 20h'
    )

    # ----- Prescrição -----
    prescritor = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Médico Prescritor'
    )
    crm_prescritor = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='CRM'
    )
    data_inicio = models.DateField(
        null=True,
        blank=True,
        verbose_name='Início do Uso'
    )
    data_fim = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fim do Uso'
    )

    # ----- Status -----
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativo',
        verbose_name='Status'
    )

    # ----- Observações -----
    indicacao = models.TextField(
        blank=True,
        verbose_name='Indicação / Motivo'
    )
    efeitos_colaterais = models.TextField(
        blank=True,
        verbose_name='Efeitos Colaterais Observados'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    # ----- Auditoria -----
    registrado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Registrado por'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'

    def __str__(self):
        return f"{self.nome} {self.dosagem} — {self.get_frequencia_display()}"


# ==============================================================================
# 5. CIF — Classificação Internacional de Funcionalidade (OBRIGATÓRIO)
# ==============================================================================
class AvaliacaoCIF(models.Model):
    """
    Avaliação baseada na CIF (Classificação Internacional de Funcionalidade,
    Incapacidade e Saúde) — padrão OMS.
    
    Avalia 3 grandes componentes:
    - Funções e Estruturas do Corpo (b)
    - Atividades e Participação (d)
    - Fatores Ambientais (e)
    
    Escala qualificadora: 0 = sem problema, 1 = leve, 2 = moderado,
    3 = grave, 4 = completo
    """
    QUALIFICADOR_CHOICES = [
        (0, '0 — Sem problema'),
        (1, '1 — Problema leve'),
        (2, '2 — Problema moderado'),
        (3, '3 — Problema grave'),
        (4, '4 — Problema completo'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='avaliacoes_cif',
        verbose_name='Prontuário'
    )
    data_avaliacao = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data da Avaliação'
    )
    avaliador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Avaliador'
    )

    # ============================================================
    # COMPONENTE 1 — FUNÇÕES E ESTRUTURAS DO CORPO (b)
    # ============================================================
    # Funções mentais (b1)
    b1_funcoes_mentais = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='b1 — Funções Mentais',
        help_text='Atenção, memória, emoções, percepção'
    )
    # Funções sensoriais e dor (b2)
    b2_funcoes_sensoriais = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='b2 — Funções Sensoriais e Dor',
        help_text='Visão, audição, tato, dor'
    )
    # Funções cardiovasculares e respiratórias (b4)
    b4_cardiorrespiratorias = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='b4 — Funções Cardiovasculares e Respiratórias',
        help_text='Coração, pulmão, pressão, respiração'
    )
    # Funções neuromusculoesqueléticas e movimento (b7)
    b7_neuromusculoesqueleticas = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='b7 — Funções Neuromusculoesqueléticas',
        help_text='Mobilidade, força, tônus, coordenação'
    )
    # Funções da pele (b8)
    b8_pele = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='b8 — Funções da Pele',
        help_text='Integridade da pele, cicatrização'
    )

    # ============================================================
    # COMPONENTE 2 — ATIVIDADES E PARTICIPAÇÃO (d)
    # ============================================================
    # Aprendizagem e aplicação do conhecimento (d1)
    d1_aprendizagem = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d1 — Aprendizagem e Conhecimento'
    )
    # Tarefas e demandas gerais (d2)
    d2_tarefas_gerais = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d2 — Tarefas e Demandas Gerais'
    )
    # Comunicação (d3)
    d3_comunicacao = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d3 — Comunicação'
    )
    # Mobilidade (d4)
    d4_mobilidade = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d4 — Mobilidade',
        help_text='Andar, correr, subir escadas, trocar posição'
    )
    # Cuidado pessoal (d5)
    d5_cuidado_pessoal = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d5 — Cuidado Pessoal',
        help_text='Banho, vestir, alimentação'
    )
    # Vida doméstica (d6)
    d6_vida_domestica = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d6 — Vida Doméstica'
    )
    # Relações interpessoais (d7)
    d7_relacoes = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d7 — Relações Interpessoais'
    )
    # Áreas principais da vida — esporte, lazer, educação (d8/d9)
    d8_areas_principais = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='d8/d9 — Esporte, Lazer, Educação'
    )

    # ============================================================
    # COMPONENTE 3 — FATORES AMBIENTAIS (e)
    # ============================================================
    # Produtos e tecnologia (e1)
    e1_produtos_tecnologia = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='e1 — Produtos e Tecnologia',
        help_text='Muletas, órteses, cadeira de rodas'
    )
    # Ambiente natural e mudanças (e2)
    e2_ambiente_natural = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='e2 — Ambiente Natural',
        help_text='Clima, temperatura, terreno'
    )
    # Apoio e relacionamentos (e3)
    e3_apoio_relacionamentos = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='e3 — Apoio e Relacionamentos',
        help_text='Família, amigos, técnicos, terapeutas'
    )
    # Atitudes (e4)
    e4_atitudes = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='e4 — Atitudes',
        help_text='Atitudes individuais e sociais'
    )
    # Serviços, sistemas e políticas (e5)
    e5_servicos_sistemas = models.IntegerField(
        choices=QUALIFICADOR_CHOICES,
        default=0,
        verbose_name='e5 — Serviços, Sistemas e Políticas',
        help_text='Acesso a saúde, educação, esporte'
    )

    # ============================================================
    # AVALIAÇÃO GLOBAL
    # ============================================================
    pontuacao_funcoes_corpo = models.IntegerField(
        default=0,
        verbose_name='Soma — Funções e Estruturas do Corpo'
    )
    pontuacao_atividades = models.IntegerField(
        default=0,
        verbose_name='Soma — Atividades e Participação'
    )
    pontuacao_fatores_ambientais = models.IntegerField(
        default=0,
        verbose_name='Soma — Fatores Ambientais'
    )
    pontuacao_global = models.IntegerField(
        default=0,
        verbose_name='Pontuação Global'
    )
    classificacao_global = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Classificação Global',
        help_text='Calculada automaticamente'
    )

    # ----- Observações do avaliador -----
    perfil_funcionalidade = models.TextField(
        blank=True,
        verbose_name='Perfil de Funcionalidade',
        help_text='Descreva o quadro geral do paciente segundo a CIF'
    )
    objetivos_cif = models.TextField(
        blank=True,
        verbose_name='Objetivos CIF',
        help_text='Objetivos baseados na avaliação CIF'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name = 'Avaliação CIF'
        verbose_name_plural = 'Avaliações CIF'

    def __str__(self):
        return f"CIF — {self.prontuario.atleta.usuario.get_full_name()} ({self.data_avaliacao.strftime('%d/%m/%Y')})"

    def save(self, *args, **kwargs):
        # Calcula somas
        self.pontuacao_funcoes_corpo = (
            self.b1_funcoes_mentais + self.b2_funcoes_sensoriais +
            self.b4_cardiorrespiratorias + self.b7_neuromusculoesqueleticas +
            self.b8_pele
        )
        self.pontuacao_atividades = (
            self.d1_aprendizagem + self.d2_tarefas_gerais + self.d3_comunicacao +
            self.d4_mobilidade + self.d5_cuidado_pessoal + self.d6_vida_domestica +
            self.d7_relacoes + self.d8_areas_principais
        )
        self.pontuacao_fatores_ambientais = (
            self.e1_produtos_tecnologia + self.e2_ambiente_natural +
            self.e3_apoio_relacionamentos + self.e4_atitudes + self.e5_servicos_sistemas
        )
        self.pontuacao_global = (
            self.pontuacao_funcoes_corpo +
            self.pontuacao_atividades +
            self.pontuacao_fatores_ambientais
        )

        # Classificação global baseada no total de problemas
        # Total máximo: 5*4 + 8*4 + 5*4 = 72
        pct = (self.pontuacao_global / 72) * 100
        if pct == 0:
            self.classificacao_global = 'Sem incapacidade'
        elif pct <= 15:
            self.classificacao_global = 'Incapacidade leve'
        elif pct <= 35:
            self.classificacao_global = 'Incapacidade moderada'
        elif pct <= 60:
            self.classificacao_global = 'Incapacidade grave'
        else:
            self.classificacao_global = 'Incapacidade completa'

        super().save(*args, **kwargs)


# ==============================================================================
# 6. AVALIAÇÃO CARDIORRESPIRATÓRIA
# ==============================================================================
class AvaliacaoCardiorrespiratoria(models.Model):
    """
    Avaliação específica para pacientes com condições cardiorrespiratórias:
    asma, bronquite, DPOC, pós-cirurgia cardíaca, insuficiência cardíaca.
    """
    CONDICAO_CHOICES = [
        ('asma', 'Asma'),
        ('bronquite', 'Bronquite'),
        ('dpoc', 'DPOC'),
        ('enfisema', 'Enfisema'),
        ('pos_cirurgia_cardiaca', 'Pós-cirurgia cardíaca'),
        ('insuficiencia_cardiaca', 'Insuficiência cardíaca'),
        ('hipertensao', 'Hipertensão'),
        ('arritmia', 'Arritmia'),
        ('infarto', 'Pós-infarto'),
        ('pneumonia', 'Pneumonia'),
        ('covid_longo', 'COVID longa'),
        ('outra', 'Outra'),
    ]

    TABAGISMO_CHOICES = [
        ('nunca', 'Nunca fumou'),
        ('ex_fumante', 'Ex-fumante'),
        ('fumante', 'Fumante atual'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='avaliacoes_cardiorrespiratorias',
        verbose_name='Prontuário'
    )
    data_avaliacao = models.DateTimeField(auto_now_add=True)
    avaliador = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Avaliador'
    )

    # ----- Condições -----
    condicao_principal = models.CharField(
        max_length=30,
        choices=CONDICAO_CHOICES,
        default='asma',
        verbose_name='Condição Principal'
    )
    outras_condicoes = models.TextField(
        blank=True,
        verbose_name='Outras Condições',
        help_text='Liste outras condições cardiorrespiratórias'
    )

    # ----- Histórico -----
    tempo_diagnostico = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Tempo desde o Diagnóstico'
    )
    tabagismo = models.CharField(
        max_length=20,
        choices=TABAGISMO_CHOICES,
        default='nunca',
        verbose_name='Tabagismo'
    )
    carga_tabagica = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Carga Tabágica',
        help_text='Ex: 20 maços/ano'
    )

    # ----- Sinais e sintomas -----
    frequencia_dispneia = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(4)],
        verbose_name='Frequência de Dispneia (0-4)',
        help_text='0 = ausente, 4 = incapacitante'
    )
    tosse = models.BooleanField(default=False, verbose_name='Tosse')
    tosse_produtiva = models.BooleanField(default=False, verbose_name='Tosse Produtiva')
    sibilos = models.BooleanField(default=False, verbose_name='Sibilos')
    cianose = models.BooleanField(default=False, verbose_name='Cianose')
    uso_musculos_acessorios = models.BooleanField(
        default=False,
        verbose_name='Uso de Músculos Acessórios'
    )
    limitacao_atividade = models.BooleanField(
        default=False,
        verbose_name='Limitação nas Atividades de Vida Diária'
    )

    # ----- Testes funcionais -----
    teste_caminhada_6min = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='Teste de Caminhada de 6 min (metros)'
    )
    spo2_reouso = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='SpO₂ em Repouso (%)'
    )
    spo2_esforco = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='SpO₂ após Esforço (%)'
    )
    fc_repouso = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='FC Repouso (bpm)'
    )
    fc_maxima = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='FC Máxima (bpm)'
    )
    pa_repouso = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='PA em Repouso'
    )
    escala_borg = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Escala de Borg (0-10)',
        help_text='Percepção subjetiva de esforço'
    )

    # ----- Exames complementares -----
    espirometria = models.TextField(
        blank=True,
        verbose_name='Espirometria',
        help_text='Resultados: VEF1, CVF, relação VEF1/CVF'
    )
    ecg = models.TextField(blank=True, verbose_name='ECG')
    ecocardiograma = models.TextField(blank=True, verbose_name='Ecocardiograma')
    raio_x_torax = models.TextField(blank=True, verbose_name='Raio-X de Tórax')

    # ----- Plano -----
    plano_cardiorrespiratorio = models.TextField(
        blank=True,
        verbose_name='Plano Fisioterapêutico Cardiorrespiratório'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_avaliacao']
        verbose_name = 'Avaliação Cardiorrespiratória'
        verbose_name_plural = 'Avaliações Cardiorrespiratórias'

    def __str__(self):
        return f"Cardio — {self.prontuario.atleta.usuario.get_full_name()} ({self.get_condicao_principal_display()})"


# ==============================================================================
# 7. ESCALAS DE RISCO
# ==============================================================================
class EscalaRisco(models.Model):
    """
    Escalas validadas de avaliação de risco.
    Exemplos: Berg (equilíbrio), Morse (queda), EVA (dor),
    Glasgow (consciência), Barthel (funcionalidade).
    """
    TIPO_ESCALA = [
        ('berg', 'Escala de Berg (Equilíbrio)'),
        ('morse', 'Escala de Morse (Risco de Queda)'),
        ('eva', 'Escala Visual Analógica (Dor)'),
        ('glasgow', 'Escala de Glasgow (Consciência)'),
        ('barthel', 'Índice de Barthel (Funcionalidade)'),
        ('mrc', 'MRC (Força Muscular 0-5)'),
        ('ashes', 'ASHES (Asma)'),
        ('borg', 'Escala de Borg (Esforço Percebido)'),
        ('nprs', 'NPRS (Dor Numérica)'),
        ('outra', 'Outra Escala'),
    ]

    NIVEL_RISCO_CHOICES = [
        ('baixo', 'Baixo Risco'),
        ('moderado', 'Risco Moderado'),
        ('alto', 'Alto Risco'),
        ('critico', 'Risco Crítico'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='escalas_risco',
        verbose_name='Prontuário'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_ESCALA,
        default='eva',
        verbose_name='Tipo de Escala'
    )
    data_aplicacao = models.DateTimeField(auto_now_add=True)
    aplicado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Aplicado por'
    )

    # ----- Resultado -----
    pontuacao = models.IntegerField(
        default=0,
        verbose_name='Pontuação Obtida'
    )
    pontuacao_maxima = models.IntegerField(
        default=100,
        verbose_name='Pontuação Máxima da Escala'
    )
    nivel_risco = models.CharField(
        max_length=20,
        choices=NIVEL_RISCO_CHOICES,
        default='baixo',
        verbose_name='Nível de Risco'
    )

    # ----- Interpretação -----
    interpretacao = models.TextField(
        blank=True,
        verbose_name='Interpretação'
    )
    conduta_recomendada = models.TextField(
        blank=True,
        verbose_name='Conduta Recomendada'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_aplicacao']
        verbose_name = 'Escala de Risco'
        verbose_name_plural = 'Escalas de Risco'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.prontuario.atleta.usuario.get_full_name()} ({self.get_nivel_risco_display()})"

    @property
    def percentual_risco(self):
        """Percentual da pontuação em relação ao máximo."""
        if not self.pontuacao_maxima:
            return 0
        return round((self.pontuacao / self.pontuacao_maxima) * 100, 1)


# ==============================================================================
# 8. RELATÓRIO DIÁRIO
# ==============================================================================
class RelatorioDiario(models.Model):
    """
    Relatório de cada sessão de fisioterapia.
    Registra o que foi feito, como o paciente reagiu e o plano para a próxima.
    """
    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='relatorios_diarios',
        verbose_name='Prontuário'
    )
    data_sessao = models.DateField(verbose_name='Data da Sessão')
    horario_inicio = models.TimeField(verbose_name='Início')
    horario_fim = models.TimeField(verbose_name='Término')

    # ----- Profissional -----
    fisioterapeuta = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='relatorios_diarios',
        verbose_name='Fisioterapeuta Responsável'
    )

    # ----- Procedimentos realizados -----
    procedimentos = models.TextField(
        verbose_name='Procedimentos Realizados',
        help_text='Liste as técnicas aplicadas (ex: TENS, cinesioterapia, mobilização)'
    )
    tecnicas_utilizadas = models.TextField(
        blank=True,
        verbose_name='Técnicas Utilizadas'
    )

    # ----- Avaliação do dia -----
    dor_inicio = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Dor no Início da Sessão (0-10)'
    )
    dor_fim = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Dor no Fim da Sessão (0-10)'
    )
    estado_geral = models.TextField(
        blank=True,
        verbose_name='Estado Geral do Paciente',
        help_text='Como o paciente chegou e como saiu'
    )
    reacao_paciente = models.TextField(
        blank=True,
        verbose_name='Reação ao Tratamento'
    )

    # ----- Sinais vitais -----
    pa_inicial = models.CharField(max_length=20, blank=True, verbose_name='PA Inicial')
    pa_final = models.CharField(max_length=20, blank=True, verbose_name='PA Final')
    fc_inicial = models.IntegerField(null=True, blank=True, verbose_name='FC Inicial')
    fc_final = models.IntegerField(null=True, blank=True, verbose_name='FC Final')
    spo2_inicial = models.IntegerField(null=True, blank=True, verbose_name='SpO₂ Inicial')
    spo2_final = models.IntegerField(null=True, blank=True, verbose_name='SpO₂ Final')

    # ----- Plano -----
    plano_proxima_sessao = models.TextField(
        blank=True,
        verbose_name='Plano para Próxima Sessão'
    )
    orientacoes_paciente = models.TextField(
        blank=True,
        verbose_name='Orientações ao Paciente',
        help_text='Exercícios para casa, cuidados, etc.'
    )
    observacoes = models.TextField(blank=True, verbose_name='Observações')

    # ----- Auditoria -----
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_sessao', '-horario_inicio']
        verbose_name = 'Relatório Diário'
        verbose_name_plural = 'Relatórios Diários'

    def __str__(self):
        return f"Relatório {self.data_sessao.strftime('%d/%m/%Y')} — {self.prontuario.atleta.usuario.get_full_name()}"

    @property
    def duracao_minutos(self):
        """Duração da sessão em minutos."""
        from datetime import datetime, date
        inicio = datetime.combine(date.today(), self.horario_inicio)
        fim = datetime.combine(date.today(), self.horario_fim)
        delta = fim - inicio
        return int(delta.total_seconds() / 60)


# ==============================================================================
# 9. ENCAMINHAMENTO MÉDICO
# ==============================================================================
class EncaminhamentoMedico(models.Model):
    """
    Encaminhamento do paciente para outro profissional de saúde
    (médico, ortopedista, cardiologista, etc.).
    """
    ESPECIALIDADE_CHOICES = [
        ('ortopedia', 'Ortopedia'),
        ('cardiologia', 'Cardiologia'),
        ('pneumologia', 'Pneumologia'),
        ('neurologia', 'Neurologia'),
        ('reumatologia', 'Reumatologia'),
        ('psiquiatria', 'Psiquiatria'),
        ('clinica_geral', 'Clínica Geral'),
        ('oftalmologia', 'Oftalmologia'),
        ('endocrinologia', 'Endocrinologia'),
        ('outra', 'Outra Especialidade'),
    ]

    URGENCIA_CHOICES = [
        ('eletivo', 'Eletivo'),
        ('prioritario', 'Prioritário'),
        ('urgente', 'Urgente'),
    ]

    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('agendado', 'Agendado'),
        ('realizado', 'Realizado'),
        ('cancelado', 'Cancelado'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='encaminhamentos',
        verbose_name='Prontuário'
    )
    data_encaminhamento = models.DateField(
        auto_now_add=True,
        verbose_name='Data do Encaminhamento'
    )

    # ----- Especialidade -----
    especialidade = models.CharField(
        max_length=30,
        choices=ESPECIALIDADE_CHOICES,
        default='ortopedia',
        verbose_name='Especialidade'
    )
    medico_encaminhado = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Médico'
    )
    urgencia = models.CharField(
        max_length=20,
        choices=URGENCIA_CHOICES,
        default='eletivo',
        verbose_name='Urgência'
    )

    # ----- Conteúdo -----
    motivo = models.TextField(
        verbose_name='Motivo do Encaminhamento'
    )
    resumo_clinico = models.TextField(
        blank=True,
        verbose_name='Resumo Clínico',
        help_text='Resumo do quadro para o médico'
    )
    exames_realizados = models.TextField(
        blank=True,
        verbose_name='Exames Realizados'
    )
    hipotese_diagnostica = models.TextField(
        blank=True,
        verbose_name='Hipótese Diagnóstica'
    )
    questionamentos = models.TextField(
        blank=True,
        verbose_name='Questionamentos ao Médico'
    )

    # ----- Retorno -----
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    data_retorno = models.DateField(null=True, blank=True, verbose_name='Data de Retorno')
    parecer_medico = models.TextField(
        blank=True,
        verbose_name='Parecer Médico'
    )
    conduta_sugerida = models.TextField(
        blank=True,
        verbose_name='Conduta Sugerida pelo Médico'
    )

    # ----- Auditoria -----
    encaminhado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Encaminhado por'
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data_encaminhamento']
        verbose_name = 'Encaminhamento Médico'
        verbose_name_plural = 'Encaminhamentos Médicos'

    def __str__(self):
        return f"Encaminhamento {self.get_especialidade_display()} — {self.prontuario.atleta.usuario.get_full_name()}"


# ==============================================================================
# 10. EXAMES
# ==============================================================================
class Exame(models.Model):
    """
    Exames complementares do paciente: laboratoriais, imagem, laudos.
    """
    TIPO_CHOICES = [
        ('raio_x', 'Raio-X'),
        ('ressonancia', 'Ressonância Magnética'),
        ('tomografia', 'Tomografia Computadorizada'),
        ('ultrassom', 'Ultrassonografia'),
        ('eletrocardiograma', 'Eletrocardiograma (ECG)'),
        ('ecocardiograma', 'Ecocardiograma'),
        ('espirometria', 'Espirometria'),
        ('laboratorial', 'Laboratorial'),
        ('cintilografia', 'Cintilografia'),
        ('densitometria', 'Densitometria Óssea'),
        ('eletroneuromiografia', 'Eletroneuromiografia'),
        ('outro', 'Outro'),
    ]

    STATUS_CHOICES = [
        ('solicitado', 'Solicitado'),
        ('agendado', 'Agendado'),
        ('realizado', 'Realizado'),
        ('laudo_disponivel', 'Laudo Disponível'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='exames',
        verbose_name='Prontuário'
    )
    tipo = models.CharField(
        max_length=30,
        choices=TIPO_CHOICES,
        default='raio_x',
        verbose_name='Tipo de Exame'
    )
    descricao = models.CharField(
        max_length=200,
        verbose_name='Descrição',
        help_text='Ex: Ressonância magnética do joelho direito'
    )

    # ----- Datas -----
    data_solicitacao = models.DateField(
        auto_now_add=True,
        verbose_name='Data da Solicitação'
    )
    data_realizacao = models.DateField(
        null=True,
        blank=True,
        verbose_name='Data de Realização'
    )

    # ----- Local -----
    local_realizacao = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Local de Realização'
    )

    # ----- Resultado -----
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='solicitado',
        verbose_name='Status'
    )
    laudo = models.TextField(
        blank=True,
        verbose_name='Laudo / Resultado'
    )
    conclusao = models.TextField(
        blank=True,
        verbose_name='Conclusão'
    )

    # ----- Anexo -----
    arquivo = models.FileField(
        upload_to='exames/%Y/%m/',
        null=True,
        blank=True,
        verbose_name='Arquivo do Exame'
    )

    # ----- Auditoria -----
    solicitado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Solicitado por'
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data_solicitacao']
        verbose_name = 'Exame'
        verbose_name_plural = 'Exames'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.prontuario.atleta.usuario.get_full_name()}"


# ==============================================================================
# 11. EVOLUÇÃO FISIOTERAPÊUTICA DETALHADA
# ==============================================================================
class EvolucaoFisioterapeutica(models.Model):
    """
    Evolução detalhada de fisioterapia — diferente da EvolucaoFisica
    (que é uma avaliação rápida de indicadores).
    
    Esta evolução descreve detalhadamente o quadro do paciente
    em cada atendimento, com avaliação funcional, conduta e plano.
    """
    TIPO_EVOLUCAO_CHOICES = [
        ('inicial', 'Avaliação Inicial'),
        ('intermediaria', 'Evolução Intermediária'),
        ('reavaliacao', 'Reavaliação'),
        ('alta', 'Alta Fisioterapêutica'),
    ]

    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='evolucoes_fisioterapeuticas',
        verbose_name='Prontuário'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_EVOLUCAO_CHOICES,
        default='intermediaria',
        verbose_name='Tipo de Evolução'
    )
    data = models.DateTimeField(auto_now_add=True, verbose_name='Data')
    fisioterapeuta = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Fisioterapeuta'
    )

    # ----- Subjetivo / Objetivo / Avaliação / Plano (SOAP) -----
    subjetivo = models.TextField(
        blank=True,
        verbose_name='S — Subjetivo',
        help_text='Queixas do paciente, relato'
    )
    objetivo = models.TextField(
        blank=True,
        verbose_name='O — Objetivo',
        help_text='Exame físico, medidas, testes'
    )
    avaliacao = models.TextField(
        blank=True,
        verbose_name='A — Avaliação',
        help_text='Análise do fisioterapeuta'
    )
    plano = models.TextField(
        blank=True,
        verbose_name='P — Plano',
        help_text='Conduta e planejamento'
    )

    # ----- Avaliações específicas -----
    escala_dor = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
        verbose_name='Dor (EVA 0-10)'
    )
    forca_muscular = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Força Muscular (MRC 0-5)'
    )
    amplitude_movimento = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Amplitude de Movimento'
    )
    testes_especiais = models.TextField(
        blank=True,
        verbose_name='Testes Especiais Realizados'
    )

    # ----- Conduta -----
    conduta = models.TextField(
        blank=True,
        verbose_name='Conduta Fisioterapêutica',
        help_text='O que foi feito nesta sessão'
    )
    resposta_ao_tratamento = models.TextField(
        blank=True,
        verbose_name='Resposta ao Tratamento'
    )

    # ----- Situação -----
    paciente_estavel = models.BooleanField(
        default=True,
        verbose_name='Paciente Estável'
    )
    necessita_encaminhamento = models.BooleanField(
        default=False,
        verbose_name='Necessita Encaminhamento'
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']
        verbose_name = 'Evolução Fisioterapêutica'
        verbose_name_plural = 'Evoluções Fisioterapêuticas'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.prontuario.atleta.usuario.get_full_name()} ({self.data.strftime('%d/%m/%Y')})"


# ==============================================================================
# 12. 🔥 NOVO — COMPARTILHAMENTO DE PRONTUÁRIO COM O TÉCNICO
# ==============================================================================
class CompartilhamentoProntuario(models.Model):
    """
    Permite que o fisioterapeuta compartilhe o prontuário com um técnico.
    O técnico visualiza em modo leitura e (opcionalmente) adiciona
    observações de treino que enriquecem o tratamento clínico.
    """
    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='compartilhamentos',
        verbose_name='Prontuário'
    )
    tecnico = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='prontuarios_compartilhados',
        verbose_name='Técnico'
    )
    liberado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='prontuarios_liberados',
        verbose_name='Liberado por'
    )
    liberado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Liberado em'
    )
    pode_comentar = models.BooleanField(
        default=True,
        help_text='Se marcado, o técnico pode adicionar observações de treino',
        verbose_name='Pode comentar'
    )
    observacao_liberacao = models.TextField(
        blank=True,
        help_text='Mensagem opcional do fisio para o técnico (ex: foco em fortalecer quadríceps)',
        verbose_name='Observação da Liberação'
    )
    ativo = models.BooleanField(
        default=True,
        verbose_name='Ativo'
    )

    class Meta:
        unique_together = ['prontuario', 'tecnico']
        ordering = ['-liberado_em']
        verbose_name = 'Compartilhamento de Prontuário'
        verbose_name_plural = 'Compartilhamentos de Prontuário'

    def __str__(self):
        return f"{self.prontuario.numero_prontuario} → {self.tecnico.get_full_name() or self.tecnico.username}"


# ==============================================================================
# 13. 🔥 NOVO — OBSERVAÇÃO DE TREINO DO TÉCNICO
# ==============================================================================
class ObservacaoTecnico(models.Model):
    """
    Registro do técnico sobre como o atleta se saiu no treino/atividade.
    Integra dados de desempenho esportivo com o prontuário clínico,
    criando um ciclo fechado de reabilitação.
    """
    TIPO_OBSERVACAO = [
        ('treino', 'Treino Regular'),
        ('recuperacao', 'Sessão de Recuperação'),
        ('ocorrencia', 'Ocorrência / Incidente'),
        ('desempenho', 'Avaliação de Desempenho'),
        ('comportamento', 'Comportamento / Atitude'),
        ('outro', 'Outro'),
    ]

    NIVEL_IMPACTO = [
        ('positivo', 'Impacto Positivo'),
        ('neutro', 'Neutro'),
        ('atencao', 'Requer Atenção'),
        ('critico', 'Crítico'),
    ]

    compartilhamento = models.ForeignKey(
        CompartilhamentoProntuario,
        on_delete=models.CASCADE,
        related_name='observacoes',
        verbose_name='Compartilhamento'
    )
    prontuario = models.ForeignKey(
        Prontuario,
        on_delete=models.CASCADE,
        related_name='observacoes_tecnico',
        verbose_name='Prontuário'
    )
    tecnico = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='observacoes_registradas',
        verbose_name='Técnico'
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_OBSERVACAO,
        default='treino',
        verbose_name='Tipo de Observação'
    )
    nivel_impacto = models.CharField(
        max_length=20,
        choices=NIVEL_IMPACTO,
        default='neutro',
        verbose_name='Nível de Impacto'
    )
    titulo = models.CharField(
        max_length=200,
        verbose_name='Título'
    )
    descricao = models.TextField(
        verbose_name='Descrição'
    )

    # Métricas quantitativas (0-10)
    desempenho_treino = models.IntegerField(
        null=True,
        blank=True,
        help_text='Como o atleta se saiu no treino (0-10)',
        verbose_name='Desempenho no Treino'
    )
    dor_relatada = models.IntegerField(
        null=True,
        blank=True,
        help_text='Dor relatada pelo atleta durante o treino (0-10)',
        verbose_name='Dor Relatada'
    )
    aderencia = models.IntegerField(
        null=True,
        blank=True,
        help_text='Adesão ao programa proposto (0-10)',
        verbose_name='Adesão ao Programa'
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Observação do Técnico'
        verbose_name_plural = 'Observações dos Técnicos'

    def __str__(self):
        return f"{self.get_tipo_display()} — {self.titulo}"

    @property
    def cor_impacto(self):
        return {
            'positivo': 'success',
            'neutro': 'secondary',
            'atencao': 'warning',
            'critico': 'danger',
        }.get(self.nivel_impacto, 'secondary')

    @property
    def icone_tipo(self):
        return {
            'treino': 'fa-running',
            'recuperacao': 'fa-heartbeat',
            'ocorrencia': 'fa-exclamation-triangle',
            'desempenho': 'fa-chart-line',
            'comportamento': 'fa-smile',
            'outro': 'fa-info-circle',
        }.get(self.tipo, 'fa-info-circle')