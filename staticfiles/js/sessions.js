document.addEventListener("DOMContentLoaded", function () {

    const tabs = document.querySelectorAll(".tab");
    const container = document.getElementById("sessionsContent");
    const searchInput = document.getElementById("searchInput");

    const urlParams = new URLSearchParams(window.location.search);
    let currentType = urlParams.get("type") || "upcoming";

    // Set active tab initially
    tabs.forEach(tab => {
        tab.classList.toggle("active", tab.dataset.type === currentType);
    });

    // ---------------- LOAD SESSIONS ----------------
    function loadSessions(type = currentType, search = "") {
        currentType = type;

        const params = new URLSearchParams();
        params.set("type", type);
        if (search.trim()) params.set("search", search.trim());

        fetch(`/projects/sessions/?${params.toString()}`, {
            headers: { "X-Requested-With": "XMLHttpRequest" }
        })
        .then(res => res.json())
        .then(data => {
            container.style.opacity = 0;

            setTimeout(() => {
                container.innerHTML = data.html;
                container.style.opacity = 1;
            }, 150);

            window.history.pushState({}, "", `?${params.toString()}`);
        })
        .catch(error => console.error("Error:", error));
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

});

document.addEventListener("click", function(e) {

    if (e.target.closest(".assign-team-btn")) {
        return;
    }

    const card = e.target.closest(".session-card");

    if (card) {
        const url = card.getAttribute("data-url");

        if (url) {
            window.location.href = url.trim();
        }
    }

});
