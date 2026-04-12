// Espera o DOM carregar
document.addEventListener("DOMContentLoaded", function() {
    // Pega todas as mensagens
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        // Depois de 5 segundos, adiciona a classe que esconde
        setTimeout(() => {
            alert.classList.add("hide");
            // Remove do DOM após a animação (600ms)
            setTimeout(() => alert.remove(), 600);
        }, 5000);
    });
});