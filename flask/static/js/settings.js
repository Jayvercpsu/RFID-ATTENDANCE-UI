// Profile form submission handler
document
  .getElementById("profileForm")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value;
    const currentPassword = document.getElementById("currentPassword").value;
    const newPassword = document.getElementById("newPassword").value;
    const confirmPassword = document.getElementById("confirmPassword").value;

    // Validate passwords match if new password is provided
    if (newPassword && newPassword !== confirmPassword) {
      showAlert("error", "New passwords do not match!");
      return;
    }

    try {
      // Send update request to server
      const response = await fetch("/api/update-profile", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          currentPassword,
          newPassword,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(
          result.message || result.error || "Failed to update profile"
        );
      }

      showAlert("success", "Profile updated successfully!");
      // Clear password fields
      document.getElementById("currentPassword").value = "";
      document.getElementById("newPassword").value = "";
      document.getElementById("confirmPassword").value = "";
    } catch (error) {
      console.error("Profile update error:", error);
      showAlert("error", error.message);
    }
  });

// Helper function to show alerts
function showAlert(type, message) {
  const alertBox = document.createElement("div");
  alertBox.className = `alert alert-${type}`;
  alertBox.textContent = message;
  alertBox.style.position = "fixed";
  alertBox.style.top = "20px";
  alertBox.style.right = "20px";
  alertBox.style.padding = "10px 20px";
  alertBox.style.borderRadius = "5px";
  alertBox.style.color = "white";
  alertBox.style.zIndex = "1000";

  if (type === "success") {
    alertBox.style.backgroundColor = "#4CAF50";
  } else if (type === "error") {
    alertBox.style.backgroundColor = "#f44336";
  } else {
    alertBox.style.backgroundColor = "#2196F3";
  }

  document.body.appendChild(alertBox);
  setTimeout(() => alertBox.remove(), 3000);
}

// Backup functions
function createBackup() {
  const backupPath = document.getElementById("backupLocation").value.trim();
  if (!backupPath) {
    showAlert("error", "Please enter a backup path (e.g. D:\\Projects)");
    return;
  }

  fetch("/api/create-backup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ backup_path: backupPath }),
  })
    .then((res) => res.json())
    .then((data) => {
      if (data.success) {
        showAlert(
          "success",
          "Backup successfully created at: " + data.backup_path
        );
      } else {
        throw new Error(data.error || "Backup failed");
      }
    })
    .catch((err) => {
      console.error(err);
      if (err.message.includes("denied")) {
        showAlert("error", "Cannot backup using main directory. Try add sub folder.");
      } else {
        showAlert("error", err.message);
      }
    });
}

function restoreBackup() {
  const input = document.getElementById("restoreFileInput");
  input.value = ""; // reset any previous selection
  input.click();

  input.onchange = () => {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("backupFile", file);

    fetch("/api/restore-backup", {
      method: "POST",
      body: formData,
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showAlert("success", "Restore successful!");
          setTimeout(() => location.reload(), 1000); // optional refresh
        } else {
          throw new Error(data.error || "Restore failed");
        }
      })
      .catch((err) => {
        console.error(err);
        showAlert("error", err.message);
      });
  };
}

async function saveBackupPath(path) {
  try {
    const response = await fetch("/api/set-backup-path", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ path }),
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.message);
  } catch (error) {
    console.error("Error saving backup path:", error);
  }
}

// Initialize the page
document.addEventListener("DOMContentLoaded", function () {
  loadCurrentSettings();
});

// Load current settings from server
async function loadCurrentSettings() {
  try {
    const response = await fetch("/api/get-settings");
    const settings = await response.json();

    if (response.ok) {
      document.getElementById("username").value = settings.username || "admin";
      document.getElementById("backupLocation").value =
        settings.backup_path || "";
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
  }
}

window.createBackup = createBackup;
window.restoreBackup = restoreBackup;
