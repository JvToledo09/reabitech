/**
 * REABITECH - Charts & Graphs
 */

Chart.defaults.font.family = "'Poppins', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.color = '#5A6461';

// ============================================
// FUNÇÃO PARA CRIAR GRÁFICO DE EVOLUÇÃO
// ============================================
function createEvolutionChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels || ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4', 'Semana 5', 'Semana 6'],
            datasets: [
                {
                    label: 'Dor',
                    data: data?.dor || [8, 7, 6, 5, 4, 3],
                    borderColor: '#dc3545',
                    backgroundColor: 'rgba(220, 53, 69, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#dc3545',
                },
                {
                    label: 'Desempenho',
                    data: data?.desempenho || [4, 5, 6, 7, 8, 9],
                    borderColor: '#2BA181',
                    backgroundColor: 'rgba(43, 161, 129, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#2BA181',
                },
                {
                    label: 'Mobilidade',
                    data: data?.mobilidade || [5, 6, 7, 7, 8, 9],
                    borderColor: '#ffc107',
                    backgroundColor: 'rgba(255, 193, 7, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#ffc107',
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
                        color: isDark ? '#e0e0e0' : '#333'
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? '#1a1a2e' : 'white',
                    titleColor: isDark ? 'white' : '#333',
                    bodyColor: isDark ? '#ccc' : '#666',
                    borderColor: isDark ? '#333' : '#eee',
                    borderWidth: 1,
                    cornerRadius: 12,
                    padding: 12,
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: {
                        color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        color: isDark ? '#999' : '#666'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: isDark ? '#999' : '#666'
                    }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE DESEMPENHO POR MODALIDADE (Barras)
// ============================================
function createPerformanceChart(canvasId, data, labels) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels || ['Futebol', 'Vôlei', 'Basquete', 'Natação', 'Atletismo'],
            datasets: [{
                label: 'Desempenho Médio',
                data: data || [7.5, 8.2, 6.8, 9.0, 7.8],
                backgroundColor: [
                    '#2BA181',
                    '#5A6461',
                    '#2BA181',
                    '#5A6461',
                    '#2BA181'
                ],
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 10,
                    grid: {
                        color: isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)'
                    },
                    ticks: {
                        color: isDark ? '#999' : '#666'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: isDark ? '#999' : '#666'
                    }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE SAÚDE MENTAL (Radar)
// ============================================
function createMentalHealthChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    
    return new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Ansiedade', 'Motivação', 'Estresse', 'Autoestima', 'Qualidade do Sono'],
            datasets: [{
                label: 'Avaliação Atual',
                data: data || [4, 8, 3, 7, 6],
                backgroundColor: 'rgba(43, 161, 129, 0.2)',
                borderColor: '#2BA181',
                pointBackgroundColor: '#2BA181',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#2BA181',
                fill: true,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: isDark ? '#e0e0e0' : '#333'
                    }
                }
            },
            scales: {
                r: {
                    beginAtZero: true,
                    max: 10,
                    ticks: {
                        stepSize: 2,
                        color: isDark ? '#999' : '#666',
                        backdropColor: 'transparent'
                    },
                    grid: {
                        color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                    },
                    angleLines: {
                        color: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'
                    },
                    pointLabels: {
                        color: isDark ? '#e0e0e0' : '#333',
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

// ============================================
// GRÁFICO DE RECUPERAÇÃO (Doughnut)
// ============================================
function createRecoveryChart(canvasId, percent) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;
    
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const value = Math.min(Math.max(percent || 75, 0), 100);
    const color = value >= 70 ? '#2BA181' : value >= 40 ? '#ffc107' : '#dc3545';
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Recuperado', 'Restante'],
            datasets: [{
                data: [value, 100 - value],
                backgroundColor: [color, isDark ? '#333' : '#e9ecef'],
                borderWidth: 0,
                hoverOffset: 10,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '75%',
            plugins: {
                legend: {
                    display: false
                },
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
                const text = `${value}%`;
                ctx.font = 'bold 28px Poppins, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = isDark ? 'white' : '#333';
                ctx.fillText(text, width / 2, height / 2 - 5);
                ctx.font = '12px Poppins, sans-serif';
                ctx.fillStyle = isDark ? '#999' : '#666';
                ctx.fillText('Recuperado', width / 2, height / 2 + 25);
                ctx.restore();
            }
        }]
    });
}

// ============================================
// AUTO-INIT: Inicializa os gráficos automaticamente
// ============================================
document.addEventListener("DOMContentLoaded", function() {
    // Busca todos os gráficos pelos IDs e inicia
    const evolutionEl = document.getElementById('evolutionChart');
    if (evolutionEl) {
        // Pega os dados do atributo data, se existir
        const dataAttr = evolutionEl.getAttribute('data-data');
        const labelsAttr = evolutionEl.getAttribute('data-labels');
        createEvolutionChart('evolutionChart', dataAttr ? JSON.parse(dataAttr) : null, labelsAttr ? JSON.parse(labelsAttr) : null);
    }

    const recoveryEl = document.getElementById('recoveryChart');
    if (recoveryEl) {
        // Pega o valor do atributo data-percent para inicializar
        const percent = recoveryEl.getAttribute('data-percent') || 75;
        createRecoveryChart('recoveryChart', parseFloat(percent));
    }

    const performanceEl = document.getElementById('performanceChart');
    if (performanceEl) {
        const dataAttr = performanceEl.getAttribute('data-data');
        const labelsAttr = performanceEl.getAttribute('data-labels');
        createPerformanceChart('performanceChart', dataAttr ? JSON.parse(dataAttr) : null, labelsAttr ? JSON.parse(labelsAttr) : null);
    }

    const mentalEl = document.getElementById('mentalHealthChart');
    if (mentalEl) {
        const dataAttr = mentalEl.getAttribute('data-data');
        createMentalHealthChart('mentalHealthChart', dataAttr ? JSON.parse(dataAttr) : null);
    }
});

// ============================================
// EXPORT
// ============================================
window.ReabiTechCharts = {
    createEvolutionChart,
    createPerformanceChart,
    createMentalHealthChart,
    createRecoveryChart
};