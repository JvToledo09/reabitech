// REABITECH GLASS PREMIUM V2
(function () {
    'use strict';
    function on() {
        document.body.classList.add('glass-v2');
        rail();
        var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;
        var calm = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (fine && !calm) tilt();
        var btn = document.getElementById('desktopToggleBtn');
        if (btn) btn.addEventListener('click', function () {
            document.body.classList.toggle('gv2-rail-open');
        });
    }
    function rail() {
        var wide = window.matchMedia('(min-width: 1200px)').matches;
        document.body.classList.toggle('gv2-rail', wide);
        if (!wide) document.body.classList.remove('gv2-rail-open');
    }
    var rt;
    window.addEventListener('resize', function () {
        clearTimeout(rt); rt = setTimeout(rail, 150);
    });
    function tilt() {
        var sel = '.card, .glass-card, .stat-card, .coord-section, .dash-section';
        document.addEventListener('pointermove', function (e) {
            var el = e.target.closest ? e.target.closest(sel) : null;
            if (!el || !document.body.classList.contains('glass-v2')) return;
            var r = el.getBoundingClientRect();
            var x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
            el.style.setProperty('--gv2-mx', (x * 100).toFixed(1) + '%');
            el.style.setProperty('--gv2-my', (y * 100).toFixed(1) + '%');
            el.style.setProperty('--gv2-ry', ((x - .5) * 3).toFixed(2) + 'deg');
            el.style.setProperty('--gv2-rx', ((.5 - y) * 3).toFixed(2) + 'deg');
        }, { passive: true });
        document.addEventListener('pointerout', function (e) {
            var el = e.target.closest ? e.target.closest(sel) : null;
            if (!el) return;
            el.style.setProperty('--gv2-rx', '0deg');
            el.style.setProperty('--gv2-ry', '0deg');
        }, { passive: true });
    }
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', on);
    else on();
})();
