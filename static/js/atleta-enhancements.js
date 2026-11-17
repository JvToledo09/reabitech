document.addEventListener('DOMContentLoaded', function() {
    const path = window.location.pathname;

    // -------------------------------------------------------------
    // TELA: MINHA RECUPERAÇÃO (Corrigir os cards)
    // -------------------------------------------------------------
    if (path.includes('/recuperacao/')) {
        // Procura os cards de lesão
        const lesaoCards = document.querySelectorAll('.dash-section .dash-stat');
        lesaoCards.forEach(card => {
            card.classList.add('lesao-card');
            
            // Pega o título da lesão e organiza o header
            const title = card.querySelector('h4, h5, strong');
            if (title) {
                // Envolve o título e a data em uma div flex
                const headerDiv = document.createElement('div');
                headerDiv.className = 'lesao-header';
                title.parentNode.insertBefore(headerDiv, title);
                headerDiv.appendChild(title);
                
                // Joga a badge de "Em tratamento" pra dentro do header
                const badge = card.querySelector('.dash-stat-badge');
                if (badge) headerDiv.appendChild(badge);
            }
        });
    }

    // -------------------------------------------------------------
    // TELA: SAÚDE MENTAL (Transformar tabela em Grid de Cards)
    // -------------------------------------------------------------
    if (path.includes('/psicologico/')) {
        const table = document.querySelector('.dash-table');
        if (table) {
            const tbody = table.querySelector('tbody');
            const rows = tbody.querySelectorAll('tr');
            
            // Cria o container do grid
            const grid = document.createElement('div');
            grid.className = 'mental-grid';
            
            rows.forEach(row => {
                const tds = row.querySelectorAll('td');
                if (tds.length >= 3) {
                    const date = tds[0].innerText.trim();
                    const scoreText = tds[1].innerText.trim(); // Ex: "6,2/10"
                    const status = tds[2].innerText.trim(); // Ex: "Regular"
                    
                    const scoreNum = parseFloat(scoreText.replace(',', '.')) || 0;
                    const percent = (scoreNum / 10) * 100;
                    
                    let color = '#10b981'; // Verde
                    let msg = 'Excelente! Continue assim.';
                    if (scoreNum < 4) {
                        color = '#ef4444'; // Vermelho
                        msg = 'Atenção: procure seu psicólogo.';
                    } else if (scoreNum < 7) {
                        color = '#f59e0b'; // Laranja
                        msg = 'Regular. Você consegue melhorar!';
                    }

                    // Cria o Card
                    const card = document.createElement('div');
                    card.className = 'mental-card';
                    card.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <span class="mental-date"><i class="fas fa-calendar-alt"></i> ${date}</span>
                            <span class="dash-stat-badge ${scoreNum >= 7 ? 'success' : scoreNum >= 4 ? 'warn' : 'danger'}">${status}</span>
                        </div>
                        <div class="mental-score">
                            <h2>${scoreNum}</h2><span>/10</span>
                        </div>
                        <div class="mental-progress">
                            <div class="mental-progress-fill" style="width: ${percent}%; background: ${color};"></div>
                        </div>
                        <div class="mental-msg" style="background: ${color}20; color: ${color};">
                            ${msg}
                        </div>
                    `;
                    grid.appendChild(card);
                }
            });
            
            // Substitui a tabela pelo grid
            table.parentNode.replaceChild(grid, table);
        }
    }

    // -------------------------------------------------------------
    // TELA: MEUS EXERCÍCIOS (Transformar lista em Cards de Academia)
    // -------------------------------------------------------------
    if (path.includes('/exercicios/')) {
        // Encontra os containers dos exercícios
        const exercicioDivs = document.querySelectorAll('.dash-section > div[style*="display: flex"]');
        
        if (exercicioDivs.length > 0) {
            // Cria a grid
            const grid = document.createElement('div');
            grid.className = 'exercise-grid';
            
            exercicioDivs.forEach((div, index) => {
                // Extrai as informações do HTML original
                const nome = div.querySelector('p:nth-child(1)') ? div.querySelector('p:nth-child(1)').innerText : 'Exercício';
                const detalhes = div.querySelector('p:nth-child(2)') ? div.querySelector('p:nth-child(2)').innerText : '';
                
                // Tenta extrair séries, reps, etc (ex: "3x12 · 3x por semana")
                let series = "3", rep = "12", freq = "3x";
                if (detalhes.includes('x')) {
                    const partes = detalhes.split('·');
                    if (partes[0]) {
                        const s = partes[0].trim().split('x');
                        series = s[0] || "3";
                        rep = s[1] || "12";
                    }
                    if (partes[1]) freq = partes[1].trim();
                }

                // Gradiente temático por tipo de exercício (Unsplash descontinuado)
                const gradientes = [
                    'linear-gradient(135deg, #10b981, #0891b2)',
                    'linear-gradient(135deg, #3b82f6, #8b5cf6)',
                    'linear-gradient(135deg, #f59e0b, #ef4444)',
                    'linear-gradient(135deg, #059669, #10b981)',
                    'linear-gradient(135deg, #7c3aed, #ec4899)',
                ];
                const gradiente = gradientes[index % gradientes.length];
                const icones = ['fa-dumbbell', 'fa-person-running', 'fa-heart-pulse', 'fa-spa', 'fa-bolt'];
                const icone = icones[index % icones.length];

                // Cria o Card Premium
                const card = document.createElement('div');
                card.className = 'exercise-card';
                card.innerHTML = `
                    <div class="exercise-img-wrapper" style="background: ${gradiente}; display: flex; align-items: center; justify-content: center; min-height: 140px; border-radius: 14px 14px 0 0;">
                        <i class="fas ${icone}" style="font-size: 3rem; color: rgba(255,255,255,0.85);"></i>
                    </div>
                    <div class="exercise-body">
                        <h4 class="exercise-title">${nome}</h4>
                        <p class="exercise-desc">${detalhes.split('·')[0] || 'Siga as instruções do seu fisioterapeuta.'}</p>
                        
                        <div class="exercise-stats">
                            <div class="exercise-stat-box">
                                <strong>${series}</strong>
                                <span>Séries</span>
                            </div>
                            <div class="exercise-stat-box">
                                <strong>${rep}</strong>
                                <span>Reps</span>
                            </div>
                            <div class="exercise-stat-box">
                                <strong>${freq}</strong>
                                <span>Freq.</span>
                            </div>
                        </div>
                        
                        <button class="btn-concluir" onclick="this.innerHTML='<i class=\\'fas fa-check\\'></i> Concluído!'; this.style.background='#10b981'; this.disabled=true;">
                            <i class="fas fa-play"></i> Marcar como Concluído
                        </button>
                    </div>
                `;
                grid.appendChild(card);
                
                // Esconde o card original
                div.style.display = 'none';
            });
            
            // Insere a grid no lugar da lista antiga
            const parentSection = exercicioDivs[0].parentNode;
            parentSection.appendChild(grid);
            
            // Remove o cabeçalho "Meus Exercícios" se estiver sobrando (opcional)
        }
    }
});
