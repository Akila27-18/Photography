document.addEventListener("DOMContentLoaded", function () {

    let selectedToken = null;

    const selectionModal = document.getElementById("selectionModal");
    const selectionPassword = document.getElementById("selectionPassword");
    const selectionError = document.getElementById("selectionError");
    const selectionSubmitBtn = document.getElementById("selectionSubmitBtn");
    const selectionCloseBtn = document.getElementById("selectionCloseBtn");

    // =========================
    // PROJECT CARD CLICK LOGIC
    // =========================
    document.querySelectorAll(".project-card").forEach(card => {

        // SELECTION COLUMN
        if (card.dataset.token) {
            card.addEventListener("click", function () {
                selectedToken = this.dataset.token;
                selectionPassword.value = "";
                selectionError.textContent = "";
                selectionModal.classList.add("active");
            });
        }

        // SESSION COLUMNS
        else if (card.dataset.sessionUrl) {
            card.addEventListener("click", function () {
                window.location.href = this.dataset.sessionUrl;
            });
        }

        card.style.cursor = "pointer";
    });

    // =========================
    // CLOSE MODAL
    // =========================
    selectionCloseBtn?.addEventListener("click", function () {
        selectionModal.classList.remove("active");
    });

    selectionModal?.addEventListener("click", function (e) {
        if (e.target === selectionModal) {
            selectionModal.classList.remove("active");
        }
    });

    // =========================
    // SUBMIT PASSWORD
    // =========================
    selectionSubmitBtn?.addEventListener("click", async function () {

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

            if (data.success) {
                window.location.href = `/projects/selection/${selectedToken}/`;
            } else {
                selectionError.textContent = data.error || "Invalid password";
            }

        } catch (error) {
            console.error(error);
            selectionError.textContent = "Something went wrong.";
        }
    });

    // =========================
    // DRAG & DROP
    // =========================
    if (typeof Sortable !== "undefined") {
        document.querySelectorAll(".cards").forEach(column => {

            if (column.closest(".selection")) return;

            new Sortable(column, {
                group: "projects",
                animation: 150,
                ghostClass: "drag-ghost",
                onEnd: async evt => {

                    const projectId = evt.item.dataset.projectId;
                    const columnId = evt.to.id;

                    let newStatus = "";

                    if (columnId.includes("to-be-assigned")) newStatus = "to_assign";
                    else if (columnId.includes("pre-production")) newStatus = "pre_production";
                    else if (columnId.includes("selection")) newStatus = "selection";
                    else if (columnId.includes("post-production")) newStatus = "post_production";
                    else if (columnId.includes("completed")) newStatus = "completed";

                    try {
                        const response = await fetch(UPDATE_STATUS_URL, {
                            method: "POST",
                            headers: {
                                "Content-Type": "application/json",
                                "X-CSRFToken": getCookie("csrftoken")
                            },
                            body: JSON.stringify({
                                project_id: projectId,
                                new_status: newStatus
                            })
                        });

                        const data = await response.json();

                        if (!data.success) {
                            evt.from.appendChild(evt.item);
                        }

                    } catch (err) {
                        evt.from.appendChild(evt.item);
                        console.error("Status update failed:", err);
                    }
                }
            });
        });
    }

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

});
