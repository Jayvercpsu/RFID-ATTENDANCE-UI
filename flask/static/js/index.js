async function loadLogs() {
  const logsContainer = document.getElementById("logsContainer");

  const res = await fetch("/api/logs");
  console.log(res);
  if (!res.ok) {
    logsContainer.innerHTML = "<p style='text-align:center;'>Empty logs for today</p>";
    return;
  }

  const logs = await res.json();

  // Sort logs descending by timestamp to get the latest entry
  logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
  const latestLog = logs[0];

  // Update student section with latest log
  if (latestLog) {
    document.querySelector(".student-photo").src =
      latestLog.avatar || profileIconUrl;

    document.querySelector("#studentName").textContent =
      latestLog.first_name + " " + latestLog.last_name;
    document.querySelector("#studentGender").textContent =
      latestLog.gender?.charAt(0).toUpperCase() + latestLog.gender?.slice(1) ||
      "N/A";
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

document.addEventListener("DOMContentLoaded", () => {
  const codeTypeRadios = document.querySelectorAll('input[name="codeType"]');
  const scannerTypeRadios = document.querySelectorAll(
    'input[name="scannerType"]'
  );
  const scannerOptions = document.getElementById("scannerOptions");
  const manualCodeInput = document.getElementById("manualCodeInput");
  const scanBtn = document.getElementById("scanBtn");
  const qrModal = document.getElementById("qrModal");
  const readerElement = document.getElementById("reader");
  const inlineQrWrapper = document.getElementById("inlineQrScanner");

  let scanner;
  let inlineScanner;
  let lastScannedCode = null;
  let lastScannedTime = 0;
  let scanningLocked = false;
  let capturedPhotoBlob = null;
  let inlineScannerRunning = false;

  function updateUI() {
    const selectedCodeType = document.querySelector(
      'input[name="codeType"]:checked'
    ).value;

    if (selectedCodeType === "input") {
      scannerOptions.style.display = "none";
      manualCodeInput.style.display = "block";
    } else {
      scannerOptions.style.display = "flex";
      manualCodeInput.style.display = "none";
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
      toastr.info("RFID scanning is not implemented yet.");
      return;
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

  document
    .getElementById("closeQrModal")
    .addEventListener("click", async () => {
      qrModal.classList.remove("show");
      if (scanner) {
        await scanner.stop();
        readerElement.innerHTML = "";
      }
    });

  updateUI(); // Initialize UI on page load

  const registerForm = document.getElementById("registerForm");
  registerForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    const codeType = document.querySelector(
      'input[name="codeType"]:checked'
    ).value;
    const rfidCode =
      codeType === "input"
        ? manualCodeInput.value
        : document.getElementById("qrCodeValue").value;

    if (!rfidCode) {
      toastr.error("Please enter or scan a code.");
      return;
    }

    const selectedScannerType = document.querySelector(
      'input[name="scannerType"]:checked'
    ).value;
    if (codeType != "input" && selectedScannerType === "rfid") {
      toastr.info("RFID scanning is not implemented yet.");
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
        toastr.success(result.message);
        setTimeout(() => {
          registerForm.reset();
          qrModal.classList.remove("show");
          document.getElementById("reader").innerHTML = "";
          document.getElementById("registerModal").classList.remove("show");
          startInlineScanner();
        }, 2000);
      } else {
        toastr.error(result.error || "Registration failed.");
      }
    } catch (err) {
      toastr.error("Something went wrong.");
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
        toastr.success("Photo captured!");
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
      (decodedText) => {
        document.getElementById("qrCodeValue").value = decodedText;
        scanner.stop().then(() => {
          qrModal.classList.remove("show");
          toastr.success("Successfully scanned code.");
          document.getElementById("scanSound").play();
          console.log("Scanned QR Code:", decodedText);
          readerElement.innerHTML = "";
        });
      },
      (err) => {}
    );
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
          const now = Date.now();

          // Prevent any scanning while locked
          if (scanningLocked) return;

          if (decodedText) {
            lastScannedCode = decodedText;
            lastScannedTime = now;
            scanningLocked = true; // 🔒 lock scanner

            document.getElementById("qrCodeValue").value = decodedText;
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
                  toastr.info(result.error);
                } else {
                  toastr.error("Unidentified code or not registered.");
                }

                document.getElementById("scanSoundError").play();
              } else {
                toastr.success(
                  `Successfully logged ${result.status.toLowerCase()}`
                );
                document.getElementById("scanSound").play();
                await loadLogs();
              }
            } catch (error) {
              console.error("Fetch error:", error);
              toastr.error("API request failed.");
            }

            // Allow rescanning of same code after 5 seconds
            setTimeout(() => {
              scanningLocked = false;
            }, 1000);
          }

          //   else if (now - lastScannedTime >= 2000) {
          //     toastr.info("Already scanned.");
          //     document.getElementById("scanSoundError").play();
          //     lastScannedTime = now; // update timestamp to avoid flooding
          //   }
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
      });
  }

  const registerModal = document.getElementById("registerModal");
  const registerToggle = document.getElementById("registerToggleBtn");
  const closeModalBtn = document.getElementById("closeModal");
  const modalOverlay = registerModal.querySelector(".modal-overlay");

  registerToggle.addEventListener("click", async () => {
    await inlineScanner.stop();
  });

  function hideModal() {
    registerModal.classList.remove("show");
    startInlineScanner();
  }

  closeModalBtn.addEventListener("click", hideModal);
  modalOverlay.addEventListener("click", hideModal);

  // Restart inline scanner
  setTimeout(() => {
    startInlineScanner();
  }, 500);
});
