/**
 * REABITECH - Main JavaScript
 */

console.log('🚀 REABITECH iniciado com sucesso!');

// ============================================
// CARD ANIMATIONS
// ============================================
document.querySelectorAll('.stat-card, .card-modern, .card-atleta').forEach(card => {
    card.addEventListener('mouseenter', function() {
        this.style.transition = 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    });
});

// ============================================
// TOOLTIP AUTO-INIT (Bootstrap)
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(el) {
        return new bootstrap.Tooltip(el);
    });
});

// ============================================
// CONFIRM ACTION (para exclusões)
// ============================================
function confirmAction(message, callback) {
    if (confirm(message || 'Tem certeza que deseja realizar esta ação?')) {
        callback();
    }
}

// ============================================
// FORMATAR NÚMEROS
// ============================================
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(date) {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleDateString('pt-BR');
}

function formatDateTime(date) {
    if (!date) return '-';
    const d = new Date(date);
    return d.toLocaleString('pt-BR');
}

// ============================================
// NOTIFICAÇÃO TOAST
// ============================================
function showToast(message, type = 'success') {
    const colors = {
        success: '#2BA181',
        error: '#dc3545',
        warning: '#ffc107',
        info: '#0dcaf0'
    };
    
    const toast = document.createElement('div');
    toast.className = `position-fixed bottom-0 end-0 p-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        <div class="toast show" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header" style="background: ${colors[type] || colors.info}; color: white;">
                <strong class="me-auto">REABITECH</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 5000);
}

// ============================================
// MASK DE CPF/CNPJ (se necessário)
// ============================================
function maskCPF(value) {
    value = value.replace(/\D/g, '');
    if (value.length <= 11) {
        return value.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    }
    return value;
}

function maskPhone(value) {
    value = value.replace(/\D/g, '');
    if (value.length <= 10) {
        return value.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
    }
    return value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
}

// ============================================
// EXPORT
// ============================================
window.ReabiTech = {
    formatNumber,
    formatCurrency,
    formatDate,
    formatDateTime,
    showToast,
    confirmAction,
    maskCPF,
    maskPhone
};

// ============================================
// 🔥 NOVAS FUNÇÕES: Animações, máscaras extras e utilitários premium
// ============================================

// ===== ANIMAÇÃO DE ENTRADA (PARA ELEMENTOS COM .animate-fadeInUp) =====
document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.animate-fadeInUp');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('show');
        }, index * 100); // Efeito cascata
    });
});

// ===== MÁSCARA DE CEP =====
function maskCEP(value) {
    value = value.replace(/\D/g, '');
    return value.replace(/(\d{5})(\d{3})/, '$1-$2');
}

// ===== MÁSCARA DE DATA =====
function maskDate(value) {
    value = value.replace(/\D/g, '');
    if (value.length <= 2) return value;
    if (value.length <= 4) return value.replace(/(\d{2})(\d{2})/, '$1/$2');
    return value.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
}

// ===== TOGGLE DE TEMA (DARK MODE) =====
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-bs-theme') === 'dark';
    html.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    return !isDark;
}

// ===== SCROLL SUAVE PARA ÂNCORAS =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

// Adicionando as novas funções ao export
window.ReabiTech = {
    ...window.ReabiTech,
    maskCEP,
    maskDate,
    toggleTheme
};