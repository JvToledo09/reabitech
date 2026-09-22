/**
 * REABITECH - Main JavaScript
 * Versão corrigida - Setembro 2026
 */

// ============================================
// LOG DE INICIALIZAÇÃO (só em desenvolvimento)
// ============================================
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🚀 REABITECH iniciado com sucesso!');
}

// ============================================
// TOOLTIP AUTO-INIT (Bootstrap)
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (el) {
        return new bootstrap.Tooltip(el);
    });
});

// ============================================
// ANIMAÇÃO DE ENTRADA (elementos com .animate-fadeInUp)
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    const elements = document.querySelectorAll('.animate-fadeInUp');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.classList.add('show');
        }, index * 100); // Efeito cascata
    });
});

// ============================================
// SCROLL SUAVE PARA ÂNCORAS
// (ignora links com data-bs-toggle, href="#", etc.)
// ============================================
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('a[href^="#"]:not([data-bs-toggle])').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (!href || href === '#') return;

            const target = document.querySelector(href);
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
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
// FORMATAÇÃO DE NÚMEROS, MOEDAS E DATAS
// ============================================
function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function formatCurrency(value) {
    if (value === null || value === undefined) return '-';
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
// MÁSCARAS (funcionam com qualquer quantidade de dígitos)
// ============================================

// ----- CPF: 000.000.000-00 -----
function maskCPF(value) {
    value = value.replace(/\D/g, '').slice(0, 11);
    return value
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d)/, '$1.$2')
        .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
}

// ----- Telefone: (00) 00000-0000 ou (00) 0000-0000 -----
function maskPhone(value) {
    value = value.replace(/\D/g, '').slice(0, 11);
    if (value.length <= 10) {
        return value
            .replace(/(\d{2})(\d)/, '($1) $2')
            .replace(/(\d{4})(\d)/, '$1-$2');
    }
    return value
        .replace(/(\d{2})(\d)/, '($1) $2')
        .replace(/(\d{5})(\d)/, '$1-$2');
}

// ----- CEP: 00000-000 -----
function maskCEP(value) {
    value = value.replace(/\D/g, '').slice(0, 8);
    return value.replace(/(\d{5})(\d)/, '$1-$2');
}

// ----- Data: DD/MM/AAAA -----
function maskDate(value) {
    value = value.replace(/\D/g, '').slice(0, 8);
    if (value.length <= 2) return value;
    if (value.length <= 4) return value.replace(/(\d{2})(\d)/, '$1/$2');
    return value.replace(/(\d{2})(\d{2})(\d{4})/, '$1/$2/$3');
}

// ============================================
// TOGGLE DE TEMA (DARK MODE)
// ============================================
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-bs-theme') === 'dark';
    html.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
    localStorage.setItem('theme', isDark ? 'light' : 'dark');
    return !isDark;
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
    toast.className = 'position-fixed bottom-0 end-0 p-3';
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
// EXPORT GLOBAL
// ============================================
window.ReabiTech = {
    // Formatação
    formatNumber,
    formatCurrency,
    formatDate,
    formatDateTime,

    // Máscaras
    maskCPF,
    maskPhone,
    maskCEP,
    maskDate,

    // Utilidades
    showToast,
    confirmAction,
    toggleTheme
};

// ============================================
// LOG DE CARREGAMENTO (só em desenvolvimento)
// ============================================
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('✅ REABITECH Main.js carregado. Funções disponíveis em window.ReabiTech');
}