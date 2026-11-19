
document.addEventListener('DOMContentLoaded', function() {
    // Pega todos os cards e botoes do sistema
    const elements = document.querySelectorAll(
        '.card, .card-modern, .card-premium, .dash-stat, .dash-action, ' +
        '.fisio-stat, .fisio-action, .fisio-atleta, .kpi-card, .chart-card, ' +
        '.btn, .btn-primary-custom, .btn-outline-custom'
    );
    
    elements.forEach(el => {
        el.classList.add('mega-tilt');
        
        // Define transicao suave na saida (bounce)
        el.style.transition = 'transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.5s ease, border-color 0.3s ease';
        
        el.addEventListener('mousemove', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            // Se for botao, o 3D e mais sutil para nao atrapalhar o clique
            const isBtn = this.classList.contains('btn') || this.classList.contains('btn-primary-custom') || this.classList.contains('btn-outline-custom');
            const maxTilt = isBtn ? 3 : 10;
            
            const rotateX = ((y - centerY) / centerY) * -maxTilt;
            const rotateY = ((x - centerX) / centerX) * maxTilt;
            
            // Atualiza o transform via requestAnimationFrame para ser fluido a 60fps
            this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.04, 1.04, 1.04) translateY(-5px)`;
            
            // Salva a posicao do mouse para o CSS desenhar o brilho
            this.style.setProperty('--mouse-x', x + 'px');
            this.style.setProperty('--mouse-y', y + 'px');
            
            // Liga a classe de brilho
            this.classList.add('is-tilting');
        });
        
        el.addEventListener('mouseleave', function() {
            // Remove o transform (o CSS com bounce cuida de voltar suavemente)
            this.style.transform = '';
            this.classList.remove('is-tilting');
        });
    });
});
