// demo.html is the guest prompt; only rewrite copy when we landed with ?error=.
const error = new URLSearchParams(window.location.search).get("error");
if (error) {
    const title = document.getElementById("demo-title");
    const lead = document.getElementById("demo-lead");
    const errorEl = document.getElementById("demo-error");
    const actions = document.getElementById("demo-actions");
    if (title) title.textContent = "Demo unavailable right now";
    if (lead) {
        lead.textContent = "We couldn't open the guest session. You can try again, log in, or create an account.";
    }
    if (errorEl) {
        errorEl.hidden = false;
        errorEl.textContent = error === "unavailable" ? "Could not start the demo." : error;
    }
    const guest = actions?.querySelector("[data-demo-entry]");
    if (guest) guest.textContent = "Try again";
}
