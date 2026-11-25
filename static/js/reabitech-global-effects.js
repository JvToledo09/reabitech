
document.addEventListener('DOMContentLoaded', function() {
    // Aplica o efeito de onda (ripple) em todos os botoes
    const buttons = document.querySelectorAll('.btn, button, [class*="btn-"]');
    
    buttons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = x + 'px';
            ripple.style.top = y + 'px';
            
            const size = Math.max(rect.width, rect.height);
            ripple.style.width = ripple.style.height = size + 'px';
            ripple.style.marginLeft = ripple.style.marginTop = (-size/2) + 'px';
            
            this.appendChild(ripple);
            setTimeout(() => ripple.remove(), 600);
        });
    });
});
