// 🌿 Cana-ML Front-End Logic
// Autor: Adão & Gemini

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("uploadForm");
    const resultBox = document.getElementById("result");

    // =====================================================
    // Envio e análise da imagem
    // =====================================================
    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();

            const file = document.getElementById("imageInput").files[0];
            if (!file) {
                alert("Por favor, selecione uma imagem antes de analisar.");
                return;
            }

            const formData = new FormData();
            formData.append("image", file);

            resultBox.innerHTML = `<p>🔄 Analisando imagem...</p>`;
            resultBox.classList.remove("hidden");

            try {
                const res = await fetch("/predict", {
                    method: "POST",
                    body: formData
                });

                const data = await res.json();

                if (data.error) {
                    resultBox.innerHTML = `<p class="alert">❌ ${data.error}</p>`;
                    return;
                }

                resultBox.innerHTML = `
                    <p><b>Classe:</b> ${data.class}</p>
                    <p><b>Confiança:</b> ${data.confidence}%</p>
                    <p>${data.explain}</p>
                    <p><b>Arquivo:</b> ${data.file}</p>
                    ${data.alert ? `<p class="alert">⚠️ ${data.alert}</p>` : ""}
                    ${data.gps_link ? `<p><a href="${data.gps_link}" target="_blank" class="map-link">📍 Ver no mapa</a></p>` : ""}
                    <p><b>Data:</b> ${data.timestamp}</p>

                    <div class="img-box mt-3">
                        <img src="${data.file_url}" alt="Imagem analisada">
                    </div>
                `;

                await loadRecent();

            } catch (err) {
                console.error("Erro na análise:", err);
                resultBox.innerHTML = `<p class="alert">Erro ao processar a imagem.</p>`;
            }
        });
    }

    // =====================================================
    // Carregar histórico de análises
    // =====================================================
    async function loadRecent() {
        const container = document.querySelector(".recent-list");
        if (!container) return;

        try {
            const res = await fetch("/recent");
            const data = await res.json();

            if (!data.length) {
                container.innerHTML = "<p>Nenhuma análise recente.</p>";
                return;
            }

            container.innerHTML = data.map(r => `
                <div class="recent-item">
                    <div class="img-box">
                        <img src="${r.file_url}" alt="Imagem analisada">
                    </div>

                    <div class="info">
                        <p><b>Classe:</b> ${r.class}</p>
                        <p><b>Confiança:</b> ${r.confidence}%</p>
                        <p><b>Data:</b> ${r.timestamp}</p>
                        ${r.alert ? `<p class="alert">${r.alert}</p>` : ""}
                        ${r.gps_link ? `<a href="${r.gps_link}" target="_blank" class="map-link">📍 Ver localização</a>` : ""}
                    </div>
                </div>
            `).join("");

        } catch (error) {
            console.error("Erro ao carregar histórico:", error);
            container.innerHTML = "<p>Erro ao carregar histórico.</p>";
        }
    }

    // Carrega o histórico automaticamente
    loadRecent();

    document.getElementById("analyzeForm").addEventListener("submit", async function(e) {
        e.preventDefault();

        document.getElementById("loading").style.display = "block";

        const fileInput = document.getElementById("fileInput");
        const file = fileInput.files[0];

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("/analyze", {
                method: "POST",
                body: formData
            });

            document.getElementById("loading").style.display = "none";
            location.reload();
        } catch (error) {
            document.getElementById("loading").style.display = "none";
            alert("Erro ao processar a imagem!");
        }
    });
});


