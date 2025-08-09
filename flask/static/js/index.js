async function loadLogs() {
  const logsContainer = document.getElementById("logsContainer");

  const res = await fetch("/api/logs?length=500");
  if (!res.ok) {
    logsContainer.innerHTML =
      "<p style='text-align:center;'>Empty logs for today</p>";
    return;
  }

  const response = await res.json();
  const logs = response.data || [];

  if (!logs.length) {
    logsContainer.innerHTML =
      "<p style='text-align:center;'>Empty logs for today</p>";
    return;
  }

  // Sort logs descending by timestamp to get the latest entry
  logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  const latestLog = logs[0];

  // Update student section with latest log
  if (latestLog) {
    document.querySelector(".student-photo").src =
      latestLog.avatar || profileIconUrl;

    document.querySelector("#studentName").textContent =
      latestLog.first_name + " " + latestLog.last_name;
    document.querySelector("#occupation").textContent =
      latestLog.occupation?.charAt(0).toUpperCase() +
        latestLog.occupation?.slice(1) || "N/A";
    document.querySelector(
      "#studentLevel"
    ).textContent = `${latestLog.grade} - ${latestLog.strandOrSec}`;
    document.querySelector("#studentStatus").textContent =
      latestLog.status == "IN" ? "Time In" : "Time Out";
    document.querySelector("#studentTime").textContent = formatTime(
      latestLog.timestamp
    );
  }

  // Update logs list
  logsContainer.innerHTML = "";

  logs.forEach((log) => {
    const entry = document.createElement("div");
    entry.className = "log-entry";

    entry.innerHTML = `
        <img src="${
          log.avatar || profileIconUrl
        }" alt="Student" class="log-avatar"
        onerror="this.onerror=null;this.src='${profileIconUrl}';"
        />
        <div class="log-info">
          <div class="log-name">${log.first_name} ${log.last_name}</div>
          <div class="log-time">${formatTime(log.timestamp)}</div>
          <div class="log-department">${log.grade} - ${log.strandOrSec}</div>
        </div>
        <div class="log-status ${
          log.status === "IN" ? "status-in" : "status-out"
        }">${log.status}</div>
      `;

    logsContainer.appendChild(entry);
  });
}

function formatTime(isoString) {
  if (!isoString) return "Unknown time";
  const date = new Date(isoString);
  return `${date.toLocaleDateString()}, ${date.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  })}`;
}

document.addEventListener("DOMContentLoaded", loadLogs);

const codeTypeRadios = document.querySelectorAll('input[name="codeType"]');
const scannerTypeRadios = document.querySelectorAll(
  'input[name="scannerType"]'
);
const scannerOptions = document.getElementById("scannerOptions");
const manualCodeInput = document.getElementById("manualCodeInput");
const scanBtn = document.getElementById("scanBtn");
const qrModal = document.getElementById("qrModal");
const rfidModal = document.getElementById("rfidModal");
const readerElement = document.getElementById("reader");
const inlineQrWrapper = document.getElementById("inlineQrScanner");
const registerModal = document.getElementById("registerModal");
const registerToggle = document.getElementById("registerToggleBtn");
const closeModalBtn = document.getElementById("closeModal");
const modalOverlay = registerModal.querySelector(".modal-overlay");
const registerForm = document.getElementById("registerForm");
const scanSound = document.getElementById("scanSound");
const scanSoundError = document.getElementById("scanSoundError");
const scanCodeValue = document.getElementById("scanCodeValue");

let scanner;
let inlineScanner;
let lastScannedCode = null;
let lastScannedTime = 0;
let scanningLocked = false;
let capturedPhotoBlob = null;
let inlineScannerRunning = false;
let allowScannerInRegisterModal = false;

function showAlert(message, color = "#4CAF50", enableSound = true) {
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
  }, 2000);

  if (enableSound) {
    const sound = color == "#4CAF50" ? scanSound : scanSoundError;
    if (sound) {
      sound.play().then(() => {
        sound.currentTime = 0;
      });
    }
  }
}

function updateUI() {
  const selectedCodeType = document.querySelector(
    'input[name="codeType"]:checked'
  ).value;

  if (selectedCodeType === "input") {
    scannerOptions.style.display = "none";
    manualCodeInput.style.display = "block";
    scanCodeValue.value = "";
  } else {
    scannerOptions.style.display = "flex";
    manualCodeInput.style.display = "none";
    manualCodeInput.value = "";
    updateScanButtonState();
  }
}

function updateScanButtonState() {
  const selectedScannerType = document.querySelector(
    'input[name="scannerType"]:checked'
  ).value;
}

codeTypeRadios.forEach((radio) => {
  radio.addEventListener("change", updateUI);
});

scannerTypeRadios.forEach((radio) => {
  radio.addEventListener("change", updateScanButtonState);
});

scanBtn.addEventListener("click", async () => {
  const selectedScannerType = document.querySelector(
    'input[name="scannerType"]:checked'
  ).value;

  if (selectedScannerType === "rfid") {
    allowScannerInRegisterModal = true;
    rfidModal.classList.add("show");
    attachScanner(true);
  }

  if (selectedScannerType === "qr") {
    if (inlineScannerRunning && inlineScanner) {
      try {
        await inlineScanner.stop();
        inlineScannerRunning = false;
      } catch (err) {
        console.warn("Scanner not running or already stopped.");
      }
    }

    qrModal.classList.add("show");
    setTimeout(() => {
      startModalScanner();
    }, 300);
  }
});

document.getElementById("closeQrModal").addEventListener("click", async () => {
  qrModal.classList.remove("show");
  if (scanner) {
    await scanner.stop();
    readerElement.innerHTML = "";
  }
});

document.getElementById("closeRFIDModal").addEventListener("click", () => {
  rfidModal.classList.remove("show");
  detachScanner();
});

updateUI(); // Initialize UI on page load

registerForm.addEventListener("submit", async function (e) {
  e.preventDefault();

  const codeType = document.querySelector(
    'input[name="codeType"]:checked'
  ).value;
  const rfidCode =
    codeType === "input" ? manualCodeInput.value : scanCodeValue.value;

  if (!rfidCode) {
    showAlert("Please enter or scan a code.", "#f44336", false);
    return;
  }

  const formData = {
    first_name: registerForm[0].value,
    middle_name: registerForm[1].value,
    last_name: registerForm[2].value,
    age: registerForm[3].value,
    gender: registerForm[4].value,
    grade: registerForm[5].value,
    section: registerForm[6].value,
    contact: registerForm[7].value,
    address: registerForm[8].value,
    guardian: registerForm[9].value,
    occupation: registerForm[10].value,
    id_number: registerForm[11].value,
    rfid_code: rfidCode,
  };

  const payload = new FormData();
  payload.append("data", JSON.stringify(formData));
  if (capturedPhotoBlob) {
    payload.append(
      "photo",
      capturedPhotoBlob,
      `${formData.first_name}_${formData.last_name}_${formData.age}.jpg`
    );
  }

  try {
    const res = await fetch("/api/register", {
      method: "POST",
      body: payload,
    });

    const result = await res.json();

    if (res.ok) {
      showAlert("Registration successful!", "#4CAF50", false);
      setTimeout(() => {
        registerForm.reset();
        qrModal.classList.remove("show");
        document.getElementById("reader").innerHTML = "";
        document.getElementById("registerModal").classList.remove("show");
        startInlineScanner();
      }, 2000);
    } else {
      console.error("Registration error:", result.error);
      showAlert(result.error || "Registration failed.", "#f44336", false);
    }
  } catch (err) {
    showAlert(
      err.message || "Failed to register. Please try again.",
      "#f44336",
      false
    );
    console.error(err);
  }
});

const takeSnapshotBtn = document.getElementById("takeSnapshot");
const video = document.getElementById("webcam");
const canvas = document.getElementById("snapshotCanvas");
let isPhotoTaken = false;

// Start webcam stream
navigator.mediaDevices
  .getUserMedia({ video: true })
  .then((stream) => {
    video.srcObject = stream;
  })
  .catch((err) => {
    console.warn("Webcam not available:", err);
  });

takeSnapshotBtn.addEventListener("click", () => {
  if (!isPhotoTaken) {
    // Take photo
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);

    // Convert to blob for upload
    canvas.toBlob((blob) => {
      capturedPhotoBlob = blob;
      showAlert("Photo captured successfully!", "#4CAF50", false);
    }, "image/jpeg");

    // Hide video, show canvas
    video.style.display = "none";
    canvas.style.display = "block";

    takeSnapshotBtn.textContent = "Retake Photo";
    isPhotoTaken = true;
  } else {
    // Retake photo: show video again
    video.style.display = "block";
    canvas.style.display = "none";

    takeSnapshotBtn.textContent = "Take Photo";
    isPhotoTaken = false;
  }
});

// Reset scanner memory every 30 minutes
setInterval(() => {
  lastScannedCode = null;
  lastScannedTime = 0;
  scanningLocked = false;
  console.log("Scanner memory reset.");
}, 30 * 60 * 1000);

function startModalScanner() {
  scanner = new Html5Qrcode("reader");
  scanner.start(
    { facingMode: "environment" },
    {
      fps: 10,
      qrbox: 250,
    },
    async (decodedText) => {
      try {
        await scanner.stop();
        qrModal.classList.remove("show");
        readerElement.innerHTML = "";
        checkRFID(decodedText);
      } catch (error) {
        showAlert("Error checking RFID", "#f44336");
      }
    },
    (err) => {
      console.error("QR Scanner error:", err);
    }
  );
}

async function checkRFID(decodedText) {
  // Call the API to check RFID
  const response = await fetch("/api/check-rfid", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rfid_code: decodedText }),
  });

  const result = await response.json();
  if (result.exists) {
    scanCodeValue.value = "";
    showAlert("RFID code already registered in our database.", "#f44336");
  } else {
    scanCodeValue.value = decodedText;
    showAlert("Successfuly scanned code.");
  }
}

async function createLogs(decodedText) {
  const now = Date.now();

  // Prevent any scanning while locked
  if (scanningLocked) return;

  if (decodedText) {
    lastScannedCode = decodedText;
    lastScannedTime = now;
    scanningLocked = true; // 🔒 lock scanner

    scanCodeValue.value = decodedText;
    console.log("Scanned QR Code:", decodedText);

    try {
      const response = await fetch("/api/log", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          rfid: decodedText,
        }),
      });

      const result = await response.json();
      if (!response.ok) {
        console.error("API Error:", result.error);

        if (result.error && result.error.includes("Already")) {
          showAlert(result.error, "#f44336");
        } else {
          showAlert("Unidentified code or not registered.", "#f44336");
        }
      } else {
        showAlert(`Successfully logged ${result.status.toLowerCase()}`);
        await loadLogs();
      }
    } catch (error) {
      console.error("Fetch error:", error);
      showAlert("Failed to log attendance. Please try again.");
    }

    // Allow rescanning of same code after 5 seconds
    setTimeout(() => {
      scanningLocked = false;
    }, 1000);
  }
}

function startInlineScanner() {
  inlineQrWrapper.style.display = "block";
  inlineScanner = new Html5Qrcode("reader2");
  inlineScanner
    .start(
      { facingMode: "environment" },
      {
        fps: 10,
        qrbox: 250,
      },
      async (decodedText) => {
        createLogs(decodedText);
      },
      (err) => {
        // error callback (optional)
      }
    )
    .then(() => {
      inlineScannerRunning = true;
    })
    .catch((err) => {
      inlineScannerRunning = false;
      console.error("Failed to start inline scanner:", err);

      // ➕ Show fallback broken-camera UI
      const readerEl = document.getElementById("reader2");
      readerEl.innerHTML = `
        <div class='camera-broken'>
          <img src="/static/images/broken_camera.png" alt="Camera unavailable" />
          <p>
            Unable to access camera<br/>Please enable or connect a webcam
          </p>
        </div>
      `;
    });
}

registerToggle.addEventListener("click", async () => {
  await inlineScanner.stop();
});

function hideModal() {
  registerModal.classList.remove("show");
  allowScannerInRegisterModal = false;
  startInlineScanner();
  attachScanner();
}

closeModalBtn.addEventListener("click", hideModal);
modalOverlay.addEventListener("click", hideModal);

// Restart inline scanner
setTimeout(() => {
  startInlineScanner();
  3;
}, 500);

function attachScanner(register = false) {
  onScan.attachTo(document, {
    suffixKeyCodes: [13], // Enter
    reactToPaste: true,
    onScan: function (scannedCode) {
      if (register) {
        rfidModal.classList.remove("show");
        checkRFID(scannedCode);
        setTimeout(() => {
          detachScanner();
          allowScannerInRegisterModal = false;
        }, 100);
      } else {
        createLogs(scannedCode);
      }
    },
  });
}

function detachScanner() {
  onScan.detachFrom(document);
}

// Watch the modal's class changes
const observer = new MutationObserver(() => {
  if (
    registerModal.classList.contains("show") &&
    !allowScannerInRegisterModal
  ) {
    detachScanner();
  } else {
    attachScanner();
  }
});

observer.observe(registerModal, {
  attributes: true,
  attributeFilter: ["class"],
});

// Initial check on page load
if (!registerModal.classList.contains("show")) {
  attachScanner();
}
