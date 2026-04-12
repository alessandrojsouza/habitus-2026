// static/js/menu.js

function toggleMenu() {
    const menu = document.getElementById("menu-lateral");
    const icon = document.getElementById("menu-icon");

    menu.classList.toggle("ativo");

    if (menu.classList.contains("ativo")) {
        icon.src = "/static/icones-site/menu-lateral.png"; // ícone "X"
    } else {
        icon.src = "/static/icones-site/menu-lateral.png"; // ícone menu
    }
}
