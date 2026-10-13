const campoCep = document.getElementById("cep");
const campoLocal = document.getElementById("local_evento");
const botaoCep = document.getElementById("buscar-cep");
const mensagemCep = document.getElementById("mensagem-cep");

if (campoCep && campoLocal && botaoCep && mensagemCep) {
    botaoCep.addEventListener("click", async function () {
        const cepInformado = campoCep.value.trim();
        mensagemCep.classList.remove("ajuda-erro");

        if (!/^[0-9]{5}-?[0-9]{3}$/.test(cepInformado)) {
            mensagemCep.textContent = "Informe um CEP com 8 números, como 01001-000.";
            mensagemCep.classList.add("ajuda-erro");
            campoCep.focus();
            return;
        }

        const cep = cepInformado.replace("-", "");
        const url = botaoCep.dataset.urlCep.replace("__CEP__", encodeURIComponent(cep));
        botaoCep.disabled = true;
        mensagemCep.textContent = "Consultando CEP...";
        let mensagemErro = "Não foi possível consultar o CEP. Tente novamente.";

        try {
            const resposta = await fetch(url, {
                headers: { "Accept": "application/json" }
            });
            const resultado = await resposta.json();

            if (!resultado || typeof resultado !== "object") {
                throw new Error();
            }
            if (!resposta.ok || resultado.erro) {
                mensagemErro = typeof resultado.erro === "string"
                    ? resultado.erro
                    : "Não foi possível consultar esse CEP.";
                throw new Error();
            }
            if (typeof resultado.endereco !== "string" || !resultado.endereco.trim()) {
                mensagemErro = "O CEP consultado não possui um endereço disponível.";
                throw new Error();
            }

            campoLocal.value = resultado.endereco;
            mensagemCep.textContent = "Local preenchido. Confira o endereço e complete com o número, se necessário.";
            campoLocal.focus();
        } catch {
            mensagemCep.textContent = mensagemErro;
            mensagemCep.classList.add("ajuda-erro");
        } finally {
            botaoCep.disabled = false;
        }
    });
}
