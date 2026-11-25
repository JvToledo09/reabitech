/**
 * REABITECH - Charts & Graphs
 * Versão corrigida - Setembro 2026
 */

// ============================================
// CONFIGURAÇÕES GLOBAIS DO CHART.JS
// ============================================
Chart.defaults.font.family = "'Poppins', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#5A6461';

// ============================================
// PALETA DE CORES CENTRALIZADA
// ============================================
const THEME = {
    primary:   '#2BA181',
    secondary: '#5A6461',
    danger:    '#dc3545',
    warning:   '#ffc107',
    info:      '#0dcaf0',
    success:   '#28a745',
    purple:    '#6f42c1',
    blue:      '#0d6efd',

    // Versões com transparência
    primarySoft:   'rgba(43, 161, 129, 0.1)',
    dangerSoft:    'rgba(220, 53, 69, 0.1)',
    warningSoft:   'rgba(255, 193, 7, 0.1)',
    infoSoft:      'rgba(13, 202, 240, 0.1)',
    purpleSoft:    'rgba(111, 66, 193, 0.1)',
};

// ============================================
// UTILITÁRIO: Detecta se está em dark mode
// ============================================
function isDarkMode() {
    return document.documentElement.getAttribute('data-bs-theme') === 'dark';
}

// ============================================
// UTILITÁRIO: Lê valores de json_script com segurança
// ============================================
function getJSON(id) {
    const el = document.getElementById(id);
    return el ? JSON.parse(el.textContent) : [];
}

// ============================================
// GRÁFICO DE EVOLUÇÃO (Linha)
// Use: createEvolutionChart('meuCanvasId', dados, labels)
// ============================================
function createEvolutionChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const dark = isDarkMode();

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels || ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4', 'Semana 5', 'Semana 6'],
            datasets: [
                {
                    label: 'Dor',
                    data: data?.dor || [8, 7, 6, 5, 4, 3],
                    borderColor: THEME.danger,
                    backgroundColor: THEME.dangerSoft,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: THEME.danger,
                },
                {
                    label: 'Desempenho',
                    data: data?.desempenho || [4, 5, 6, 7, 8, 9],
                    borderColor: THEME.primary,
                    backgroundColor: THEME.primarySoft,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: THEME.primary,
                },
                {
                    label: 'Mobilidade',
                    data: data?.mobilidade || [5, 6, 7, 7, 8, 9],
                    borderColor: THEME.warning,
                    backgroundColor: THEME.warningSoft,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: THEME.warning,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        color: dark ? '#e0e0e0' : '#333'
                    }
                },
                tooltip: {
                    backgroundColor: dark ? '#1a1a2e' : 'white',
                    titleColor: dark ? 'white' : '#333',
                    bodyColor: dark ? '#ccc' : '#666',
                    borderColor: dark ? '#333' : '#eee',
                    borderWidth: 1,
                    cornerRadius: 12,
                    padding: 12,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' },
                    ticks: { color: dark ? '#999' : '#666' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: dark ? '#999' : '#666' }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE DESEMPENHO (Barras)
// Use: createPerformanceChart('meuCanvasId', dados, labels)
// ============================================
function createPerformanceChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const dark = isDarkMode();

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels || ['Futebol', 'Vôlei', 'Basquete', 'Natação', 'Atletismo'],
            datasets: [{
                label: 'Desempenho Médio',
                data: data || [7.5, 8.2, 6.8, 9.0, 7.8],
                backgroundColor: [
                    THEME.primary,
                    THEME.secondary,
                    THEME.primary,
                    THEME.secondary,
                    THEME.primary
                ],
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: { color: dark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' },
                    ticks: { color: dark ? '#999' : '#666' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: dark ? '#999' : '#666' }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE SAÚDE MENTAL (Radar)
// Use: createMentalHealthChart('meuCanvasId', [ansiedade, motivacao, estresse, autoestima, sono])
// ============================================
function createMentalHealthChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const dark = isDarkMode();

    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Ansiedade', 'Motivação', 'Estresse', 'Autoestima', 'Qualidade do Sono'],
            datasets: [{
                label: 'Avaliação Atual',
                data: data || [4, 8, 3, 7, 6],
                backgroundColor: 'rgba(43, 161, 129, 0.2)',
                borderColor: THEME.primary,
                pointBackgroundColor: THEME.primary,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: THEME.primary,
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: dark ? '#e0e0e0' : '#333' }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 10,
                    ticks: {
                        stepSize: 2,
                        color: dark ? '#999' : '#666',
                        backdropColor: 'transparent'
                    },
                    grid: { color: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
                    angleLines: { color: dark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)' },
                    pointLabels: {
                        color: dark ? '#e0e0e0' : '#333',
                        font: { size: 11 }
                    }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE RECUPERAÇÃO (Doughnut)
// Use: createRecoveryChart('meuCanvasId', 75)  // percentual de 0 a 100
// ============================================
function createRecoveryChart(canvasId, percent) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    const dark = isDarkMode();
    const value = Math.min(Math.max(percent || 0, 0), 100);
    const color = value >= 70 ? THEME.primary : value >= 40 ? THEME.warning : THEME.danger;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Recuperado', 'Restante'],
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [color, dark ? '#333' : '#e9ecef'],
                borderWidth: 0,
                hoverOffset: 10,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed + '%';
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'textCenter',
            beforeDraw: function(chart) {
                const { width, height, ctx } = chart;
                ctx.save();
                ctx.font = 'bold 28px Poppins, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = dark ? 'white' : '#333';
                ctx.fillText(value + '%', width / 2, height / 2 - 5);
                ctx.font = '12px Poppins, sans-serif';
                ctx.fillStyle = dark ? '#999' : '#666';
                ctx.fillText('Recuperado', width / 2, height / 2 + 25);
                ctx.restore();
            }
        }]
    });
}

// ============================================
// EXPORT GLOBAL
// ============================================
window.ReabiTechCharts = {
    THEME,
    isDarkMode,
    getJSON,
    createEvolutionChart,
    createPerformanceChart,
    createMentalHealthChart,
    createRecoveryChart
};

// ============================================
// LOG DE INICIALIZAÇÃO
// ============================================
console.log('📊 REABITECH Charts carregado. Funções disponíveis em window.ReabiTechCharts');