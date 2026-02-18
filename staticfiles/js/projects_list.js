document.addEventListener("DOMContentLoaded", function () {

    /* ===============================
       ROW CLICK NAVIGATION
    =============================== */

    const rows = document.querySelectorAll(".clickable-row");

    rows.forEach(row => {
        row.addEventListener("click", function (e) {

            // Prevent navigation if clicking on interactive elements
            if (
                e.target.closest(".status-pill") ||
                e.target.closest(".task-pill") ||
                e.target.closest("button") ||
                e.target.closest("a")
            ) {
                return;
            }

            const url = this.dataset.sessionUrl;
            if (url) {
                window.location.href = url;
            }
        });
    });



    /* ===============================
       OPTIONAL: SMOOTH HOVER EFFECT
    =============================== */

    rows.forEach(row => {
        row.addEventListener("mouseenter", function () {
            this.classList.add("row-hover");
        });

        row.addEventListener("mouseleave", function () {
            this.classList.remove("row-hover");
        });
    });



    /* ===============================
       AUTO REFRESH STATUS (if using AJAX task toggle)
    =============================== */

    window.refreshProjectRow = function(projectId, newStatus) {

        const row = document.querySelector(`[data-project-id="${projectId}"]`);
        if (!row) return;

        const statusCell = row.querySelector(".status-pill");

        if (!statusCell) return;

        if (newStatus === "pre_production" || newStatus === "selection") {
            statusCell.textContent = "In-Progress";
            statusCell.classList.remove("red");
            statusCell.classList.add("yellow");
        }

        if (newStatus === "post_production") {
            statusCell.textContent = "To be assigned";
            statusCell.classList.remove("yellow");
            statusCell.classList.add("red");
        }

        if (newStatus === "completed") {
            statusCell.textContent = "Completed";
            statusCell.classList.remove("yellow", "red");
            statusCell.style.background = "#22C55E";
            statusCell.style.color = "#fff";
        }
    };

});
