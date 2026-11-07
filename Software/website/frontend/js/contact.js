const CONTACT_URL = `${GROWHUB_API_ORIGIN}/api/web/contact`;

function setContactStatus(message, isError = false) {
    const status = document.getElementById("contact-status");
    if (!status) return;
    if (!message) {
        status.hidden = true;
        status.textContent = "";
        status.classList.remove("is-error", "is-success");
        return;
    }
    status.hidden = false;
    status.textContent = message;
    status.classList.toggle("is-error", isError);
    status.classList.toggle("is-success", !isError);
}

function initContactForm() {
    const form = document.getElementById("contact-form");
    const submit = document.getElementById("contact-submit");
    if (!form || !submit) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        setContactStatus("");

        const data = new FormData(form);
        const payload = {
            name: String(data.get("name") || "").trim(),
            email: String(data.get("email") || "").trim(),
            topic: String(data.get("topic") || "").trim(),
            message: String(data.get("message") || "").trim(),
            company: String(data.get("company") || "").trim(),
        };

        if (!payload.name || !payload.email || !payload.topic || payload.message.length < 10) {
            setContactStatus("Fill in your name, email, topic, and a short message.", true);
            return;
        }

        submit.disabled = true;
        submit.textContent = "Sending…";
        try {
            const response = await fetch(CONTACT_URL, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const body = await response.json().catch(() => ({}));
            if (!response.ok) {
                const detail = typeof body.detail === "string"
                    ? body.detail
                    : Array.isArray(body.detail)
                        ? body.detail.map((item) => item.msg || item).join(" ")
                        : `Could not send (${response.status})`;
                throw new Error(detail);
            }
            form.reset();
            setContactStatus("Thanks — your message is on its way. We'll get back to you soon.");
        } catch (error) {
            setContactStatus(
                error instanceof TypeError
                    ? "Could not reach the GrowHub server."
                    : error.message || "Could not send your message.",
                true,
            );
        } finally {
            submit.disabled = false;
            submit.textContent = "Send message";
        }
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initContactForm);
} else {
    initContactForm();
}
