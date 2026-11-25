
document.addEventListener('DOMContentLoaded', function() {
    const splash = document.getElementById('reabitech-splash');
    if (splash) {
        setTimeout(() => {
            splash.classList.add('fade-out');
            setTimeout(() => splash.remove(), 800); // Remove do DOM apos a transicao
        }, 2500); // 2.5 segundos de exibicao
    }
});
