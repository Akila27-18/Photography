// -----------------------------
// CSRF Helper
// -----------------------------
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// -----------------------------
// Safe AJAX Helper
// -----------------------------
async function postJSON(url, data) {
  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });

    if (!res.ok) {
      throw new Error(`Server error: ${res.status}`);
    }

    return await res.json();

  } catch (err) {
    console.error("Request failed:", err);
    return { success: false, error: err.message || "Network error" };
  }
}

// -----------------------------
// Save Project Fields (Batch)
// -----------------------------
document.getElementById('save-project')?.addEventListener('click', async function () {

  if (this.dataset.processing === "true") return;
  this.dataset.processing = "true";

  const inputs = document.querySelectorAll('input[data-field][data-project-id]');

  for (const input of inputs) {

    const payload = {
      project_id: input.dataset.projectId,
      field: input.dataset.field,
      value: input.value
    };

    const data = await postJSON("/projects/update-field/", payload);

    if (data.success) {
      input.style.borderColor = "green";
      setTimeout(() => input.style.borderColor = "", 1500);
    } else {
      alert(`Error saving ${payload.field}: ${data.error || "Unknown error"}`);
    }
  }

  this.dataset.processing = "false";
});

// -----------------------------
// Toggle Team Members
// -----------------------------
document.querySelectorAll('.avatar[data-user-id]').forEach(avatar => {

  avatar.addEventListener('click', async function () {

    if (this.dataset.processing === "true") return;
    this.dataset.processing = "true";

    const projectId = this.dataset.projectId;
    const userId = this.dataset.userId;

    const data = await postJSON("/projects/toggle-member/", {
      project_id: projectId,
      user_id: userId
    });

    if (data.success) {
      this.classList.toggle('active');
    } else {
      alert("Failed to toggle team member: " + (data.error || "Unknown error"));
    }

    this.dataset.processing = "false";
  });

});

// -----------------------------
// Toggle Task Completion
// -----------------------------
document.querySelectorAll('.task-toggle').forEach(cb => {

  cb.addEventListener('change', async function () {

    if (this.dataset.processing === "true") return;
    this.dataset.processing = "true";

    const taskId = this.dataset.taskId;
    const completed = this.checked;

    const data = await postJSON("/projects/toggle-task/", {
      task_id: taskId,
      completed: completed
    });

    if (data.success) {

      console.log(`Completed ${data.completed}/${data.total} tasks`);

      if (data.new_status === "selection") {
        alert("All tasks completed! Project moved to Selection.");
        window.location.href = "/projects/board/";
      }

    } else {
      alert("Failed to toggle task: " + (data.error || "Unknown error"));
      this.checked = !completed; // revert checkbox on error
    }

    this.dataset.processing = "false";
  });

});

// -----------------------------
// Update Project Status Manually
// -----------------------------
document.querySelectorAll('[data-status-update]').forEach(button => {

  button.addEventListener('click', async function () {

    if (this.dataset.processing === "true") return;
    this.dataset.processing = "true";

    const projectId = this.dataset.projectId;
    const newStatus = this.dataset.statusUpdate;

    const data = await postJSON("/projects/update-status/", {
      project_id: projectId,
      new_status: newStatus
    });

    if (data.success) {
      alert(`Project status updated to ${newStatus}`);
      window.location.reload();
    } else {
      alert("Failed to update status: " + (data.error || "Unknown error"));
    }

    this.dataset.processing = "false";
  });

});

// -----------------------------
// Send Notifications
// -----------------------------
document.getElementById('send-notifications')?.addEventListener('click', async function () {

  if (this.dataset.processing === "true") return;
  this.dataset.processing = "true";

  const projectId = this.dataset.projectId;

  const data = await postJSON(`/projects/${projectId}/send-notifications/`, {});

  if (data.success) {
    alert("Notifications sent successfully!");
  } else {
    alert("Failed to send notifications: " + (data.error || "Unknown error"));
  }

  this.dataset.processing = "false";
});

document.querySelectorAll(".photo-card").forEach(card => {
  card.addEventListener("click", function() {
    this.classList.toggle("selected");
  });
});

document.getElementById("save-selection").addEventListener("click", async function() {

  const selected = [];
  document.querySelectorAll(".photo-card.selected").forEach(card => {
    selected.push(card.dataset.photoId);
  });

  await fetch(window.location.pathname + "save/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": getCookie("csrftoken")
    },
    body: JSON.stringify({ selected_ids: selected })
  });

  alert("Selection saved!");
});
