document.addEventListener("DOMContentLoaded", () => {
  const projectId = document
    .querySelector("[data-project-id]")
    ?.dataset.projectId;

  const csrfToken = document.querySelector(
    "[name=csrfmiddlewaretoken]"
  )?.value;

  const available = document.getElementById("availableTeam");
  const preProduction = document.getElementById("preProduction");
  const postProduction = document.getElementById("postProduction");

  if (!available || !preProduction) return;

  /* ===============================
     AVAILABLE → PRE PRODUCTION
     =============================== */

  new Sortable(available, {
    group: {
      name: "team",
      pull: "clone",   // clone from available
      put: false       // cannot drop back
    },
    sort: false,
    animation: 150
  });

  new Sortable(preProduction, {
    group: {
      name: "team",
      pull: false,     // cannot drag out
      put: true        // can receive
    },
    animation: 150,

    onAdd: function (evt) {
      const userId = evt.item.dataset.userId;

      fetch("/projects/toggle-member/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken
        },
        body: JSON.stringify({
          project_id: projectId,
          user_id: userId
        })
      })
      .then(res => res.json())
      .then(data => {
        if (!data.success) {
          evt.from.appendChild(evt.item); // rollback
        }
      });
    }
  });

  /* ===============================
     POST PRODUCTION (LOCKED)
     =============================== */

  new Sortable(postProduction, {
    group: {
      name: "team",
      put: false,
      pull: false
    },
    animation: 150
  });
});
