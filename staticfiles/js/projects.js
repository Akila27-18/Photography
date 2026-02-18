document.addEventListener("DOMContentLoaded", function () {
    initializeSortable();
    initializeModals();
    initializeAssignModal();
    initializeFilters();
});

/* =========================
   DRAG & DROP
========================= */
function initializeSortable() {
    if (typeof Sortable === "undefined") return;

    document.querySelectorAll(".cards").forEach(column => {
        new Sortable(column, {
            group: "projects",
            animation: 150,
            ghostClass: "drag-ghost",
            onEnd: async function (evt) {
                const projectId = evt.item.dataset.projectId;
                const sessionUrl = evt.item.dataset.sessionUrl;
                const columnId = evt.to.id;

                let newStatus = "";
                if (columnId.includes("to-be-assigned")) newStatus = "to_assign";
                else if (columnId.includes("pre-production")) newStatus = "pre_production";
                else if (columnId.includes("selection")) newStatus = "selection";
                else if (columnId.includes("post-production")) newStatus = "post_production";
                else if (columnId.includes("completed")) newStatus = "completed";
                if (!newStatus) return;

                try {
                    const response = await fetch(UPDATE_STATUS_URL, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken": getCookie("csrftoken")
                        },
                        body: JSON.stringify({ project_id: projectId, new_status: newStatus })
                    });
                    const data = await response.json();

                    if (!data.success) {
                        evt.from.appendChild(evt.item);
                        return;
                    }

                    if (newStatus === "pre_production" && sessionUrl) {
                        window.location.href = sessionUrl;
                    }

                } catch (error) {
                    console.error("Status update failed:", error);
                    evt.from.appendChild(evt.item);
                }
            }
        });
    });
}

/* =========================
   CARD CLICKS + MODALS
========================= */
function initializeModals() {
    const selectionModal = document.getElementById("selectionModal");
    const selectionPassword = document.getElementById("selectionPassword");
    const selectionError = document.getElementById("selectionError");
    const selectionSubmitBtn = document.getElementById("selectionSubmitBtn");
    const selectionCloseBtn = document.getElementById("selectionCloseBtn");

    let selectedToken = null;

    document.querySelectorAll(".project-card").forEach(card => {
        card.addEventListener("click", function () {

            if (card.closest(".selection")) {
                const token = card.dataset.token;
                if (!token) return;
                selectedToken = token;
                selectionPassword.value = "";
                selectionError.textContent = "";
                selectionModal.classList.add("active");
                return;
            }

            if (card.closest(".pre-production") || card.closest(".post-production")) {
                const sessionUrl = card.dataset.sessionUrl;
                if (sessionUrl) window.location.href = sessionUrl;
                return;
            }
        });
    });

    // Close modal
    selectionCloseBtn?.addEventListener("click", () => selectionModal.classList.remove("active"));
    selectionModal?.addEventListener("click", (e) => {
        if (e.target === selectionModal) selectionModal.classList.remove("active");
    });

    // Submit password
    selectionSubmitBtn?.addEventListener("click", async () => {
        if (!selectedToken) return;
        const password = selectionPassword.value.trim();
        if (!password) {
            selectionError.textContent = "Password cannot be empty";
            return;
        }
        try {
            const response = await fetch(`/projects/selection/${selectedToken}/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "X-CSRFToken": getCookie("csrftoken"),
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: new URLSearchParams({ password })
            });
            const data = await response.json();
            if (data.success) window.location.href = `/projects/selection/${selectedToken}/`;
            else selectionError.textContent = data.error || "Invalid password";
        } catch {
            selectionError.textContent = "Something went wrong.";
        }
    });
}

/* =========================
   ASSIGN MODAL
========================= */
function initializeAssignModal() {
    const assignModal = document.getElementById("assignModal");
    const assignCloseBtn = document.getElementById("assignCloseBtn");
    const assignNowBtn = document.getElementById("assignNowBtn");

    if (!assignModal) return;

    if (typeof TO_ASSIGN_COUNT !== "undefined" && TO_ASSIGN_COUNT > 0) {
        assignModal.classList.add("active");
    }

    assignCloseBtn?.addEventListener("click", () => assignModal.classList.remove("active"));
    assignModal.addEventListener("click", (e) => {
        if (e.target === assignModal) assignModal.classList.remove("active");
    });

    assignNowBtn?.addEventListener("click", () => {
        assignModal.classList.remove("active");
        const toBeAssignedColumn = document.getElementById("to-be-assigned-cards");
        if (toBeAssignedColumn) {
            toBeAssignedColumn.scrollIntoView({ behavior: "smooth", block: "start" });
            toBeAssignedColumn.classList.add("highlight");
            setTimeout(() => toBeAssignedColumn.classList.remove("highlight"), 2000);
        }
    });
}

/* =========================
   FILTER DROPDOWN
========================= */
function initializeFilters() {
    const toggleBtn = document.getElementById("filterToggle");
    const panel = document.getElementById("filtersPanel");

    if (!toggleBtn || !panel) return;

    toggleBtn.addEventListener("click", function(e) {
        e.stopPropagation();
        panel.classList.toggle("hidden");
    });

    // Prevent clicks inside panel from closing it
    panel.addEventListener("click", function(e) {
        e.stopPropagation();
    });

    // Clicking outside closes the panel
    document.addEventListener("click", function() {
        panel.classList.add("hidden");
    });
}

/* =========================
   CSRF HELPER
========================= */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== "") {
        document.cookie.split(";").forEach(cookie => {
            cookie = cookie.trim();
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            }
        });
    }
    return cookieValue;
}
