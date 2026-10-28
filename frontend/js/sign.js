(function () {
    const SIGNATURE_URL = "/api/keys/api/signature/";
    const MAX_PAYLOAD_LENGTH = 60000;

    const LOGICAL_WIDTH = 600;
    const MIN_HEIGHT = 150;
    const MAX_HEIGHT = 400;

    const params = new URLSearchParams(location.hash.slice(1));
    const token = params.get("t") || "";
    const info = params.get("i") || "";

    const canvas = document.getElementById("sign-pad");
    const ctx = canvas.getContext("2d");
    const intro = document.getElementById("sign-intro");
    const stage = document.getElementById("sign-stage");
    const startBtn = document.getElementById("sign-start");
    const alertEl = document.getElementById("sign-alert");
    const infoEl = document.getElementById("sign-info");
    const stageInfoEl = document.getElementById("sign-stage-info");
    const hintEl = document.getElementById("sign-hint");
    const doneEl = document.getElementById("sign-done");
    const clearBtn = document.getElementById("sign-clear");
    const sendBtn = document.getElementById("sign-send");

    function showAlert(message, ok = false) {
        alertEl.textContent = message;
        alertEl.classList.add("visible");
        alertEl.classList.toggle("ok", ok);
    }

    if (!/^[0-9a-f]{32}$/.test(token)) {
        startBtn.classList.add("hidden");
        showAlert("Érvénytelen vagy hiányos hivatkozás. Olvasd be újra a QR kódot.");
        return;
    }

    if (info) {
        infoEl.textContent = info;
        infoEl.classList.remove("hidden");
        stageInfoEl.textContent = info;
    }

    let drawing = false;
    let hasInk = false;
    let last = null;

    function clearPad() {
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = "#111111";
        ctx.fillStyle = "#111111";
        ctx.lineWidth = 4;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        hasInk = false;
        sendBtn.disabled = true;
        hintEl.classList.remove("hidden");
    }

    function sizeCanvas() {
        const rect = canvas.getBoundingClientRect();
        if (!rect.width || !rect.height) return;

        const height = Math.round((LOGICAL_WIDTH * rect.height) / rect.width);
        canvas.width = LOGICAL_WIDTH;
        canvas.height = Math.min(MAX_HEIGHT, Math.max(MIN_HEIGHT, height));
        clearPad();
    }


    async function enterLandscape() {
        try {
            const root = document.documentElement;
            if (root.requestFullscreen && !document.fullscreenElement) {
                await root.requestFullscreen();
            }
        } catch {
        }
        try {
            if (screen.orientation && screen.orientation.lock) {
                await screen.orientation.lock("landscape");
            }
        } catch {
        }
    }

    async function leaveLandscape() {
        try {
            if (screen.orientation && screen.orientation.unlock) {
                screen.orientation.unlock();
            }
            if (document.fullscreenElement && document.exitFullscreen) {
                await document.exitFullscreen();
            }
        } catch {
        }
    }

    startBtn.addEventListener("click", async () => {
        intro.classList.add("hidden");
        stage.classList.remove("hidden");
        alertEl.classList.remove("visible");
        sizeCanvas();

        await enterLandscape();
        if (!hasInk) sizeCanvas();
    });

    window.addEventListener("resize", () => {
        if (!hasInk && !stage.classList.contains("hidden")) sizeCanvas();
    });


    function position(event) {
        const rect = canvas.getBoundingClientRect();
        return {
            x: ((event.clientX - rect.left) * canvas.width) / rect.width,
            y: ((event.clientY - rect.top) * canvas.height) / rect.height,
        };
    }

    canvas.addEventListener("pointerdown", (event) => {
        event.preventDefault();
        canvas.setPointerCapture(event.pointerId);
        drawing = true;
        last = position(event);

        ctx.beginPath();
        ctx.arc(last.x, last.y, ctx.lineWidth / 2, 0, Math.PI * 2);
        ctx.fill();

        hasInk = true;
        sendBtn.disabled = false;
        hintEl.classList.add("hidden");
    });

    canvas.addEventListener("pointermove", (event) => {
        if (!drawing) return;
        event.preventDefault();
        const point = position(event);

        ctx.beginPath();
        ctx.moveTo(last.x, last.y);
        ctx.lineTo(point.x, point.y);
        ctx.stroke();
        last = point;
    });

    function stopDrawing() {
        drawing = false;
        last = null;
    }

    canvas.addEventListener("pointerup", stopDrawing);
    canvas.addEventListener("pointercancel", stopDrawing);

    clearBtn.addEventListener("click", () => {
        alertEl.classList.remove("visible");
        clearPad();
    });

    sendBtn.addEventListener("click", async () => {
        const payload = canvas.toDataURL("image/png");

        if (payload.length > MAX_PAYLOAD_LENGTH) {
            showAlert("Az aláírás túl nagy. Töröld, és írd alá egyszerűbben.");
            return;
        }

        sendBtn.disabled = true;
        clearBtn.disabled = true;

        try {
            const response = await fetch(SIGNATURE_URL + token, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ format: "SIGNATURE", payload }),
            });

            if (!response.ok) {
                let message = `Hiba (${response.status})`;
                try {
                    const data = await response.json();
                    if (data && typeof data.message === "string") message = data.message;
                } catch {
                }
                throw new Error(message);
            }

            await leaveLandscape();
            stage.classList.add("hidden");
            alertEl.classList.remove("visible");

            if (doneEl) {
                doneEl.classList.remove("hidden");
            } else {
                showAlert("Sikeres aláírás!", true);
            }
        } catch (error) {
            showAlert(error.message || "Nem sikerült elküldeni az aláírást.");
            sendBtn.disabled = false;
            clearBtn.disabled = false;
        }
    });
})();