/* ==============================================================================
   REABITECH - LENIS SMOOTH SCROLL
   Rolagem suave consistente em desktop, trackpad e mobile
   Docs: https://lenis.dev
   ============================================================================== */

(function() {
    'use strict';

    // Nao roda se o usuario prefere movimento reduzido (acessibilidade)
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        console.log('[Lenis] Desativado por preferencia do usuario (reduced-motion).');
        return;
    }

    // Nao roda em mobile muito antigo / navegador sem suporte
    if (!window.requestAnimationFrame) return;

    // Espera DOM carregar
    function init() {
        if (typeof Lenis === 'undefined') {
            console.warn('[Lenis] Lib nao carregada. Verifique o CDN.');
            return;
        }

        // Detecta mobile (touch) - Lenis em mobile as vezes causa bugs com scroll nativo
        const isTouchDevice = ('ontouchstart' in window) || (navigator.maxTouchPoints > 0);

        // Configuracao base
        const lenis = new Lenis({
            duration: 1.15,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            direction: 'vertical',
            gestureDirection: 'vertical',
            smooth: !isTouchDevice,
            smoothTouch: false,
            touchMultiplier: 2,
            wheelMultiplier: 1,
            infinite: false,
            autoResize: true,
        });

        // Loop de animacao
        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);

        // Integra com AOS (animações on scroll)
        if (window.AOS && typeof AOS.refresh === 'function') {
            lenis.on('scroll', () => {
                if (window.AOS && typeof AOS.refreshHard === 'function') {
                    AOS.refreshHard();
                }
            });
        }

        // Expor globalmente pra debug / integracao
        window.__lenis = lenis;

        // Ao trocar de tema, força update
        const themeBtn = document.getElementById('themeToggleGlobal');
        if (themeBtn) {
            themeBtn.addEventListener('click', () => {
                setTimeout(() => lenis.resize(), 200);
            });
        }

        // Recalcula apos carregar fonts / imagens
        window.addEventListener('load', () => {
            lenis.resize();
        });

        // Redimensiona em resize da janela
        window.addEventListener('resize', () => {
            lenis.resize();
        });

        console.log('[Lenis] Inicializado com sucesso.', isTouchDevice ? '(touch: smoothTouch off)' : '(desktop: smooth on)');
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
