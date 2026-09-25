/**
 * REABITECH — Confirmação global antes de deletar
 * Uso: adicione class="btn-delete" em qualquer botão de exclusão
 */

document.addEventListener('DOMContentLoaded', function() {
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.btn-delete');
        if (!btn) return;

        e.preventDefault();

        const msg = btn.dataset.confirm || 'Tem certeza que deseja excluir este item? Esta ação não pode ser desfeita.';

        if (confirm(msg)) {
            // Se for um link <a>, redireciona
            if (btn.tagName === 'A' && btn.href) {
                window.location.href = btn.href;
            }
            // Se for <button> com data-url, redireciona
            else if (btn.dataset.url) {
                window.location.href = btn.dataset.url;
            }
            // Se for submit de form, submete
            else if (btn.form) {
                btn.form.submit();
            }
        }
    });
});