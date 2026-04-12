function removerNovaFoto() {
    const input = document.getElementById('id_nova_foto');
    const preview = document.getElementById('preview-foto');
    const salvarBtn = document.getElementById('salvar-foto-btn');
    const removerBtn = document.getElementById('remover-foto-btn');
    const padraoBtn = document.getElementById('foto-padrao');

    input.value = '';

    // Usa a imagem original se existir, senão a padrão
    const original = preview.dataset.original;
    const padrao = preview.dataset.padrao;  // precisa estar definido no HTML

    preview.src = original || padrao;

    salvarBtn.style.display = 'none';
    removerBtn.style.display = 'none';
    padraoBtn.style.display = 'none';
}

function previewNovaFoto() {
    const input = document.getElementById('id_nova_foto');
    const preview = document.getElementById('preview-foto');
    const salvarBtn = document.getElementById('salvar-foto-btn');
    const removerBtn = document.getElementById('remover-foto-btn');
    const padraoBtn = document.getElementById('foto-padrao');

    const file = input.files[0];
    if (file) {
        preview.src = URL.createObjectURL(file);
        salvarBtn.style.display = 'inline-block';
        removerBtn.style.display = 'inline-block';
        padraoBtn.style.display = 'inline-block';
    }
}
