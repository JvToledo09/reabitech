/* ==============================================================================
   REABITECH - PREMIUM EFFECTS JS
   Aplica automaticamente: tilt 3D, glow no mouse, data-lenis-prevent
   Nao precisa editar templates - tudo via JS
   ============================================================================== */

(function() {
    'use strict';

    // ==========================================================================
    // CONFIG
    // ==========================================================================
    const TILT_MAX = 6;                 // graus maximos
    const TILT_PERSPECTIVE = 1000;
    const TILT_SCALE = 1.02;
    const TILT_TRANSITION = 'transform 0.35s cubic-bezier(0.22, 1, 0.36, 1)';
    const TOUCH = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ==========================================================================
    // 1. SCROLL INTERNO DO SIDEBAR (data-lenis-prevent)
    // ==========================================================================
    function fixLenisPrevent() {
        // Elementos com scroll interno que o Lenis estava bloqueando
        const seletores = [
            '.sidebar',
            '.chat-mensagens',
            '.chat-sidebar-list',
            '.destinatarios-list',
            '.dropdown-menu',
            '.modal-body',
            '.table-responsive',
            '[style*="overflow-y: auto"]',
            '[style*="overflow-y:auto"]',
            '[style*="overflow-y: scroll"]',
            '[style*="overflow-y:scroll"]',
            '.chat-sidebar',
            '.chat-main',
            '.timeline-container',
            '.heat-bars',
        ];

        seletores.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                el.setAttribute('data-lenis-prevent', '');
                el.setAttribute('data-lenis-prevent-wheel', '');
                el.setAttribute('data-lenis-prevent-touch', '');
            });
        });

        console.log('[Premium] data-lenis-prevent aplicado em', seletores.length, 'seletores');
    }

    // ==========================================================================
    // 2. TILT 3D NOS CARDS
    // ==========================================================================
    const SELETORES_TILT = [
        '.card-modern',
        '.stat-card',
        '.kpi-card',
        '.chart-card',
        '.card-glass',
        '.rank-item',
    ];

    function aplicarTilt(el) {
        // Evita aplicar 2x
        if (el.dataset.tiltApplied) return;
        el.dataset.tiltApplied = '1';

        // Adiciona classes CSS
        el.classList.add('tilt-3d', 'tilt-glow');

        // Persiste o transform base
        let baseTransform = el.style.transform || '';

        function onMove(e) {
            if (REDUCED_MOTION || TOUCH) return;
            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const pctX = (x / rect.width) - 0.5;
            const pctY = (y / rect.height) - 0.5;

            const rotX = (-pctY * TILT_MAX).toFixed(2);
            const rotY = (pctX * TILT_MAX).toFixed(2);

            el.style.transform =
                `perspective(${TILT_PERSPECTIVE}px) ` +
                `rotateX(${rotX}deg) ` +
                `rotateY(${rotY}deg) ` +
                `scale(${TILT_SCALE})`;
            el.style.transition = 'transform 0.08s ease-out';

            // Glow segue o mouse
            el.style.setProperty('--mouse-x', x + 'px');
            el.style.setProperty('--mouse-y', y + 'px');
        }

        function onLeave() {
            el.style.transition = TILT_TRANSITION;
            el.style.transform = baseTransform || 'translateY(0) scale(1)';
        }

        el.addEventListener('mousemove', onMove);
        el.addEventListener('mouseleave', onLeave);
    }

    function aplicarTiltEmTodos() {
        if (TOUCH || REDUCED_MOTION) return;
        let count = 0;
        SELETORES_TILT.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                // Pula elementos muito pequenos
                const w = el.offsetWidth;
                const h = el.offsetHeight;
                if (w < 100 || h < 60) return;
                aplicarTilt(el);
                count++;
            });
        });
        console.log('[Premium] Tilt 3D aplicado em', count, 'elementos');
    }

    // ==========================================================================
    // 3. BOTOES PREMIUM (substitui classes automaticamente)
    // ==========================================================================
    function transformarBotoes() {
        let count = 0;
        document.querySelectorAll('.btn-primary-custom:not(.btn-3d):not([data-no-3d])').forEach(btn => {
            btn.classList.add('btn-3d');
            count++;
        });
        document.querySelectorAll('.btn-outline-custom:not(.btn-outline-3d):not([data-no-3d])').forEach(btn => {
            btn.classList.add('btn-outline-3d');
            count++;
        });
        console.log('[Premium] Botoes repaginados:', count);
    }

    // ==========================================================================
    // 4. ANIMACAO DE ENTRADA EM CARDS
    // ==========================================================================
    function animarEntrada() {
        const grupos = [
            '.row.g-3 > [class*="col-"]',
            '.kpi-card',
            '.stat-card',
            '.card-modern',
        ];
        let delay = 0;
        grupos.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.dataset.animDone) return;
                el.dataset.animDone = '1';
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    el.style.transition = 'opacity 0.55s cubic-bezier(0.22, 1, 0.36, 1), transform 0.55s cubic-bezier(0.22, 1, 0.36, 1)';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, 60 + delay);
                delay += 40;
                if (delay > 400) delay = 0;
            });
        });
    }

    // ==========================================================================
    // 5. SCROLLBAR SUAVE NOS ELEMENTOS COM SCROLL
    // ==========================================================================
    function melhorarScrollInterno() {
        const style = document.createElement('style');
        style.textContent = `
            .sidebar::-webkit-scrollbar,
            .chat-mensagens::-webkit-scrollbar,
            .dropdown-menu::-webkit-scrollbar,
            .table-responsive::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            .sidebar::-webkit-scrollbar-thumb,
            .chat-mensagens::-webkit-scrollbar-thumb {
                background: rgba(52, 211, 153, 0.35);
                border-radius: 999px;
            }
            .sidebar::-webkit-scrollbar-thumb:hover,
            .chat-mensagens::-webkit-scrollbar-thumb:hover {
                background: rgba(52, 211, 153, 0.6);
            }
            .sidebar::-webkit-scrollbar-track,
            .chat-mensagens::-webkit-scrollbar-track {
                background: transparent;
            }
        `;
        document.head.appendChild(style);
    }

    // ==========================================================================
    // 6. DETECTAR SCROLL INTERNO ADICIONADO DINAMICAMENTE
    // ==========================================================================
    function observarNovosElementos() {
        if (typeof MutationObserver === 'undefined') return;

        const observer = new MutationObserver((mutations) => {
            let temNovo = false;
            mutations.forEach(m => {
                if (m.addedNodes.length > 0) {
                    m.addedNodes.forEach(n => {
                        if (n.nodeType === 1) temNovo = true;
                    });
                }
            });
            if (temNovo) {
                // Aplica tilt nos novos
                if (!TOUCH && !REDUCED_MOTION) {
                    SELETORES_TILT.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            if (!el.dataset.tiltApplied && el.offsetWidth > 100) {
                                aplicarTilt(el);
                            }
                        });
                    });
                }
                // Aplica lenis-prevent nos novos
                fixLenisPrevent();
                // Repagina botoes
                transformarBotoes();
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
        });
    }

    // ==========================================================================
    // INIT
    // ==========================================================================
    function init() {
        fixLenisPrevent();
        transformarBotoes();
        melhorarScrollInterno();

        // Delay pra garantir que DOM renderizou
        setTimeout(() => {
            aplicarTiltEmTodos();
            animarEntrada();
        }, 100);

        // Observa elementos novos (ex: dropdowns, modais)
        observarNovosElementos();

        console.log('[Premium] Efeitos aplicados com sucesso.');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 50);
    }

    // Reaplica quando a janela redimensionar (mudou touch vs desktop)
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            fixLenisPrevent();
            if (!TOUCH && !REDUCED_MOTION) aplicarTiltEmTodos();
        }, 300);
    });

})();
