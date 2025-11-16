// 🌿 Cana-ML Front-End Logic (versão final)
// Suporte ao histórico + GPS + preview + upload

document.addEventListener("DOMContentLoaded", () => {

    // ====================================
    // ENVIO DA IMAGEM PARA ANÁLISE
    // ====================================

    let userLocation = null;

// Solicitar geolocalização ao abrir
if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            userLocation = {
                lat: pos.coords.latitude.toFixed(6),
                lon: pos.coords.longitude.toFixed(6)
            };
            console.log("GPS capturado:", userLocation);
        },
        (err) => {
            console.warn("GPS negado ou indisponível.", err);
        }
    );
} else {
    console.warn("Geolocalização não suportada.");
}

    const uploadForm = document.getElementById("uploadForm");

    if (uploadForm) {
        uploadForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const fileInput = document.getElementById("imageInput");
            const file = fileInput.files[0];

            if (!file) {
                alert("Selecione uma imagem!");
                return;
            }

            const formData = new FormData();
            formData.append("file", file);

// Adicionar localização, caso disponível
if (userLocation) {
    formData.append("lat", userLocation.lat);
    formData.append("lon", userLocation.lon);
}

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

                // Exibir resultado
                resultBox.innerHTML = `
                    <p><b>Classe:</b> ${data.prediction}</p>
                    <p><b>Confiança:</b> ${(data.confidence * 100).toFixed(1)}%</p>
                    <p><b>Data:</b> ${data.timestamp}</p>

                    ${data.gps_link 
                        ? `<p><a href="${data.gps_link}" target="_blank" class="map-link">📍 Ver no mapa</a></p>`
                        : `<p>📍 Sem localização</p>`
                    }

                    <div class="img-box mt-3">
                        <img src="/uploads/${data.file}" alt="Imagem analisada">
                    </div>
                `;

                // Atualiza histórico
                loadRecent();

            } catch (err) {
                console.error(err);
                resultBox.innerHTML = `<p class="alert">Erro ao processar a imagem.</p>`;
            }
        });
    }

    // ====================================
    // CARREGAR HISTÓRICO DINÂMICO
    // ====================================
    async function loadRecent() {
        const container = document.querySelector(".recent-list");
        if (!container) return;

        try {
            const res = await fetch("/api/recent");
            const data = await res.json();

            if (!data.length) {
                container.innerHTML = "<p>Nenhuma análise recente.</p>";
                return;
            }

            container.innerHTML = data
                .map(item => `
                    <div class="recent-item">
                        <div class="img-box">
                            <img src="${item.file_url}" alt="Imagem analisada">
                        </div>

                        <div class="info">
                            <p><b>Classe:</b> ${item.prediction}</p>
                            <p><b>Confiança:</b> ${(item.confidence * 100).toFixed(1)}%</p>
                            <p><b>Data:</b> ${item.timestamp}</p>

                            ${item.gps_link
                                ? `<p><a href="${item.gps_link}" target="_blank" class="map-link">📍 Ver no mapa</a></p>`
                                : `<p>📍 Sem localização</p>`
                            }
                        </div>
                    </div>
                `)
                .join("");

        } catch (error) {
            console.error("Erro ao carregar histórico:", error);
            container.innerHTML = "<p>Erro ao carregar histórico.</p>";
        }
    }

    // Executa carregamento automático
    loadRecent();
});







