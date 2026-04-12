document.addEventListener("DOMContentLoaded", function () {
    const inputBusca = document.getElementById("busca-exercicio");
    const resultados = document.getElementById("resultados-exercicios");
    const areaSelecionados = document.getElementById("exercicios-selecionados");
    const contador = document.getElementById("quant-exercicios");
    const form = document.querySelector("form");
    const selectGrupo = document.querySelector('select[name="grupo_muscular"]');
    const treinoIdInput = document.querySelector('input[name="treino_id"]');

    if (!form || !inputBusca || !resultados || !areaSelecionados) {
        console.error("Elementos essenciais não encontrados na página.");
        return;
    }

    const totalFormsInput = document.querySelector('input[name$="-TOTAL_FORMS"]');
    if (!totalFormsInput) {
        console.error("Campo TOTAL_FORMS do formset não encontrado.");
        return;
    }
    const prefix = totalFormsInput.name.replace(/-TOTAL_FORMS$/, "");

    function atualizarContador() {
        if (!contador) return;
        const total = areaSelecionados.querySelectorAll(".clonado").length;
        contador.innerHTML = `<p>${total} exercício${total === 1 ? '' : 's'} inserido${total === 1 ? '' : 's'} no treino</p>`;
    }

    function getIdsSelecionados() {
        const novos = Array.from(areaSelecionados.querySelectorAll(".clonado"))
            .map(c => c.getAttribute("data-id"));
        const existentes = Array.from(document.querySelectorAll('input[name$="-exercicio"]'))
            .map(input => input.value)
            .filter(v => v);
        return [...novos, ...existentes];
    }

    function adicionarClone(exercicio, card) {
        const id = exercicio.id;
        if (getIdsSelecionados().includes(id.toString())) return;

        const clone = document.createElement("div");
        clone.className = "clonado";
        clone.setAttribute("data-id", id);

        const s = card.querySelector('.input-serie').value || "";
        const r = card.querySelector('.input-repeticao').value || "";
        const c = card.querySelector('.input-carga').value || "";
        const o = card.querySelector('.input-obs')?.value || "";

        const midiaClone = exercicio.video_url
            ? `<video class="video-exercicio" autoplay loop muted playsinline width="150">
                <source src="${exercicio.video_url}" type="video/mp4">
            </video>`
            : `<img src="/static/icones-site/sem-video.png" alt="Sem vídeo" class="imagem-exercicio" width="150">`;

        clone.innerHTML = `
            <div class="clonado-info">
                ${midiaClone}
                <strong>${exercicio.nome}</strong>
                <div class="clonado-campos">
                    <label>Séries: <input type="number" class="clonado-series" value="${s}" min="0"></label>
                    <label>Repetições: <input type="number" class="clonado-repeticoes" value="${r}" min="0"></label>
                    <label>Carga: <input type="text" class="clonado-carga" value="${c}"></label>
                    <label>Observação: <input type="text" class="clonado-obs" value="${o}"></label>
                </div>
            </div>
        `;

        const totalForms = parseInt(totalFormsInput.value, 10);
        const formIndex = totalForms;

        const hiddenFields = `
            <input type="hidden" name="${prefix}-${formIndex}-exercicio" value="${id}">
            <input type="hidden" name="${prefix}-${formIndex}-series" value="${s}">
            <input type="hidden" name="${prefix}-${formIndex}-repeticoes" value="${r}">
            <input type="hidden" name="${prefix}-${formIndex}-carga" value="${c}">
            <input type="hidden" name="${prefix}-${formIndex}-observacao" value="${o}">
        `;

        clone.insertAdjacentHTML("beforeend", hiddenFields);
        totalFormsInput.value = totalForms + 1;

        const botaoExcluir = document.createElement("button");
        botaoExcluir.type = "button";
        botaoExcluir.className = "botao-excluir";
        botaoExcluir.innerHTML = `<img style="width: 15px; margin: 0px 10px 0px 0px;" src="/static/icones-site/icone-lixo.png" alt="Excluir"> Remover do treino`;
        botaoExcluir.addEventListener("click", () => {
            clone.remove();
            atualizarContador();
            totalFormsInput.value = parseInt(totalFormsInput.value, 10) - 1;
        });

        clone.appendChild(botaoExcluir);
        areaSelecionados.appendChild(clone);
        atualizarContador();
    }

    // ... (mantém o começo do seu código igual)

    function buscarExercicios() {
        const termo = inputBusca.value.trim().toLowerCase();
        const grupo = selectGrupo.value;
        resultados.innerHTML = "";

        if (!termo && !grupo) return;

        const treinoId = treinoIdInput?.value || "";

        fetch(`/buscar-exercicios/?q=${encodeURIComponent(termo)}&grupo=${encodeURIComponent(grupo)}&treino_id=${encodeURIComponent(treinoId)}`)
            .then(response => response.json())
            .then(data => {
                if (!Array.isArray(data) || data.length === 0) {
                    resultados.innerHTML = "<p>Nenhum exercício encontrado.</p>";
                    return;
                }

                const idsSelecionados = getIdsSelecionados();

                data.forEach(exercicio => {
                    if (idsSelecionados.includes(exercicio.id.toString())) return;

                    // 🔥 wrapper que vai segurar o aviso e o card
                    const wrapper = document.createElement("div");
                    wrapper.className = "wrapper-exercicio";

                    const aviso = document.createElement("div");
                    aviso.className = "overlay-aviso";
                    aviso.innerHTML = "⚠️ Adicione séries, repetições e carga para liberar o botão de adição";
                    aviso.style.cssText = `
                        background: #ffeb3b;
                        padding: 5px;
                        text-align: center;
                        font-size: 13px;
                        border-radius: 10px 10px 0px 0px;
                        font-weight: bold;
                        color: #333;
                    `;

                    const card = document.createElement("div");
                    card.className = "card-exercicio";
                    card.setAttribute("data-id", exercicio.id);

                    const midia = exercicio.video_url
                        ? `<video class="video-exercicio" autoplay loop muted playsinline>
                            <source src="${exercicio.video_url}" type="video/mp4">
                        </video>`
                        : `<img src="/static/icones-site/sem-video.png" alt="Sem vídeo" class="imagem-exercicio">`;

                    card.innerHTML = `
                        <div class="info-exercicio">
                            <div class="info-texto">
                                ${midia}
                                <div class="texto">
                                    <label>${exercicio.nome}</label>
                                    <label class="grupo-muscular">${exercicio.grupo_muscular || ''}</label>
                                </div>
                            </div>
                            <div class="inputs">
                                <div class="inputs-detalhes">
                                    <div><h2>Séries: *</h2><input type="number" placeholder="Ex: 3" min="0" class="input-serie"></div>
                                    <div><h2>Repetições: *</h2><input type="number" placeholder="Ex: 12" min="0" class="input-repeticao"></div>
                                    <div><h2>Carga: *</h2><input type="text" placeholder="Kg" class="input-carga"></div>
                                </div>
                                <div class="inputs-observacoes">
                                    <div><h2>Observações:</h2><input type="text" class="input-obs" placeholder="Insira observações"></div>
                                </div>
                            </div>
                            <button type="button" class="btn-adicionar" style="display:none;">Adicionar ao treino</button>
                        </div>
                    `;

                    const botaoAdicionar = card.querySelector(".btn-adicionar");
                    const serieInput = card.querySelector(".input-serie");
                    const repeticaoInput = card.querySelector(".input-repeticao");
                    const cargaInput = card.querySelector(".input-carga");

                    function validarCampos() {
                        if (serieInput.value && repeticaoInput.value && cargaInput.value) {
                            botaoAdicionar.style.display = "block";
                            aviso.style.display = "none"; // 🔥 esconde o aviso
                        } else {
                            botaoAdicionar.style.display = "none";
                            aviso.style.display = "block"; // 🔥 mostra o aviso
                        }
                    }

                    [serieInput, repeticaoInput, cargaInput].forEach(input => {
                        input.addEventListener("input", validarCampos);
                    });

                    botaoAdicionar.addEventListener("click", () => {
                        adicionarClone(exercicio, card);
                        botaoAdicionar.style.color = "black";
                        botaoAdicionar.style.background = "#C5F022";
                        botaoAdicionar.textContent = "Adicionado com sucesso!";
                        botaoAdicionar.disabled = true;
                    });

                    // junta o aviso e o card dentro do wrapper
                    wrapper.appendChild(aviso);
                    wrapper.appendChild(card);

                    resultados.appendChild(wrapper);
                });
            })
            .catch(err => {
                console.error("Erro na busca de exercícios:", err);
                resultados.innerHTML = "<p>Erro ao buscar exercícios.</p>";
            });
    }


    inputBusca.addEventListener("input", buscarExercicios);
    selectGrupo.addEventListener("change", buscarExercicios);

    atualizarContador();
});
