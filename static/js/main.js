console.log("ReabiTech iniciado");

document.querySelectorAll('.card').forEach(card => {

card.addEventListener('mouseenter', () => {
card.style.transform = 'translateY(-10px)';
});

card.addEventListener('mouseleave', () => {
card.style.transform = 'translateY(0px)';
});

});