
// ==========================================================================
// REABITECH - PREMIUM CHARTS GLOBAL SETTINGS
// Intercepta TODOS os graficos do sistema e aplica efeitos incriveis.
// ==========================================================================

if (typeof Chart !== 'undefined') {
    // --- 1. FONTE E CORES GLOBAIS ---
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 13;
    Chart.defaults.font.weight = '600';
    Chart.defaults.color = 'rgba(148, 163, 184, 0.9)'; // Cinza claro para os eixos

    // --- 2. ANIMACOES CINEMATOGRAFICAS ---
    Chart.defaults.animation.duration = 1500;
    Chart.defaults.animation.easing = 'easeOutQuart';
    // Animacao em cascata (cada ponto/barrinha aparece em sequencia)
    Chart.defaults.animation.delay = (context) => {
        if (context.type === 'data' && context.mode === 'default') {
            return context.dataIndex * 50; // 50ms de delay para cada item
        }
        return 0;
    };

    // --- 3. TOOLTIPS PREMIUM ---
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(15, 23, 42, 0.95)';
    Chart.defaults.plugins.tooltip.titleFont = { size: 14, weight: 'bold', family: "'Inter', sans-serif" };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 13, family: "'Inter', sans-serif" };
    Chart.defaults.plugins.tooltip.padding = 16;
    Chart.defaults.plugins.tooltip.cornerRadius = 12;
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.tooltip.boxPadding = 6;
    Chart.defaults.plugins.tooltip.usePointStyle = true;
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(52, 211, 153, 0.3)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;

    // --- 4. LINHAS SUAVES E GROSSAS ---
    Chart.defaults.elements.line.tension = 0.4;
    Chart.defaults.elements.line.borderWidth = 4;
    Chart.defaults.elements.line.fill = true;
    
    // --- 5. PONTOS NAS LINHAS (Circulos brilhantes) ---
    Chart.defaults.elements.point.radius = 5;
    Chart.defaults.elements.point.hoverRadius = 9;
    Chart.defaults.elements.point.hoverBorderWidth = 3;
    Chart.defaults.elements.point.hoverBorderColor = '#ffffff';
    Chart.defaults.elements.point.backgroundColor = '#10b981';
    Chart.defaults.elements.point.borderWidth = 0;

    // --- 6. BARRAS ARREDONDADAS ---
    Chart.defaults.elements.bar.borderRadius = 8;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.bar.maxBarThickness = 40;


    // --- 7. EIXOS E GRID ---
    // Configuracoes defensivas para diferentes versoes do Chart.js.

    const linearDefaults = Chart.defaults.scales?.linear;
    const categoryDefaults = Chart.defaults.scales?.category;

    if (linearDefaults?.grid) {
        linearDefaults.grid.color = 'rgba(255, 255, 255, 0.04)';
        linearDefaults.grid.tickLength = 0;
    }

    if (linearDefaults?.border) {
        linearDefaults.border.display = false;
        linearDefaults.border.dash = [5, 5];
    }

    if (categoryDefaults?.grid) {
        categoryDefaults.grid.display = false;
    }

    if (categoryDefaults?.border) {
        categoryDefaults.border.display = false;
    }

    // --- 8. INTERACAO ---
    Chart.defaults.interaction.mode = 'index';
    Chart.defaults.interaction.intersect = false;

    // --- 9. PLUGIN DE GRADIENTE E GLOW (O Segredo) ---
    const PremiumGlowPlugin = {
        id: 'premiumGlowPlugin',
        beforeDatasetsDraw(chart, args, options) {
            const { ctx, chartArea } = chart;
            if (!chartArea) return;

            chart.data.datasets.forEach((dataset, i) => {
                // Se for grafico de linha
                if (chart.config.type === 'line' && dataset.fill !== false) {
                    // Cria o gradiente vertical
                    const gradient = ctx.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                    
                    // Cores base (verde, azul, roxo, amarelo)
                    const colors = [
                        '16, 185, 129',  // Verde
                        '59, 130, 246',  // Azul
                        '139, 92, 246',  // Roxo
                        '245, 158, 11'   // Amarelo
                    ];
                    const rgb = colors[i % colors.length];
                    
                    gradient.addColorStop(0, `rgba(${rgb}, 0.35)`);
                    gradient.addColorStop(1, `rgba(${rgb}, 0.0)`);
                    
                    dataset.backgroundColor = gradient;
                }
                
                // Adiciona um brilho neon na linha principal
                if (chart.config.type === 'line') {
                    ctx.shadowColor = dataset.borderColor || 'rgba(16, 185, 129, 0.5)';
                    ctx.shadowBlur = 15;
                }
            });
        },
        afterDatasetsDraw(chart) {
            // Remove o brilho para nao afetar o resto
            chart.ctx.shadowBlur = 0;
        }
    };

    // Registra o Plugin Globalmente
    Chart.register(PremiumGlowPlugin);
    
    // Configuracoes globais para Pie e Doughnut ficarem bonitos
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;
    Chart.defaults.plugins.legend.labels.font = { size: 13, weight: '600' };
    
    console.log("Premium Charts Loaded: Gradients, Animations & Glow Active.");
}
