// 🌿 Cana-ML - Front-End Unificado

document.addEventListener("DOMContentLoaded", () => {

    // =========================================================
    // 1 — ENVIO DA IMAGEM PARA ANÁLISE
    // =========================================================
    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById("imageInput");
            const file = fileInput.files[0];

            if (!file) {
                alert("Selecione uma imagem antes de analisar!");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);  // ✔ backend espera "file"

            const resultBox = document.getElementById("result");
            resultBox.classList.remove("hidden");
            resultBox.innerHTML = "<p>🔄 Processando imagem...</p>";

            try {
                const res = await fetch("/upload", {
                    method: "POST",
                    body: formData
                });

                const data = await res.json();

                if (data.error) {
                    resultBox.innerHTML = `<p class="alert">❌ ${data.error}</p>`;
                    return;
                }

                // Exibir resultado da análise
                resultBox.innerHTML = `
                    <p><b>Classe:</b> ${data.prediction}</p>
                    <p><b>Confiança:</b> ${(data.confidence * 100).toFixed(1)}%</p>
                    <p><b>Data:</b> ${data.timestamp}</p>

                    <div class="img-box mt-3">
                        <img src="/uploads/${data.file}" alt="Imagem analisada">
                    </div>
                `;

                loadRecent();

            } catch (err) {
                console.error(err);
                resultBox.innerHTML = `<p class="alert">⚠️ Erro ao processar a imagem.</p>`;
            }
        });
    }


    // =========================================================
    // 2 — CARREGAR HISTÓRICO /api/recent
    // =========================================================
    async function loadRecent() {
        const container = document.querySelector(".recent-list");
        if (!container) return; // só existe nas páginas certas

        try {
            const res = await fetch("/api/recent");
            const data = await res.json();

            if (!data.length) {
                container.innerHTML = "<p>Nenhuma análise recente.</p>";
                return;
            }

            container.innerHTML = data.map(item => `
                <div class="recent-item">
                    <div class="img-box">
                        <img src="${item.file_url}" alt="Imagem analisada">
                    </div>

                    <div class="info">
                        <p><b>Classe:</b> ${item.prediction}</p>
                        <p><b>Confiança:</b> ${(item.confidence * 100).toFixed(1)}%</p>
                        <p><b>Data:</b> ${item.timestamp}</p>
                    </div>
                </div>
            `).join("");

        } catch (error) {
            console.error("Erro ao carregar histórico:", error);
            container.innerHTML = "<p>Erro ao carregar histórico.</p>";
        }
    }

    // Carregar histórico automaticamente
    loadRecent();
});





