/* ==============================================================================
   REABITECH - PREMIUM EFFECTS v2
   Tilt 3D com camadas, cursor glow, ripple, breathing indicators
   ============================================================================== */

(function() {
    'use strict';

    const TOUCH = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);
    const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const IS_MOBILE = window.matchMedia('(max-width: 992px)').matches;

    // ==========================================================================
    // 1. LENIS PREVENT EM SCROLL INTERNO
    // ==========================================================================
    function fixLenisPrevent() {
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
            '.chat-sidebar',
            '.chat-main',
            '.timeline-container',
        ];

        seletores.forEach(sel => {
            try {
                document.querySelectorAll(sel).forEach(el => {
                    el.setAttribute('data-lenis-prevent', '');
                });
            } catch (e) {}
        });
    }

    // ==========================================================================
    // 2. TILT 3D AVANCADO COM CAMADAS DE PARALAXE
    // ==========================================================================
    const SELETORES_TILT = [
        '.card-modern',
        '.stat-card',
        '.kpi-card',
        '.chart-card',
        '.card-glass',
    ];

    const TILT_MAX = 8;
    const TILT_PERSPECTIVE = 1200;

    function aplicarTilt(el) {
        if (el.dataset.tiltApplied) return;
        el.dataset.tiltApplied = '1';

        el.classList.add('tilt-3d', 'tilt-glow', 'tilt-3d-shadow');

        let rafId = null;
        let targetTransform = '';
        let targetShadowX = 0;
        let targetShadowY = 0;

        function onMove(e) {
            if (REDUCED_MOTION || TOUCH || IS_MOBILE) return;

            const rect = el.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const pctX = (x / rect.width) - 0.5;
            const pctY = (y / rect.height) - 0.5;

            const rotX = (-pctY * TILT_MAX).toFixed(2);
            const rotY = (pctX * TILT_MAX).toFixed(2);

            // Escala sutil + perspectiva
            targetTransform =
                `perspective(${TILT_PERSPECTIVE}px) ` +
                `rotateX(${rotX}deg) ` +
                `rotateY(${rotY}deg) ` +
                `translateZ(8px) scale(1.015)`;

            // Sombra dinamica (oposta ao movimento)
            targetShadowX = (-pctX * 20).toFixed(1);
            targetShadowY = (-pctY * 20).toFixed(1);

            // Atualiza variaveis CSS pra glow
            el.style.setProperty('--mouse-x', x + 'px');
            el.style.setProperty('--mouse-y', y + 'px');
            el.style.setProperty('--shadow-x', targetShadowX + 'px');
            el.style.setProperty('--shadow-y', targetShadowY + 'px');

            if (rafId) cancelAnimationFrame(rafId);
            rafId = requestAnimationFrame(() => {
                el.style.transform = targetTransform;
                el.style.transition = 'transform 0.1s ease-out, box-shadow 0.1s ease-out';
            });
        }

        function onLeave() {
            if (rafId) cancelAnimationFrame(rafId);
            el.style.transition =
                'transform 0.7s cubic-bezier(0.16, 1, 0.3, 1),' +
                'box-shadow 0.7s cubic-bezier(0.16, 1, 0.3, 1)';
            el.style.transform = 'perspective(1200px) rotateX(0) rotateY(0) translateZ(0) scale(1)';
            el.style.setProperty('--shadow-x', '0px');
            el.style.setProperty('--shadow-y', '0px');
        }

        el.addEventListener('mousemove', onMove);
        el.addEventListener('mouseleave', onLeave);
    }

    function aplicarTiltEmTodos() {
        if (TOUCH || REDUCED_MOTION || IS_MOBILE) return;
        let count = 0;
        SELETORES_TILT.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.offsetWidth < 100 || el.offsetHeight < 60) return;
                aplicarTilt(el);
                count++;
            });
        });
        console.log('[Premium v2] Tilt 3D avancado aplicado em', count, 'elementos');
    }

    // ==========================================================================
    // 3. CURSOR GLOW GLOBAL (aura verde que segue o mouse)
    // ==========================================================================
    function initCursorGlow() {
        if (TOUCH || IS_MOBILE || REDUCED_MOTION) return;

        const glow = document.createElement('div');
        glow.className = 'cursor-glow';
        document.body.appendChild(glow);

        let mouseX = window.innerWidth / 2;
        let mouseY = window.innerHeight / 2;
        let currentX = mouseX;
        let currentY = mouseY;
        let rafId;

        document.addEventListener('mousemove', (e) => {
            mouseX = e.clientX;
            mouseY = e.clientY;
        });

        function animate() {
            // Suavizacao (lerp)
            currentX += (mouseX - currentX) * 0.08;
            currentY += (mouseY - currentY) * 0.08;
            glow.style.left = currentX + 'px';
            glow.style.top = currentY + 'px';
            rafId = requestAnimationFrame(animate);
        }
        animate();

        console.log('[Premium v2] Cursor glow ativo');
    }

    // ==========================================================================
    // 4. RIPPLE NOS BOTOES (onda ao clicar)
    // ==========================================================================
    function initRipple() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest(
                '.btn-primary-custom, .btn-3d, .btn-outline-custom, .btn-outline-3d, .btn'
            );
            if (!btn) return;
            if (REDUCED_MOTION) return;

            btn.classList.add('ripple-container');
            const rect = btn.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.clientX - rect.left - size / 2;
            const y = e.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.className = 'ripple';
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';

            btn.appendChild(ripple);
            setTimeout(() => ripple.remove(), 700);
        });
    }

    // ==========================================================================
    // 5. BREATHING INDICATORS (adiciona nos badges de saude)
    // ==========================================================================
    function initBreathingIndicators() {
        // Badges com "ativo" ganham efeito de respiracao
        document.querySelectorAll('.badge').forEach(b => {
            const txt = (b.textContent || '').toLowerCase();
            if (txt.includes('ativo') || txt.includes('live') || txt.includes('em tratamento')) {
                b.classList.add('pulse-breathe');
            }
        });
    }

    // ==========================================================================
    // 6. CARDS COM ECG (aplica em KPI de saude)
    // ==========================================================================
    function initEcgCards() {
        // Aplica em cards que tem "evolucao", "recuperacao", "dor" no titulo
        document.querySelectorAll('.stat-card, .kpi-card, .card-modern').forEach(card => {
            const texto = (card.textContent || '').toLowerCase();
            if (texto.includes('evolu') || texto.includes('recupera') || texto.includes('dor') ||
                texto.includes('ades') || texto.includes('frequ')) {
                card.classList.add('card-ecg');
            }
        });
    }

    // ==========================================================================
    // 7. BOTOES PREMIUM (auto classe)
    // ==========================================================================
    function transformarBotoes() {
        document.querySelectorAll('.btn-primary-custom:not(.btn-3d)').forEach(b => b.classList.add('btn-3d'));
        document.querySelectorAll('.btn-outline-custom:not(.btn-outline-3d)').forEach(b => b.classList.add('btn-outline-3d'));
    }

    // ==========================================================================
    // 8. ANIMACAO DE ENTRADA EM CASCATA
    // ==========================================================================
    function animarEntrada() {
        const grupos = [
            '.row.g-3 > [class*="col-"]',
            '.kpi-card',
            '.stat-card',
        ];
        let delay = 0;
        grupos.forEach(sel => {
            document.querySelectorAll(sel).forEach(el => {
                if (el.dataset.animDone) return;
                el.dataset.animDone = '1';
                el.style.opacity = '0';
                el.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    el.style.transition = 'opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1)';
                    el.style.opacity = '1';
                    el.style.transform = 'translateY(0)';
                }, 60 + delay);
                delay += 45;
                if (delay > 400) delay = 0;
            });
        });
    }

    // ==========================================================================
    // 9. SCROLLBAR INTERNA BONITA
    // ==========================================================================
    function melhorarScrollInterno() {
        const style = document.createElement('style');
        style.textContent = `
            .sidebar::-webkit-scrollbar,
            .chat-mensagens::-webkit-scrollbar,
            .dropdown-menu::-webkit-scrollbar,
            .table-responsive::-webkit-scrollbar {
                width: 5px;
                height: 5px;
            }
            .sidebar::-webkit-scrollbar-thumb,
            .chat-mensagens::-webkit-scrollbar-thumb {
                background: rgba(52, 211, 153, 0.3);
                border-radius: 999px;
                transition: background 0.3s ease;
            }
            .sidebar::-webkit-scrollbar-thumb:hover,
            .chat-mensagens::-webkit-scrollbar-thumb:hover {
                background: rgba(52, 211, 153, 0.6);
            }
        `;
        document.head.appendChild(style);
    }

    // ==========================================================================
    // 10. OBSERVER (aplica em elementos novos)
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
                if (!TOUCH && !REDUCED_MOTION && !IS_MOBILE) {
                    SELETORES_TILT.forEach(sel => {
                        document.querySelectorAll(sel).forEach(el => {
                            if (!el.dataset.tiltApplied && el.offsetWidth > 100) {
                                aplicarTilt(el);
                            }
                        });
                    });
                }
                fixLenisPrevent();
                transformarBotoes();
                initEcgCards();
                initBreathingIndicators();
            }
        });

        observer.observe(document.body, { childList: true, subtree: true });
    }

    // ==========================================================================
    // INIT
    // ==========================================================================
    function init() {
        fixLenisPrevent();
        transformarBotoes();
        melhorarScrollInterno();
        initRipple();
        initCursorGlow();

        setTimeout(() => {
            aplicarTiltEmTodos();
            animarEntrada();
            initEcgCards();
            initBreathingIndicators();
        }, 100);

        observarNovosElementos();

        console.log('[Premium v2] Todos os efeitos ativos.');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 50);
    }

    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            fixLenisPrevent();
        }, 300);
    });

})();
