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
        throw new Error(result.message || result.message || "Failed to update profile");
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

// Backup directory selection
document
  .getElementById("directoryPickerBtn")
  .addEventListener("click", function () {
    openDirectoryPicker();
  });

// Handle directory selection
document
  .getElementById("directoryInput")
  .addEventListener("change", async function (e) {
    if (this.files.length > 0) {
      try {
        // Get the directory path
        const path = this.files[0].webkitRelativePath.split("/")[0];
        document.getElementById("backupLocation").value = path;

        // Save to server
        const response = await fetch("/api/set-backup-location", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ path: path }),
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.message);

        showAlert("success", "Backup location saved successfully");
      } catch (error) {
        console.error("Error saving backup location:", error);
        showAlert("error", "Failed to save backup location: " + error.message);
      }
    }
  });

// Create backup handler
async function createBackup() {
  const location = document.getElementById("backupLocation").value;
  if (!location) {
    showAlert("error", "Please select a backup location first");
    return;
  }

  try {
    showAlert("info", "Creating backup...");

    const response = await fetch("/api/create-backup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ location }),
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.message);

    showAlert("success", `Backup created successfully at ${location}`);
  } catch (error) {
    console.error("Backup error:", error);
    showAlert("error", "Failed to create backup: " + error.message);
  }
}

// Restore backup handler
async function restoreBackup() {
  try {
    showAlert("info", "Select backup file to restore...");

    // This would need a file input for backup file selection
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = ".zip,.bak,.backup";
    fileInput.onchange = async (e) => {
      const file = e.target.files[0];
      if (!file) return;

      const formData = new FormData();
      formData.append("backupFile", file);

      try {
        const response = await fetch("/api/restore-backup", {
          method: "POST",
          body: formData,
        });

        const result = await response.json();
        if (!response.ok) throw new Error(result.message);

        showAlert("success", "Backup restored successfully!");
        // Refresh the page or update UI as needed
        setTimeout(() => location.reload(), 1500);
      } catch (error) {
        console.error("Restore error:", error);
        showAlert("error", "Failed to restore backup: " + error.message);
      }
    };

    fileInput.click();
  } catch (error) {
    console.error("Restore error:", error);
    showAlert("error", "Failed to restore backup: " + error.message);
  }
}

// Directory picker function (works differently for web vs Electron)
function openDirectoryPicker() {
  // Check if running in Electron
  if (typeof window.electron !== "undefined") {
    window.electron
      .showOpenDialog({
        properties: ["openDirectory"],
      })
      .then((result) => {
        if (!result.canceled && result.filePaths.length > 0) {
          document.getElementById("backupLocation").value = result.filePaths[0];
          // Auto-save the path
          document
            .getElementById("directoryInput")
            .dispatchEvent(new Event("change"));
        }
      });
  } else {
    // Web browser fallback
    document.getElementById("directoryInput").click();
  }
}

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

// Initialize the page
document.addEventListener("DOMContentLoaded", function () {
  // Load current settings
  loadCurrentSettings();

  // Set up button event listeners
  document.querySelector(".btn-backup").addEventListener("click", createBackup);
  document
    .querySelector(".btn-restore")
    .addEventListener("click", restoreBackup);
});

// Load current settings from server
async function loadCurrentSettings() {
  try {
    const response = await fetch("/api/get-settings");
    const settings = await response.json();

    if (response.ok) {
      document.getElementById("username").value = settings.username || "admin";
      document.getElementById("backupLocation").value =
        settings.backupPath || "";
    }
  } catch (error) {
    console.error("Failed to load settings:", error);
  }
}
