document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript do professor carregado");
    
    const inputBusca = document.getElementById("busca-exercicio");
    const selectGrupo = document.getElementById("filtro-grupo");
    const resultados = document.getElementById("resultados-exercicios");
    const areaSelecionados = document.getElementById("exercicios-selecionados");
    const contador = document.getElementById("quant-exercicios");

    console.log("Elementos encontrados:", {
        inputBusca: !!inputBusca,
        selectGrupo: !!selectGrupo,
        resultados: !!resultados,
        areaSelecionados: !!areaSelecionados,
        contador: !!contador
    });

    if (!inputBusca || !resultados || !areaSelecionados || !contador) {
        console.error("Elementos essenciais não encontrados na página.");
        return;
    }

    // Função para atualizar contador de exercícios
    function atualizarContador() {
        // Conta exercícios existentes (formset) que não estão ocultos ou marcados para exclusão
        const existentesElements = document.querySelectorAll('#exercicios-selecionados .card-exercicio:not(.clonado)');
        const existentes = Array.from(existentesElements).filter(el => {
            const deleteCheckbox = el.querySelector('input[type="checkbox"][name$="-DELETE"]');
            return el.style.display !== 'none' && (!deleteCheckbox || !deleteCheckbox.checked);
        }).length;
        
        // Conta novos exercícios adicionados (apenas dentro da área de selecionados)
        const novos = document.querySelectorAll("#exercicios-selecionados .clonado").length;
        
        const total = existentes + novos;
        
        console.log("Contador - Existentes:", existentes, "Novos:", novos, "Total:", total);
        
        contador.innerHTML = `<p>${total} exercício${total === 1 ? '' : 's'} no treino</p>`;
    }

    // Função para obter IDs de exercícios já selecionados
    function getIdsSelecionados() {
        const existentes = Array.from(document.querySelectorAll('#exercicios-selecionados .card-exercicio[data-id]'))
            .map(el => el.getAttribute('data-id'))
            .filter(id => id); // Remove valores vazios
        return existentes;
    }

    // Função para buscar exercícios
    function buscarExercicios() {
        const termo = inputBusca.value.trim().toLowerCase();
        const grupo = selectGrupo ? selectGrupo.value : "";

        console.log("Buscando exercícios:", { termo, grupo });

        resultados.innerHTML = "";

        if (!termo && !grupo) return;

        const url = `/buscar-exercicios/?q=${encodeURIComponent(termo)}&grupo=${encodeURIComponent(grupo)}`;
        console.log("URL da busca:", url);

        fetch(url)
            .then(response => response.json())
            .then(data => {
                if (!Array.isArray(data) || data.length === 0) {
                    resultados.innerHTML = "<p>Nenhum exercício encontrado.</p>";
                    return;
                }

                const idsSelecionados = getIdsSelecionados();

                data.forEach(exercicio => {
                    // Evita mostrar exercícios já adicionados
                    if (idsSelecionados.includes(exercicio.id.toString())) return;

                    const card = document.createElement("div");
                    card.className = "card-exercicio";
                    card.setAttribute("data-nome", exercicio.nome.toLowerCase());
                    card.setAttribute("data-id", exercicio.id);

                    const midia = exercicio.video_url
                        ? `<video class="video-exercicio" autoplay loop muted playsinline>
                               <source src="${exercicio.video_url}" type="video/mp4">
                               Seu navegador não suporta vídeos.
                           </video>`
                        : `<img src="/static/icones-site/sem-video.png" alt="Sem vídeo" class="imagem-exercicio">`;

                    card.innerHTML = `
                        <div class="info-exercicio">
                            <div class="info-texto">
                                ${midia}
                                <div class="texto">
                                    <label>${exercicio.nome}</label>
                                    <label class="grupo-muscular">${exercicio.grupo_muscular}</label>
                                </div>
                            </div>
                            <div class="inputs">
                                <div class="inputs-detalhes">
                                    <div><h2>Séries: *</h2><input type="number" placeholder="Ex: 3"></div>
                                    <div><h2>Repetições: *</h2><input type="number" placeholder="Ex: 12"></div>
                                    <div><h2>Carga: *</h2><input type="text" placeholder="Kg"></div>
                                </div>
                                <div class="inputs-observacoes">
                                    <div>
                                        <h2>Observações:</h2>
                                        <input type="text" placeholder="Insira observações se necessário sobre o exercício">
                                    </div>
                                </div>
                            </div>
                            <button type="button" class="btn-adicionar" style="display:none;">Adicionar ao treino</button>
                        </div>
                    `;

                    const botaoAdicionar = card.querySelector(".btn-adicionar");
                    const inputsObrigatorios = card.querySelectorAll('.inputs-detalhes input');

                    // Mostrar o botão só quando séries, repetições e carga estiverem preenchidos
                    function validarCampos() {
                        const todosPreenchidos = Array.from(inputsObrigatorios).every(inp => inp.value.trim() !== "");
                        botaoAdicionar.style.display = todosPreenchidos ? "inline-block" : "none";
                    }

                    inputsObrigatorios.forEach(input => {
                        input.addEventListener("input", validarCampos);
                    });

                    // Evento do botão "Adicionar ao treino"
                    botaoAdicionar.addEventListener("click", function () {
                        console.log("Clicou em adicionar exercício:", exercicio);
                        adicionarExercicio(exercicio, card);
                    });

                    resultados.appendChild(card);
                });
            })
            .catch(error => {
                console.error("Erro ao buscar exercícios:", error);
            });
    }

    // Função para adicionar exercício ao treino
    function adicionarExercicio(exercicio, card) {
        const id = exercicio.id;

        // Evita duplicar o exercício (verifica se já existe um com mesmo data-id na área de selecionados)
        const existeExercicio = Array.from(document.querySelectorAll('#exercicios-selecionados .card-exercicio[data-id]'))
            .some(el => el.getAttribute('data-id') === id.toString());
        
        if (existeExercicio) {
            alert('Este exercício já foi adicionado ao treino.');
            return;
        }

        const inputsNumber = card.querySelectorAll('.inputs-detalhes input[type="number"]');
        const s = inputsNumber[0] ? inputsNumber[0].value : "";
        const r = inputsNumber[1] ? inputsNumber[1].value : "";
        const c = card.querySelector('.inputs-detalhes input[type="text"]') ? card.querySelector('.inputs-detalhes input[type="text"]').value : "";
        const o = card.querySelector('.inputs-observacoes input') ? card.querySelector('.inputs-observacoes input').value : "";

        const clone = document.createElement("div");
        clone.className = "card-exercicio clonado";
        clone.setAttribute("data-id", id);

        const midia = exercicio.video_url
            ? `<video class="video-exercicio" autoplay loop muted playsinline>
                   <source src="${exercicio.video_url}" type="video/mp4">
               </video>`
            : `<img src="/static/icones-site/sem-video.png" alt="Sem vídeo" class="imagem-exercicio">`;

        clone.innerHTML = `
            <div class="info-exercicio">
                <div class="info-texto">
                    ${midia}
                    <div class="texto">
                        <label>${exercicio.nome}</label>
                        <label class="grupo-muscular">${exercicio.grupo_muscular}</label>
                    </div>
                </div>
                
                <div class="inputs">
                    <div class="inputs-detalhes">
                        <div>
                            <h2>Séries: *</h2>
                            <input type="number" value="${s}" readonly>
                        </div>
                        <div>
                            <h2>Repetições: *</h2>
                            <input type="number" value="${r}" readonly>
                        </div>
                        <div>
                            <h2>Carga: *</h2>
                            <input type="text" value="${c}" readonly>
                        </div>
                    </div>
                    <div class="inputs-observacoes">
                        <div>
                            <h2>Observações:</h2>
                            <input type="text" value="${o}" readonly placeholder="Insira observações se necessário sobre o exercício">
                        </div>
                    </div>
                </div>

                <button type="button" class="botao-excluir" onclick="this.closest('.card-exercicio').remove(); atualizarContador();">Remover do treino</button>
                
                <input type="hidden" name="exercicios" value="${id}">
                <input type="hidden" name="series" value="${s}">
                <input type="hidden" name="repeticoes" value="${r}">
                <input type="hidden" name="carga" value="${c}">
                <input type="hidden" name="observacoes" value="${o}">
            </div>
        `;

        areaSelecionados.appendChild(clone);
        atualizarContador();

        // Remove o card dos resultados
        card.remove();
    }

    // Event listeners
    if (inputBusca) {
        inputBusca.addEventListener("input", buscarExercicios);
    }

    if (selectGrupo) {
        selectGrupo.addEventListener("change", buscarExercicios);
    }

    // Event listener para limpar busca quando input fica vazio
    if (inputBusca) {
        inputBusca.addEventListener("input", function () {
            if (this.value.trim() === "" && (!selectGrupo || selectGrupo.value === "")) {
                resultados.innerHTML = "";
            }
        });
    }

    // Chama a função inicial para definir o contador correto
    atualizarContador();

    // Exporta funções para uso global
    window.atualizarContador = atualizarContador;
    window.buscarExercicios = buscarExercicios;
});