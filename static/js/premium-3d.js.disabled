
document.addEventListener('DOMContentLoaded', function() {
    // Seleciona todos os cards do sistema
    const cards = document.querySelectorAll('.card, .card-modern, .card-premium, .dash-stat, .dash-action, .fisio-stat, .fisio-action, .fisio-atleta, .kpi-card, .chart-card');

    cards.forEach(card => {
        // Adiciona a classe base para o CSS saber que esse card tem 3D
        card.classList.add('has-3d-effect');

        card.addEventListener('mousemove', handleMove);
        card.addEventListener('mouseleave', handleLeave);
        card.addEventListener('mouseenter', handleEnter);
    });

    let rafId = null;

    function handleEnter(e) {
        const card = e.currentTarget;
        // Transicao rapida na entrada para nao lagar o movimento
        card.style.transition = 'transform 0.1s ease-out, box-shadow 0.1s ease-out';
    }

    function handleMove(e) {
        const card = e.currentTarget;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Calcula a posicao do mouse de 0 a 1
        const pctX = x / rect.width;
        const pctY = y / rect.height;

        // Define a inclinacao maxima (graus)
        const maxTilt = 10;
        const tiltX = (0.5 - pctY) * maxTilt;
        const tiltY = (pctX - 0.5) * maxTilt;

        // Usa requestAnimationFrame para rodar a 60fps (sem travar)
        if (rafId) cancelAnimationFrame(rafId);

        rafId = requestAnimationFrame(() => {
            // Inclina o card
            card.style.transform = `perspective(1000px) rotateX(${tiltX}deg) rotateY(${tiltY}deg) scale3d(1.03, 1.03, 1.03)`;
            
            // Sombra profunda e Neon
            card.style.boxShadow = `0 30px 60px rgba(0,0,0,0.3), 0 0 30px rgba(16, 185, 129, 0.2)`;
            
            // Atualiza as variaveis para a luz seguir o mouse
            card.style.setProperty('--mouse-x', `${x}px`);
            card.style.setProperty('--mouse-y', `${y}px`);
            
            // Ativa a classe que liga o brilho no CSS
            card.classList.add('is-tilting');
        });
    }

    function handleLeave(e) {
        const card = e.currentTarget;
        if (rafId) cancelAnimationFrame(rafId);
        
        // Transicao suave e lenta para voltar ao normal (efeito mola)
        card.style.transition = 'transform 0.6s cubic-bezier(0.2, 0.8, 0.2, 1), box-shadow 0.6s ease';
        card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
        card.style.boxShadow = '';
        
        // Desliga o brilho
        card.classList.remove('is-tilting');
    }
});
