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
      showAlert("New passwords do not match!", "#f44336");
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

      showAlert("Profile updated successfully!");
      // Clear password fields
      document.getElementById("currentPassword").value = "";
      document.getElementById("newPassword").value = "";
      document.getElementById("confirmPassword").value = "";
    } catch (error) {
      console.error("Profile update error:", error);
      showAlert(error.message, "#f44336");
    }
  });

// Helper function to show alerts
function showAlert(message, color = "#4CAF50") {
  const alertBox = document.getElementById("alertBox");
  const alertMessage = document.getElementById("alertMessage");
  const progressBar = document.getElementById("alertProgress");

  alertMessage.textContent = message;
  alertBox.style.backgroundColor = color;
  alertBox.style.right = "20px";
  alertBox.style.opacity = "1";

  progressBar.style.transition = "none";
  progressBar.style.width = "0%";

  setTimeout(() => {
    progressBar.style.transition = "width 4s linear";
    progressBar.style.width = "100%";
  }, 50);

  setTimeout(() => {
    alertBox.style.opacity = "0";
    alertBox.style.right = "-400px";
  }, 4000);
}

// Backup functions
function createBackup() {
  const backupPath = document.getElementById("backupLocation").value.trim();
  if (!backupPath) {
    showAlert("Please enter a backup path (e.g. D:\\Projects)", "#f44336");
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
        showAlert("Backup successfully created at: " + data.backup_path);
      } else {
        throw new Error(data.error || "Backup failed");
      }
    })
    .catch((err) => {
      console.error(err);
      if (err.message.includes("denied")) {
        showAlert(
          "Cannot backup using main directory. Try add sub folder.",
          "#f44336"
        );
      } else {
        showAlert(err.message, "#f44336");
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
          showAlert("Restore successful!");
          setTimeout(() => location.reload(), 1000); // optional refresh
        } else {
          throw new Error(data.error || "Restore failed");
        }
      })
      .catch((err) => {
        console.error(err);
        showAlert(err.message, "#f44336");
      });
  };
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
