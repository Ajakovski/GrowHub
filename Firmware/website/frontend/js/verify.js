const VERIFY_REDIRECT_DELAY_MS = 1500;

function showVerifyResult(title, message, action) {
    document.getElementById("verify-title").textContent = title;
    document.getElementById("verify-message").textContent = message;
    const button = document.getElementById("verify-action");
    if (action) {
        button.textContent = action.label;
        button.href = action.href;
        button.hidden = false;
    }
}