document.addEventListener("DOMContentLoaded", function () {
    const inputBusca = document.getElementById("busca-exercicio");
    const selectGrupo = document.getElementById("filtro-grupo");
    const resultados = document.getElementById("resultados-exercicios");
    const areaSelecionados = document.getElementById("exercicios-selecionados");
    const contador = document.getElementById("quant-exercicios");
    const legenda = document.getElementById("legenda");

    if (legenda) legenda.style.display = "none";

    function atualizarContador() {
        const total = areaSelecionados.querySelectorAll(".clonado").length;
        contador.innerHTML = `<p>${total} exercício${total === 1 ? "" : "s"} inserido${total === 1 ? "" : "s"} no treino</p>`;
        legenda.style.display = total > 0 ? "flex" : "none";
    }

    function buscarExercicios() {
        const termo = inputBusca.value.trim().toLowerCase();
        const grupo = selectGrupo ? selectGrupo.value : "";
        const excluidos = Array.from(areaSelecionados.querySelectorAll(".clonado"))
            .map(c => c.getAttribute("data-id"))
            .join(",");

        resultados.innerHTML = "";

        if (!termo && !grupo) return;

        fetch(`/buscar-exercicios/?q=${encodeURIComponent(termo)}&grupo=${encodeURIComponent(grupo)}&excluidos=${encodeURIComponent(excluidos)}`)
            .then(response => response.json())
            .then(data => {
                data.forEach(exercicio => {
                    // Wrapper para o aviso
                    const wrapper = document.createElement("div");
                    wrapper.className = "wrapper-exercicio";

                    const aviso = document.createElement("div");
                    aviso.className = "overlay-aviso";
                    aviso.innerHTML = "⚠️ Preencha séries, repetições e carga para adicionar ao treino";
                    aviso.style.cssText = `
                        background: #ffeb3b;
                        padding: 5px;
                        text-align: center;
                        font-size: 13px;
                        border-radius: 12px 12px 0 0;
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
                                    <label class="grupo-muscular">${exercicio.grupo_muscular}</label>
                                </div>
                            </div>
                            <div class="inputs">
                                <div class="inputs-detalhes">
                                    <div><h2>Séries: *</h2><input type="number" placeholder="Ex: 3" class="input-serie"></div>
                                    <div><h2>Repetições: *</h2><input type="number" placeholder="Ex: 12" class="input-repeticao"></div>
                                    <div><h2>Carga: *</h2><input type="text" placeholder="Kg" class="input-carga"></div>
                                </div>
                                <div class="inputs-observacoes">
                                    <div>
                                        <h2>Observações:</h2>
                                        <input type="text" placeholder="Insira observações se necessário sobre o exercício" class="input-obs">
                                    </div>
                                </div>
                            </div>
                            <button type="button" class="btn-adicionar" style="display:none;">Adicionar ao treino</button>
                        </div>
                    `;

                    const botaoAdicionar = card.querySelector(".btn-adicionar");
                    const inputsObrigatorios = card.querySelectorAll('.inputs-detalhes input');

                    // Validar campos obrigatórios e mostrar/esconder aviso
                    function validarCampos() {
                        const todosPreenchidos = Array.from(inputsObrigatorios).every(inp => inp.value.trim() !== "");
                        if (todosPreenchidos) {
                            botaoAdicionar.style.display = "inline-block";
                            aviso.style.display = "none";
                        } else {
                            botaoAdicionar.style.display = "none";
                            aviso.style.display = "block";
                        }
                    }

                    inputsObrigatorios.forEach(input => input.addEventListener("input", validarCampos));

                    botaoAdicionar.addEventListener("click", function () {
                        const id = card.getAttribute("data-id");
                        if (areaSelecionados.querySelector(`.clonado[data-id="${id}"]`)) return;

                        const clone = card.cloneNode(true);
                        clone.classList.add("clonado");
                        clone.querySelector(".btn-adicionar").remove();

                        // Botão remover
                        const botaoExcluir = document.createElement("button");
                        botaoExcluir.className = "botao-excluir";
                        botaoExcluir.innerHTML = `
                            <img src="/static/icones-site/icone-lixo.png" alt="Excluir" style="width:1em; vertical-align:middle; margin-right:0.4em;">
                            Remover do treino
                        `;
                        botaoExcluir.addEventListener("click", () => {
                            clone.remove();
                            atualizarContador();
                        });

                        clone.appendChild(botaoExcluir);
                        areaSelecionados.appendChild(clone);
                        atualizarContador();
                        botaoAdicionar.style.color = "black";
                        botaoAdicionar.style.background = "#C5F022";
                        botaoAdicionar.textContent = "Adicionado com sucesso!";
                        botaoAdicionar.disabled = true;
                    });

                    wrapper.appendChild(aviso);
                    wrapper.appendChild(card);
                    resultados.appendChild(wrapper);
                });
            })
            .catch(err => {
                resultados.innerHTML = "<p>Erro ao buscar exercícios.</p>";
                console.error(err);
            });
    }

    inputBusca.addEventListener("input", buscarExercicios);
    if (selectGrupo) selectGrupo.addEventListener("change", buscarExercicios);

    const form = document.querySelector("form");
    form.addEventListener("submit", function () {
        const selecionados = areaSelecionados.querySelectorAll(".clonado");

        selecionados.forEach(card => {
            const id = card.getAttribute("data-id");
            const series = card.querySelector(".input-serie").value || 0;
            const repeticoes = card.querySelector(".input-repeticao").value || 0;
            const carga = card.querySelector(".input-carga").value || "0";
            const observacoes = card.querySelector(".input-obs").value || "";

            const createHidden = (name, value) => {
                const input = document.createElement("input");
                input.type = "hidden";
                input.name = name;
                input.value = value;
                return input;
            };

            form.appendChild(createHidden("exercicios", id));
            form.appendChild(createHidden("series", series));
            form.appendChild(createHidden("repeticoes", repeticoes));
            form.appendChild(createHidden("carga", carga));
            form.appendChild(createHidden("observacoes", observacoes));
        });
    });
});
