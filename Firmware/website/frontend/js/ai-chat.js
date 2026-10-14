const GROWHUB_AI_ORIGIN = window.GROWHUB_AI_ORIGIN
    || `${window.location.protocol === "https:" ? "https:" : "http:"}//${window.location.hostname || "localhost"}:8001`;
const MAX_CHAT_HISTORY = 20;

const chatHistory = [];

function appendChatMessage(text, className) {
    const log = document.getElementById("ai-chat-log");
    log.querySelector(".chat-empty")?.remove();

    const item = document.createElement("div");
    item.className = `chat-message ${className}`;
    item.textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
    return item;
}

function setChatBusy(isBusy) {
    const form = document.getElementById("ai-chat-form");
    form.querySelectorAll("input, button").forEach((element) => {
        element.disabled = isBusy;
    });
    document.querySelectorAll("#ai-chat-suggestions button").forEach((button) => {
        button.disabled = isBusy;
    });
}

async function sendChatMessage(text) {
    const question = text.trim();
    if (!question) return;

    const input = document.getElementById("ai-chat-input");
    input.value = "";
    document.getElementById("ai-chat-suggestions").hidden = true;

    chatHistory.push({ role: "user", content: question });
    appendChatMessage(question, "from-user");
    const pending = appendChatMessage("Checking your GrowHub...", "from-assistant is-pending");
    setChatBusy(true);

    try {
        const response = await fetch(`${GROWHUB_AI_ORIGIN}/chat`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                hub_id: typeof currentHubId === "undefined" ? null : currentHubId,
                messages: chatHistory.slice(-MAX_CHAT_HISTORY),
            }),
        });
        const data = await response.json().catch(() => ({}));
        if (response.status === 401) redirectToLogin();
        if (!response.ok) {
            throw new Error(typeof data.detail === "string" ? data.detail : `AI request failed (${response.status})`);
        }

        chatHistory.push({ role: "assistant", content: data.reply });
        pending.className = "chat-message from-assistant";
        pending.textContent = data.reply;
    } catch (error) {
        chatHistory.pop();
        pending.className = "chat-message is-error";
        pending.textContent = error instanceof TypeError
            ? "Could not reach the GrowHub AI service."
            : error.message;
    } finally {
        setChatBusy(false);
        input.focus();
    }
}

function initAiChat() {
    const form = document.getElementById("ai-chat-form");
    if (!form) return;

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendChatMessage(document.getElementById("ai-chat-input").value);
    });

    document.getElementById("ai-chat-suggestions").addEventListener("click", (event) => {
        const button = event.target.closest("button");
        if (button) sendChatMessage(button.textContent);
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAiChat);
} else {
    initAiChat();
}
