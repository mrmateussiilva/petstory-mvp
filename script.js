// Em produção (ex.: GitHub Pages), defina window.API_URL no index.html antes deste script.
const API_URL = typeof window !== "undefined" && window.API_URL ? window.API_URL : "http://localhost:8000";
const MAX_FILES = 5;
const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB

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

function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

addEventListener("DOMContentLoaded", () => {
    const params = new URLSearchParams(location.search);
    const checkout = params.get("checkout");
    const resultEl = document.getElementById("checkout-result");
    const formContainer = document.getElementById("form-container");
    const canonicalEl = document.querySelector('link[rel="canonical"]');
    const robotsEl = document.querySelector('meta[name="robots"]');
    const pageTitle = "Livro Personalizado do Pet em PDF | PetStory";

    if (canonicalEl && location.origin && location.origin !== "null") {
        canonicalEl.href = location.origin + location.pathname;
    }

    if (checkout && resultEl && formContainer) {
        const titleEl = document.getElementById("checkout-result-title");
        const msgEl = document.getElementById("checkout-result-message");
        if (robotsEl) {
            robotsEl.setAttribute("content", "noindex, nofollow");
        }
        if (checkout === "success") {
            resultEl.classList.add("success");
            resultEl.classList.add("is-visible");
            resultEl.removeAttribute("hidden");
            if (titleEl) titleEl.textContent = "Pagamento confirmado!";
            if (msgEl) msgEl.textContent = "Em breve processaremos seu pedido e você receberá o livro por email.";
            formContainer.style.display = "none";
            document.title = "Pagamento confirmado | PetStory";
        } else if (checkout === "cancel") {
            resultEl.classList.add("cancel");
            resultEl.classList.add("is-visible");
            resultEl.removeAttribute("hidden");
            if (titleEl) titleEl.textContent = "Pagamento cancelado";
            if (msgEl) msgEl.textContent = "Você pode criar sua história quando quiser.";
            formContainer.style.display = "none";
            document.title = "Pagamento cancelado | PetStory";
        }
    } else {
        document.title = pageTitle;
    }

    const ogUrlEl = document.querySelector('meta[property="og:url"]');
    const ogImageEl = document.querySelector('meta[property="og:image"]');
    const twitterImageEl = document.querySelector('meta[name="twitter:image"]');
    if (location.origin && location.origin !== "null") {
        if (ogUrlEl) {
            ogUrlEl.setAttribute("content", location.origin + location.pathname);
        }
        const imageUrl = location.origin + "/image_com_efeito.png";
        if (ogImageEl) {
            ogImageEl.setAttribute("content", imageUrl);
        }
        if (twitterImageEl) {
            twitterImageEl.setAttribute("content", imageUrl);
        }
    }

    const overlay = document.getElementById("checkout-cta-overlay");
    const dropZone = document.getElementById("drop-zone");
    const fileInput = document.getElementById("pet-file");
    const fileListEl = document.getElementById("file-list");

    let selectedFiles = [];

    function filterValidFiles(files) {
        const list = Array.from(files).filter((f) => f.type.startsWith("image/"));
        if (list.length > MAX_FILES) {
            showAlert("Máximo 5 imagens. Serão usadas as primeiras 5.");
            return list.slice(0, MAX_FILES);
        }
        const tooBig = list.find((f) => f.size > MAX_FILE_BYTES);
        if (tooBig) {
            showAlert(tooBig.name + " tem mais de 10 MB e foi ignorado.");
            return list.filter((f) => f.size <= MAX_FILE_BYTES);
        }
        return list;
    }

    function setFiles(files) {
        selectedFiles = filterValidFiles(files);
        if (fileListEl) {
            fileListEl.classList.toggle("empty", selectedFiles.length === 0);
            if (selectedFiles.length === 0) {
                fileListEl.textContent = "Nenhuma imagem selecionada";
            } else {
                fileListEl.textContent = selectedFiles.length + " de 5 imagens: " + selectedFiles.map((f) => f.name + " (" + formatSize(f.size) + ")").join(", ");
            }
        }
    }

    dropZone.addEventListener("click", () => fileInput.click());
    dropZone.addEventListener("keydown", (e) => {
        if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            fileInput.click();
        }
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add("dragover");
    });
    dropZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
    });
    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove("dragover");
        const files = e.dataTransfer.files;
        if (files && files.length) setFiles(files);
    });

    fileInput.addEventListener("change", () => {
        const files = fileInput.files;
        if (files && files.length) setFiles(files);
        fileInput.value = "";
    });

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
            const formData = new FormData();
            formData.append("pet-name", petName);
            formData.append("user-email", userEmail);
            for (const file of selectedFiles) {
                formData.append("pet-file", file);
            }
            const res = await fetch(`${API_URL}/pet`, {
                method: "POST",
                body: formData,
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.detail || "Erro " + res.status);
            }
            const data = await res.json().catch(() => ({}));
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
                return;
            }
            overlay.remove();
            showAlert("História criada! Em breve processaremos seu pedido.");
        } catch (err) {
            console.error(err);
            showAlert(err.message || "Falha no envio. Verifique se a API está rodando em " + API_URL);
            overlay.style.pointerEvents = "";
            overlay.style.opacity = "";
        }
    }

    overlay.addEventListener("click", goToCheckout);

    // FAQ Accordion Logic
    const faqItems = document.querySelectorAll(".faq-item");
    faqItems.forEach((item) => {
        const header = item.querySelector(".faq-header");
        const content = item.querySelector(".faq-content");

        function setExpanded(expanded) {
            item.classList.toggle("active", expanded);
            header.setAttribute("aria-expanded", String(expanded));
            if (content) {
                content.hidden = !expanded;
            }
        }

        header.addEventListener("click", () => {
            const isActive = item.classList.contains("active");
            faqItems.forEach((i) => {
                i.classList.remove("active");
                const otherHeader = i.querySelector(".faq-header");
                const otherContent = i.querySelector(".faq-content");
                if (otherHeader) {
                    otherHeader.setAttribute("aria-expanded", "false");
                }
                if (otherContent) {
                    otherContent.hidden = true;
                }
            });
            setExpanded(!isActive);
        });
    });

    // Sticky Header Logic
    const header = document.querySelector(".header");
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            header.classList.add("scrolled");
        } else {
            header.classList.remove("scrolled");
        }
    });
});
