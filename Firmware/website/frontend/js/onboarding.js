const ONBOARDING_URL = `${AUTH_URL}/onboarding`;

const QUIZ_STEPS = [
    {
        key: "goal",
        title: "What are you here for?",
        lead: "No wrong answer — this just shapes the setup we suggest.",
        multi: false,
    },
    {
        key: "harvest",
        title: "How hungry is this grow?",
        lead: "Think about how much you'd love to harvest in a good week.",
        multi: false,
    },
    {
        key: "plant_ids",
        title: "What do you want to grow?",
        lead: "Pick as many as you like. We'll match grid sizes to the plants.",
        multi: true,
    },
    {
        key: "time",
        title: "How much time do you have?",
        lead: "Be honest — GrowHub should fit your week, not fight it.",
        multi: false,
    },
    {
        key: "experience",
        title: "Where are you starting from?",
        lead: "We'll keep the first setup friendlier if you're brand new.",
        multi: false,
    },
    {
        key: "space",
        title: "How much room can it take?",
        lead: "A hub base holds up to 3 floors. More floors means more hubs.",
        multi: false,
    },
];

const TOUR_STEPS = [
    {
        selector: "#dashboard-header",
        kicker: "Your live desk",
        title: "This is mission control",
        text: "When a hub is online, the status pill and timestamps tell you the data is fresh — not a dusty screenshot.",
    },
    {
        selector: "#ai-status-card",
        kicker: "AI glance",
        title: "A gut check in one sentence",
        text: "The AI peeks at sensors (and photos when it can) and leaves a short Healthy / Watch / Action needed note here.",
    },
    {
        selector: "#reservoir-heading, #hub-metrics",
        kicker: "The shared bath",
        title: "One reservoir for every floor",
        text: "Water temp, nutrients (EC) and pH live in the hub base. Every floor drinks from this same tank.",
    },
    {
        selector: "#tiles-heading, #device-selector, #tile-metrics",
        kicker: "Per-floor vibes",
        title: "Each floor has its own climate",
        text: "Air temp, humidity, light and flow are measured per floor. Flip the pills to zoom into one floor or see the average.",
    },
    {
        selector: "#camera-card",
        kicker: "Eyes on leaves",
        title: "Peek without opening the lid",
        text: "The optical node streams live when a camera is up. Stock images are handy when you're demoing without a webcam.",
    },
    {
        selector: "#ai-chat",
        kicker: "Ask anything",
        title: "Your grow buddy with tools",
        text: "Chat reads live data and photos. Ask “is my EC okay?” and it checks the real numbers before answering.",
    },
    {
        selector: "#crops-button",
        kicker: "Plant brains",
        title: "Tell GrowHub what you're growing",
        text: "This is the plant picker. It sets nutrient targets, tunes the AI, and lines the dashboard up with your crop mix — like the simulation knowing who's in the cups.",
        openPlants: true,
    },
];

let onboardPayload = null;
let quizIndex = 0;
let quizAnswers = {
    goal: null,
    harvest: null,
    plant_ids: [],
    time: null,
    experience: null,
    space: null,
};
let recommendation = null;
let tourIndex = 0;
let onboardPhase = "quiz"; // quiz | rec | tour

function showOnboardError(message) {
    const error = document.getElementById("onboard-error");
    if (!error) return;
    error.textContent = message;
    error.hidden = !message;
}

function setOnboardOpen(isOpen) {
    const modal = document.getElementById("onboard-modal");
    if (!modal) return;
    modal.hidden = !isOpen;
    document.body.classList.toggle("onboard-open", isOpen);
}

function optionSelected(stepKey, optionId) {
    if (stepKey === "plant_ids") return quizAnswers.plant_ids.includes(optionId);
    return quizAnswers[stepKey] === optionId;
}

function toggleOption(stepKey, optionId, multi) {
    if (multi) {
        const set = new Set(quizAnswers.plant_ids);
        if (set.has(optionId)) set.delete(optionId);
        else set.add(optionId);
        quizAnswers.plant_ids = [...set];
    } else {
        quizAnswers[stepKey] = optionId;
    }
    renderQuizStep();
}

function quizOptionsForStep(step) {
    if (step.key === "plant_ids") {
        return (onboardPayload?.plants || []).map((plant) => ({
            id: plant.id,
            label: plant.name,
            blurb: `${plant.blurb} · ${plant.grid_cups}-cup grid`,
        }));
    }
    return onboardPayload?.quiz?.[step.key] || [];
}

function renderProgress() {
    const progress = document.getElementById("onboard-progress");
    if (!progress) return;
    if (onboardPhase !== "quiz") {
        progress.innerHTML = "";
        return;
    }
    progress.innerHTML = QUIZ_STEPS.map((_, index) => (
        `<span class="onboard-dot${index === quizIndex ? " is-active" : ""}${index < quizIndex ? " is-done" : ""}"></span>`
    )).join("");
}

function renderQuizStep() {
    const step = QUIZ_STEPS[quizIndex];
    const body = document.getElementById("onboard-body");
    document.getElementById("onboard-kicker").textContent = `Step ${quizIndex + 1} of ${QUIZ_STEPS.length}`;
    document.getElementById("onboard-title").textContent = step.title;
    document.getElementById("onboard-lead").textContent = step.lead;
    document.getElementById("onboard-back").hidden = quizIndex === 0;
    document.getElementById("onboard-next").textContent =
        quizIndex === QUIZ_STEPS.length - 1 ? "See my setup" : "Continue";
    document.getElementById("onboard-actions").hidden = false;

    const options = quizOptionsForStep(step);
    body.innerHTML = `
        <div class="onboard-options" role="group" aria-label="${step.title}">
            ${options.map((option) => `
                <button type="button"
                    class="onboard-option${optionSelected(step.key, option.id) ? " is-selected" : ""}"
                    data-step="${step.key}"
                    data-option="${option.id}"
                    aria-pressed="${optionSelected(step.key, option.id)}">
                    <strong>${option.label}</strong>
                    <span>${option.blurb}</span>
                </button>
            `).join("")}
        </div>
    `;
    renderProgress();
    showOnboardError("");
}

function renderRecommendation(rec) {
    onboardPhase = "rec";
    recommendation = rec;
    const body = document.getElementById("onboard-body");
    document.getElementById("onboard-kicker").textContent = "Your starter kit";
    document.getElementById("onboard-title").textContent = "Here's what we'd build";
    document.getElementById("onboard-lead").textContent =
        "A hub is the base with the reservoir. Each floor is a basin, planter grid and canopy stacked on top — up to 3 floors per hub.";
    document.getElementById("onboard-back").hidden = false;
    document.getElementById("onboard-next").textContent = "Show me the dashboard";
    document.getElementById("onboard-actions").hidden = false;
    renderProgress();

    const hubs = rec.hub_layout || [];
    const grids = rec.grids || [];
    body.innerHTML = `
        <div class="onboard-rec">
            <p class="onboard-rec-headline">${rec.headline}</p>
            <p class="onboard-rec-summary">${rec.summary}</p>
            <div class="onboard-rec-grid">
                ${hubs.map((hub) => `
                    <article class="onboard-rec-card">
                        <span class="kicker">Hub ${hub.hub_index}</span>
                        <strong>${hub.floors} floor${hub.floors === 1 ? "" : "s"}</strong>
                        <span>Base + stacked grow floors</span>
                    </article>
                `).join("")}
                ${grids.map((grid) => `
                    <article class="onboard-rec-card">
                        <span class="kicker">${grid.grid_cups}-cup grid</span>
                        <strong>${grid.floors} floor${grid.floors === 1 ? "" : "s"}</strong>
                        <span>${grid.label}</span>
                    </article>
                `).join("")}
            </div>
            <ul class="onboard-why">
                ${(rec.why || []).map((line) => `<li>${line}</li>`).join("")}
            </ul>
            <button type="button" class="auth-back" id="onboard-skip-tour">Skip the tour</button>
        </div>
    `;
    document.getElementById("onboard-skip-tour")?.addEventListener("click", () => finishOnboarding({ openPlants: false }));
    showOnboardError("");
}

async function saveQuizAndShowRec() {
    const button = document.getElementById("onboard-next");
    button.disabled = true;
    showOnboardError("");
    try {
        const response = await fetch(ONBOARDING_URL, {
            method: "PUT",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(quizAnswers),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(typeof data.detail === "string" ? data.detail : `Could not save (${response.status})`);
        }
        onboardPayload = data;
        renderRecommendation(data.recommendation);
    } catch (error) {
        showOnboardError(error instanceof TypeError ? "Could not reach the GrowHub server." : error.message);
    } finally {
        button.disabled = false;
    }
}

function currentStepHasAnswer() {
    const step = QUIZ_STEPS[quizIndex];
    if (step.key === "plant_ids") return quizAnswers.plant_ids.length > 0;
    return Boolean(quizAnswers[step.key]);
}

async function handleOnboardNext() {
    if (onboardPhase === "rec") {
        setOnboardOpen(false);
        startTour();
        return;
    }
    if (!currentStepHasAnswer()) {
        showOnboardError(QUIZ_STEPS[quizIndex].key === "plant_ids"
            ? "Pick at least one plant."
            : "Pick an option to continue.");
        return;
    }
    if (quizIndex < QUIZ_STEPS.length - 1) {
        quizIndex += 1;
        renderQuizStep();
        return;
    }
    await saveQuizAndShowRec();
}

function handleOnboardBack() {
    if (onboardPhase === "rec") {
        onboardPhase = "quiz";
        quizIndex = QUIZ_STEPS.length - 1;
        renderQuizStep();
        return;
    }
    if (quizIndex > 0) {
        quizIndex -= 1;
        renderQuizStep();
    }
}

function placeTourBubble(target) {
    const bubble = document.getElementById("tour-bubble");
    const rect = target.getBoundingClientRect();
    const margin = 16;
    const bubbleWidth = Math.min(360, window.innerWidth - margin * 2);
    let left = rect.left + rect.width / 2 - bubbleWidth / 2;
    left = Math.max(margin, Math.min(left, window.innerWidth - bubbleWidth - margin));

    let top = rect.bottom + 14;
    bubble.style.width = `${bubbleWidth}px`;
    bubble.style.left = `${left}px`;
    // Measure after setting width so we know if it fits below.
    bubble.style.top = `${top}px`;
    const bubbleHeight = bubble.getBoundingClientRect().height;
    if (top + bubbleHeight > window.innerHeight - margin) {
        top = Math.max(margin, rect.top - bubbleHeight - 14);
    }
    bubble.style.top = `${top}px`;
}

function highlightTourTarget(selector) {
    const spotlight = document.getElementById("tour-spotlight");
    const parts = selector.split(",").map((part) => part.trim());
    let top = Infinity;
    let left = Infinity;
    let right = 0;
    let bottom = 0;
    let first = null;

    parts.forEach((part) => {
        const el = document.querySelector(part);
        if (!el) return;
        if (!first) first = el;
        const rect = el.getBoundingClientRect();
        top = Math.min(top, rect.top);
        left = Math.min(left, rect.left);
        right = Math.max(right, rect.right);
        bottom = Math.max(bottom, rect.bottom);
    });

    if (!first || !Number.isFinite(top)) {
        spotlight.style.display = "none";
        return document.body;
    }

    const pad = 10;
    spotlight.style.display = "block";
    spotlight.style.top = `${Math.max(0, top - pad)}px`;
    spotlight.style.left = `${Math.max(0, left - pad)}px`;
    spotlight.style.width = `${right - left + pad * 2}px`;
    spotlight.style.height = `${bottom - top + pad * 2}px`;
    first.scrollIntoView({ behavior: "smooth", block: "center" });
    return first;
}

function renderTourStep() {
    const step = TOUR_STEPS[tourIndex];
    const overlay = document.getElementById("tour-overlay");
    overlay.hidden = false;
    document.body.classList.add("tour-open");

    document.getElementById("tour-kicker").textContent = `${step.kicker} · ${tourIndex + 1}/${TOUR_STEPS.length}`;
    document.getElementById("tour-title").textContent = step.title;
    document.getElementById("tour-text").textContent = step.text;
    document.getElementById("tour-next").textContent =
        tourIndex === TOUR_STEPS.length - 1 ? "Open plant picker" : "Next";

    // Wait a tick so layout settles after scroll.
    requestAnimationFrame(() => {
        const target = highlightTourTarget(step.selector);
        placeTourBubble(target);
    });
}

function startTour() {
    onboardPhase = "tour";
    tourIndex = 0;
    // Make sure crops button is visible during the tour even before a hub reports.
    const crops = document.getElementById("crops-button");
    if (crops) crops.hidden = false;
    renderTourStep();
}

function closeTour() {
    document.getElementById("tour-overlay").hidden = true;
    document.body.classList.remove("tour-open");
}

async function finishOnboarding({ openPlants }) {
    closeTour();
    setOnboardOpen(false);
    try {
        await fetch(`${ONBOARDING_URL}/complete`, {
            method: "POST",
            credentials: "include",
        });
    } catch (error) {
        console.warn("could not mark onboarding complete:", error);
    }
    if (openPlants && typeof openPlantModal === "function") {
        try {
            if (typeof loadPlantCatalog === "function") await loadPlantCatalog();
            // Prefer plant ids from the quiz so the picker feels connected.
            if (recommendation?.plant_ids?.length && typeof selectedPlantIds !== "undefined") {
                selectedPlantIds = new Set(recommendation.plant_ids);
            }
            openPlantModal({ editing: Boolean(globalTelemetry?.crops?.configured) });
        } catch (error) {
            console.warn("could not open plant picker after tour:", error);
        }
    }
}

async function handleTourNext() {
    const step = TOUR_STEPS[tourIndex];
    if (tourIndex >= TOUR_STEPS.length - 1) {
        await finishOnboarding({ openPlants: Boolean(step.openPlants) });
        return;
    }
    tourIndex += 1;
    renderTourStep();
}

function openQuiz(payload) {
    onboardPayload = payload;
    onboardPhase = "quiz";
    quizIndex = 0;
    quizAnswers = {
        goal: payload.answers?.goal || null,
        harvest: payload.answers?.harvest || null,
        plant_ids: [...(payload.answers?.plant_ids || [])],
        time: payload.answers?.time || null,
        experience: payload.answers?.experience || null,
        space: payload.answers?.space || null,
    };
    if (payload.recommendation && payload.answers) {
        renderRecommendation(payload.recommendation);
    } else {
        renderQuizStep();
    }
    setOnboardOpen(true);
}

async function ensureOnboarding() {
    try {
        const response = await fetch(ONBOARDING_URL, { credentials: "include" });
        if (response.status === 401) {
            redirectToLogin();
            return;
        }
        if (!response.ok) throw new Error(`http error! status: ${response.status}`);
        const data = await response.json();
        onboardPayload = data;
        if (data.completed) return;
        // If they already saved answers but never finished the tour, resume at the recommendation.
        if (data.recommendation && data.answers) {
            openQuiz(data);
            return;
        }
        openQuiz(data);
    } catch (error) {
        console.warn("could not load onboarding:", error);
    }
}

function initOnboarding() {
    const modal = document.getElementById("onboard-modal");
    if (!modal) return;

    document.getElementById("onboard-body").addEventListener("click", (event) => {
        const button = event.target.closest("button[data-step][data-option]");
        if (!button || onboardPhase !== "quiz") return;
        const stepKey = button.getAttribute("data-step");
        const optionId = button.getAttribute("data-option");
        const step = QUIZ_STEPS.find((item) => item.key === stepKey);
        if (!step) return;
        toggleOption(stepKey, optionId, step.multi);
    });

    document.getElementById("onboard-next").addEventListener("click", handleOnboardNext);
    document.getElementById("onboard-back").addEventListener("click", handleOnboardBack);
    document.getElementById("tour-next").addEventListener("click", handleTourNext);
    document.getElementById("tour-skip").addEventListener("click", () => finishOnboarding({ openPlants: false }));
    window.addEventListener("resize", () => {
        if (document.getElementById("tour-overlay")?.hidden) return;
        const step = TOUR_STEPS[tourIndex];
        if (step) {
            const target = highlightTourTarget(step.selector);
            placeTourBubble(target);
        }
    });

    ensureOnboarding();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initOnboarding);
} else {
    initOnboarding();
}
