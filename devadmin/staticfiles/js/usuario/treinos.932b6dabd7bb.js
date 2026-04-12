document.addEventListener("DOMContentLoaded", () => {
    const btnsOpcoes = document.querySelectorAll(".btn-opcoes");

    btnsOpcoes.forEach(btn => {
        const menu = btn.parentElement.querySelector(".dropdown-opcoes");

        // Mostrar/ocultar ao clicar no botão
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            menu.classList.toggle("hidden");
        });

        // Fechar ao clicar fora
        document.addEventListener("click", (e) => {
            if (!btn.contains(e.target) && !menu.contains(e.target)) {
                menu.classList.add("hidden");
            }
        });
    });
});
