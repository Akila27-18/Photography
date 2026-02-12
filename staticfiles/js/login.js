console.log("login.js loaded");

// -------------------------
// Password toggle
// -------------------------
function togglePassword() {
    const pwd = document.getElementById("password");
    if (!pwd) {
        console.error("Password input not found");
        return;
    }
    pwd.type = pwd.type === "password" ? "text" : "password";
}

// -------------------------
// Fetch login page config
// -------------------------
function refreshLoginConfig() {
    fetch("/accounts/api/login-config/")
        .then(res => res.json())
        .then(data => {
            const welcome = document.querySelector(".welcome-text");
            if (welcome) {
                // Preserve line breaks in welcome text
                welcome.innerHTML = data.welcome_text.replace(/\n/g, "<br>");
            }
        })
        .catch(err => console.error("Failed to load login config:", err));
}

// Initial fetch and refresh every 5 seconds
refreshLoginConfig();
setInterval(refreshLoginConfig, 5000);

// -------------------------
// Role switch redirect
// -------------------------
document.addEventListener("DOMContentLoaded", () => {
    const adminRadio = document.getElementById("role-admin");
    const teamRadio = document.getElementById("role-team");

    if (adminRadio) {
        adminRadio.addEventListener("change", () => {
            if (adminRadio.checked) window.location.href = "/accounts/login/";
        });
    }

    if (teamRadio) {
        teamRadio.addEventListener("change", () => {
            if (teamRadio.checked) window.location.href = "/accounts/team-login/";
        });
    }
});
