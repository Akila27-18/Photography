document.addEventListener("DOMContentLoaded", function () {

    const tabs = document.querySelectorAll(".tab");
    const container = document.getElementById("sessionsContent");
    const searchInput = document.getElementById("searchInput");

    const urlParams = new URLSearchParams(window.location.search);
    let currentType = urlParams.get("type") || "upcoming";

    // Active tab initially
    tabs.forEach(tab => {
        tab.classList.toggle("active", tab.dataset.type === currentType);
    });

    // For aborting previous fetch requests
    let currentController = null;

    // ---------------- LOAD SESSIONS ----------------
    function loadSessions(type = currentType, search = "") {
        currentType = type;

        // Abort previous fetch
        if (currentController) currentController.abort();
        currentController = new AbortController();
        const signal = currentController.signal;

        const params = new URLSearchParams();
        params.set("type", type);
        if (search.trim()) params.set("search", search.trim());

        // Smooth fade-out
        container.style.transition = "opacity 0.2s ease";
        container.style.opacity = 0;

        fetch(`/projects/sessions/?${params.toString()}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" },
            signal: signal
        })
        .then(res => res.json())
        .then(data => {
            container.innerHTML = data.html;
            container.style.opacity = 1;
            window.history.pushState({}, "", `?${params.toString()}`);
        })
        .catch(error => {
            if (error.name === "AbortError") return;
            console.error("Error:", error);
            container.innerHTML = "<p class='error-text' style='text-align:center;'>Failed to load sessions. Please try again.</p>";
            container.style.opacity = 1;
        });
    }

    // ---------------- TAB CLICK ----------------
    tabs.forEach(tab => {
        tab.addEventListener("click", function (e) {
            e.preventDefault();
            tabs.forEach(t => t.classList.remove("active"));
            this.classList.add("active");
            loadSessions(this.dataset.type, searchInput.value);
        });
    });

    // ---------------- SEARCH (DEBOUNCE) ----------------
    let searchTimeout;
    if (searchInput) {
        searchInput.addEventListener("keyup", function () {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                loadSessions(currentType, this.value.trim());
            }, 300);
        });
    }

    // ---------------- BACK/FORWARD ----------------
    window.addEventListener("popstate", function(){
        const params = new URLSearchParams(window.location.search);
        const type = params.get("type") || "upcoming";
        const search = params.get("search") || "";
        loadSessions(type, search);
    });

    // ---------------- CARD CLICK ----------------
    document.addEventListener("click", function(e) {
        if (e.target.closest(".assign-team-btn")) return;

        const card = e.target.closest(".session-card");
        if (card) {
            const url = card.getAttribute("data-url");
            if (url) window.location.href = url.trim();
        }
    });

    // ---------------- CARD KEYBOARD ACCESS ----------------
    document.addEventListener("keydown", function(e) {
        const card = e.target.closest(".session-card");
        if (card && (e.key === "Enter" || e.key === " ")) {
            e.preventDefault();
            const url = card.getAttribute("data-url");
            if (url) window.location.href = url.trim();
        }
    });

});
