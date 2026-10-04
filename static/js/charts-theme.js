/* ============================================================================
 * REABITECH — Charts Theme Helper
 * Reconfigura o visual dos gráficos Chart.js conforme o tema (light/dark).
 * Uso: depois de criar um Chart, chame window.ReabitechCharts.aplicarTema(chart)
 * ==========================================================================*/

(function() {
    'use strict';

    // ---------- Paletas ----------
    const PALETA = {
        light: {
            texto: '#0f172a',
            textoSuave: '#64748b',
            grid: 'rgba(15, 23, 42, 0.08)',
            tooltipBg: 'rgba(15, 23, 42, 0.92)',
            tooltipTexto: '#ffffff',
            border: 'rgba(15, 23, 42, 0.12)',
        },
        dark: {
            texto: '#e2e8f0',
            textoSuave: '#94a3b8',
            grid: 'rgba(226, 232, 240, 0.10)',
            tooltipBg: 'rgba(15, 23, 42, 0.95)',
            tooltipTexto: '#f1f5f9',
            border: 'rgba(226, 232, 240, 0.15)',
        },
    };

    // ---------- Cores da marca ----------
    const CORES_MARCA = [
        '#2BA181', '#0dcaf0', '#7c3aed', '#f59e0b', '#ef4444',
        '#10b981', '#3b82f6', '#ec4899', '#8b5cf6', '#14b8a6',
    ];

    function temaAtual() {
        return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    }

    function paletaAtual() {
        return PALETA[temaAtual()];
    }

    // ---------- Aplicar tema a um chart ----------
    function aplicarTema(chart) {
        if (!chart || !chart.options) return;
        const p = paletaAtual();

        // Fonte global
        if (!chart.options.font) chart.options.font = {};
        chart.options.font.family = "'Inter', -apple-system, sans-serif";
        chart.options.color = p.texto;

        // Legendas
        if (chart.options.plugins && chart.options.plugins.legend) {
            chart.options.plugins.legend.labels = Object.assign(
                {},
                chart.options.plugins.legend.labels,
                { color: p.texto, font: { family: "'Inter', sans-serif", size: 12, weight: '600' } }
            );
        }

        // Tooltips
        if (chart.options.plugins && chart.options.plugins.tooltip) {
            chart.options.plugins.tooltip = Object.assign(
                {},
                chart.options.plugins.tooltip,
                {
                    backgroundColor: p.tooltipBg,
                    titleColor: p.tooltipTexto,
                    bodyColor: p.tooltipTexto,
                    borderColor: p.border,
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                }
            );
        }

        // Eixos (x e y)
        ['x', 'y'].forEach(eixo => {
            if (chart.options.scales && chart.options.scales[eixo]) {
                const s = chart.options.scales[eixo];
                s.ticks = Object.assign({}, s.ticks, { color: p.textoSuave });
                s.grid = Object.assign({}, s.grid, { color: p.grid, borderColor: p.grid });
                if (s.title) s.title.color = p.textoSuave;
            }
        });

        chart.update('none');
    }

    // ---------- Aplicar a todos os charts registrados ----------
    function aplicarTemaTodos() {
        if (!window.Chart || !window.Chart.instances) return;
        Object.values(window.Chart.instances).forEach(aplicarTema);
    }

    // ---------- Observar mudanças de tema ----------
    function observarTema() {
        const obs = new MutationObserver((mutations) => {
            mutations.forEach(m => {
                if (m.attributeName === 'data-theme') {
                    // Pequeno delay pra garantir que o CSS ja aplicou
                    setTimeout(aplicarTemaTodos, 50);
                }
            });
        });
        obs.observe(document.documentElement, { attributes: true });
    }

    // ---------- Cores padrao ----------
    function corPorIndice(i) {
        return CORES_MARCA[i % CORES_MARCA.length];
    }

    // ---------- API publica ----------
    window.ReabitechCharts = {
        aplicarTema,
        aplicarTemaTodos,
        temaAtual,
        paletaAtual,
        corPorIndice,
        CORES_MARCA,
    };

    // Auto-init quando o DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observarTema);
    } else {
        observarTema();
    }
})();
