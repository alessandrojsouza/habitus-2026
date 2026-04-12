document.addEventListener("DOMContentLoaded", function () {
    const divsData = document.querySelectorAll(".custom-date");

    divsData.forEach(div => {
        div.addEventListener("click", function () {
            const input = div.querySelector("input[type='date']");
            input.focus();
            input.click();
        });
    });

    const inputInicio = document.getElementById("data-inicio");
    const inputFim = document.getElementById("data-fim");

    inputInicio.addEventListener("change", function () {
        const data = this.value;
        if (data) {
            const [ano, mes, dia] = data.split("-");
            document.getElementById("label-inicio").innerHTML = `${dia}/${mes}/${ano}`;
        }
    });

    inputFim.addEventListener("change", function () {
        const data = this.value;
        if (data) {
            const [ano, mes, dia] = data.split("-");
            document.getElementById("label-fim").innerHTML = `${dia}/${mes}/${ano}`;
        }
    });
});
