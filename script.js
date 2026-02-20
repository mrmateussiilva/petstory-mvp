const API_URL = "http://localhost:8000";

function showAlert(message) {
    const backdrop = document.getElementById("custom-alert");
    const messageEl = document.getElementById("alert-message");
    const okBtn = document.getElementById("alert-ok");
    messageEl.textContent = message;
    backdrop.removeAttribute("hidden");
    backdrop.classList.add("is-open");
    function close() {
        backdrop.classList.remove("is-open");
        backdrop.setAttribute("hidden", "");
        okBtn.removeEventListener("click", close);
        backdrop.removeEventListener("click", onBackdropClick);
    }
    function onBackdropClick(e) {
        if (e.target === backdrop) close();
    }
    okBtn.addEventListener("click", close);
    backdrop.addEventListener("click", onBackdropClick);
}

addEventListener("DOMContentLoaded", () => {
    const petForm = document.getElementById("pet-form");
    const overlay = document.getElementById("checkout-cta-overlay");

    async function goToCheckout(event) {
        event.preventDefault();
        event.stopPropagation();
        const petName = document.getElementById("pet-name").value.trim();
        const userEmail = document.getElementById("user-email").value.trim();
        if (!petName || !userEmail) {
            showAlert("Preencha o nome do pet e o email.");
            return;
        }
        overlay.style.pointerEvents = "none";
        overlay.style.opacity = "0.7";
        try {
            const formData = new FormData(petForm);
            const res = await fetch(`${API_URL}/pet`, {
                method: "POST",
                body: formData,
            });
            if (!res.ok) throw new Error(`Erro ${res.status}`);
            await res.json().catch(() => ({}));
            overlay.remove();
            const wrapper = document.getElementById("checkout-cta-wrapper");
            const yampiButton = wrapper.querySelector("a, button, [role='button']");
            if (yampiButton) yampiButton.click();
        } catch (err) {
            console.error(err);
            showAlert("Falha no envio. Verifique se a API está rodando em " + API_URL);
            overlay.style.pointerEvents = "";
            overlay.style.opacity = "";
        }
    }

    overlay.addEventListener("click", goToCheckout);
});