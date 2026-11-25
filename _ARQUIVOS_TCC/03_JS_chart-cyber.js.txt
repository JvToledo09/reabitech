(function() {
    'use strict';

    function getThemeColors() {
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        return {
            text: isDark ? '#cbd5e1' : '#475569',
            textMuted: isDark ? '#94a3b8' : '#64748b',
            grid: isDark ? 'rgba(148, 163, 184, 0.1)' : 'rgba(15, 23, 42, 0.08)',
            tooltipBg: isDark ? '#1e293b' : '#ffffff',
            tooltipText: isDark ? '#f1f5f9' : '#0f172a'
        };
    }

    function applyColorsToChart(chart) {
        const colors = getThemeColors();
        
        if (chart.options) {
            if (chart.options.plugins && chart.options.plugins.legend && chart.options.plugins.legend.labels) {
                chart.options.plugins.legend.labels.color = colors.text;
            }
            if (chart.options.plugins && chart.options.plugins.tooltip) {
                chart.options.plugins.tooltip.backgroundColor = colors.tooltipBg;
                chart.options.plugins.tooltip.titleColor = colors.tooltipText;
                chart.options.plugins.tooltip.bodyColor = colors.text;
            }
            if (chart.options.scales) {
                Object.keys(chart.options.scales).forEach(axis => {
                    const scale = chart.options.scales[axis];
                    if (scale.ticks) scale.ticks.color = colors.text;
                    if (scale.grid) scale.grid.color = colors.grid;
                    if (scale.pointLabels) scale.pointLabels.color = colors.text;
                });
            }
        }
        chart.update('none');
    }

    function setupChartInterceptor() {
        if (typeof Chart === 'undefined') {
            setTimeout(setupChartInterceptor, 500);
            return;
        }

        const OriginalChart = Chart;
        window.Chart = new Proxy(OriginalChart, {
            construct: function(target, args) {
                const canvas = args[0];
                const config = args[1];
                const colors = getThemeColors();

                if (config.options) {
                    config.options.color = colors.text;
                    config.options.borderColor = colors.grid;
                    config.options.font = config.options.font || {};
                    config.options.font.family = "'Inter', sans-serif";
                }

                const chartInstance = new target(canvas, config);
                applyColorsToChart(chartInstance);

                setTimeout(() => {
                    if (chartInstance && chartInstance.canvas) {
                        chartInstance.canvas._chartInstance = chartInstance;
                    }
                }, 10);

                return chartInstance;
            }
        });

        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.attributeName === 'data-theme') {
                    const allCanvases = document.querySelectorAll('canvas');
                    allCanvases.forEach(canvas => {
                        let chart = canvas._chartInstance;
                        if (!chart && typeof Chart !== 'undefined' && Chart.getChart) {
                            chart = Chart.getChart(canvas);
                        }
                        if (chart) applyColorsToChart(chart);
                    });
                }
            });
        });

        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupChartInterceptor);
    } else {
        setupChartInterceptor();
    }
})();
