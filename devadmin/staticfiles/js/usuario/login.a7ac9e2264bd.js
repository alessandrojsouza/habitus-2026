//js do olho para ver senha digitada//
function toggleSenha() {
    const senhaInput = document.getElementById("senha");
    const olhoIcone = document.getElementById("iconeSenha");

    const imgAberto = olhoIcone.dataset.aberto;
    const imgFechado = olhoIcone.dataset.fechado;

    if (senhaInput.type === "password") {
        senhaInput.type = "text";
        olhoIcone.src = imgAberto;
    } else {
        senhaInput.type = "password";
        olhoIcone.src = imgFechado;
    }
}


//js da notificacao de erro no login//
window.addEventListener('DOMContentLoaded', () => {
            const errorToast = document.getElementById('error-toast');
            if (errorToast) {
                setTimeout(() => {
                    errorToast.style.opacity = '0';
                    setTimeout(() => {
                        errorToast.style.display = 'none';
                    }, 500); // tempo da transição CSS
                }, 5000); // 5 segundos visível
            }
        });