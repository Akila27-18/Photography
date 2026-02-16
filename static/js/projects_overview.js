document.addEventListener("DOMContentLoaded", function () {

    const buttons = document.querySelectorAll(".toggle-btn");
    const bodies = document.querySelectorAll(".overview-body");

    buttons.forEach(btn => {
        btn.addEventListener("click", function () {

            buttons.forEach(b => b.classList.remove("active"));
            this.classList.add("active");

            const target = this.dataset.target;

            bodies.forEach(body => {
                body.classList.add("hidden");
            });

            document.getElementById(target).classList.remove("hidden");
        });
    });

});
