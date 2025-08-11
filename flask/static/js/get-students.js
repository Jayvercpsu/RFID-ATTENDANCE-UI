let deleteRFID = null;
let studentsTable = null;

$(document).ready(function () {
  fetch("/api/students")
    .then((response) => response.json())
    .then((data) => {
      const tbody = document.getElementById("studentsBody");
      tbody.innerHTML = "";

      data.forEach((student) => {
        const row = document.createElement("tr");
        row.setAttribute("data-rfid", student.rfid_code);

        row.innerHTML = `
  <td class="col-avatar"> 
    <img src="${
      student.avatar || profileIconUrl
    }" onerror="this.src='${profileIconUrl}'" alt="Student Photo" width="50" style="border-radius: 4px;" />    
  </td>
  <td class="col-id-number">${student.id_number || ""}</td>
  <td class="col-first_name">${student.first_name || ""}</td>
  <td class="col-middle_name">${student.middle_name || ""}</td>
  <td class="col-last_name">${student.last_name || ""}</td>
  <td class="col-age">${student.age || ""}</td>
  <td class="col-gender">${student.gender || ""}</td>
  <td class="col-grade">${student.grade || ""}</td>
  <td class="col-section">${student.strandOrSec || student.section || ""}</td>
  <td class="col-contact">${student.contact || ""}</td>
  <td class="col-address">${student.address || ""}</td>
 
 <td style="position: relative; overflow: visible; text-align: left;">
  <div style="position: relative; display: inline-block;">
    <!-- Three Dots Button -->
    <button class="btn-save" onclick="toggleMenu(this)" style="cursor: pointer; z-index: 2; position: relative;">
      <i class="fas fa-ellipsis-v"></i>
    </button>

    <!-- Dropdown Menu -->
    <div class="dropdown-menu" style="
      display: none;
      opacity: 0;
      transform: translateX(5px);
      transition: opacity 0.2s ease, transform 0.2s ease;
      position: absolute;
      z-index: 3;
      min-width: 50px;
      background: #fff;
      border: 1px solid #ccc;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      padding: 4px 0;
      right: 100%;
      top: 0;
    ">
      <button class="btn-edit" data-rfid="${student.rfid_code}" style="
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        background: none;
        border: none;
        width: 100%;
        text-align: right;
        cursor: pointer;
        font-size: 14px;
      ">
        <span>Edit</span>
        <i class="fas fa-pen"></i>
      </button>
      <button onclick='openDeletePopup("${student.rfid_code}")' style="
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 8px;
        padding: 10px 16px;
        background: none;
        border: none;
        width: 100%;
        text-align: right;
        cursor: pointer;
        font-size: 14px;
      ">
        <span>Delete</span>
        <i class="fas fa-trash" style="color: red;"></i>
      </button>
    </div>
  </div>
</td>
        `;
        tbody.appendChild(row);
      });

      if (studentsTable) {
        studentsTable.clear().destroy();
      }
      studentsTable = $("#studentsTable").DataTable({
        language: {
          searchPlaceholder: "Search students...",
        },
      });
    });

  $("#editForm").submit(function (e) {
    e.preventDefault();

    const updated = {
      rfid: $("#edit_rfid").val(),
      first_name: $("#edit_first_name").val(),
      middle_name: $("#edit_middle_name").val(),
      last_name: $("#edit_last_name").val(),
      age: $("#edit_age").val(),
      gender: $("#edit_gender").val(),
      grade: $("#edit_grade").val(),
      section: $("#edit_section").val(),
      contact: $("#edit_contact").val(),
      address: $("#edit_address").val(),
      guardian: $("#edit_guardian").val(),
    };

    fetch(`/api/students/${updated.rfid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(updated),
    })
      .then((res) => res.json())
      .then(() => {
        const row = $(`tr[data-rfid="${updated.rfid}"]`);
        if (row.length) {
          const updatedStudent = updated;

          // Map column selectors to updated values
          const fieldMap = {
            ".col-first_name": updatedStudent.first_name,
            ".col-middle_name": updatedStudent.middle_name,
            ".col-last_name": updatedStudent.last_name,
            ".col-age": updatedStudent.age,
            ".col-gender": updatedStudent.gender,
            ".col-grade": updatedStudent.grade,
            ".col-section": updatedStudent.section,
            ".col-contact": updatedStudent.contact,
            ".col-address": updatedStudent.address,
            ".col-guardian": updatedStudent.guardian,
          };

          // Update each column using jQuery
          $.each(fieldMap, function (selector, value) {
            row.find(selector).text(value || "");
          });
        }

        closeEditPopup();
        showAlert("Student updated successfully");
      });
  });

  $(document).on("click", ".btn-edit", function () {
    const rfid = $(this).data("rfid");

    fetch("/api/students")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch student list");
        return res.json();
      })
      .then((data) => {
        const student = data.find((s) => s.rfid_code === rfid);
        if (!student) {
          alert("Student not found.");
          return;
        }

        const resolvedRfid = student.rfid_code;
        if (!resolvedRfid) {
          alert("Missing RFID or RFID code. Cannot edit this student.");
          return;
        }

        $("#edit_rfid").val(resolvedRfid);

        $("#edit_first_name").val(student.first_name || "");
        $("#edit_middle_name").val(student.middle_name || "");
        $("#edit_last_name").val(student.last_name || "");
        $("#edit_age").val(student.age || "");
        $("#edit_gender").val(student.gender || "");
        $("#edit_grade").val(student.grade || "");
        $("#edit_section").val(student.strandOrSec || student.section || "");
        $("#edit_contact").val(student.contact || "");
        $("#edit_address").val(student.address || "");
        $("#edit_guardian").val(student.guardian || "");

        $("#editPopup").removeClass("hidden");
      })
      .catch((err) => {
        console.error("Fetch error:", err);
        alert("Failed to load student data.");
      });
  });
});

function toggleMenu(button) {
  const menu = button.parentElement.querySelector(".dropdown-menu");

  document.querySelectorAll(".dropdown-menu").forEach((m) => {
    if (m !== menu) {
      m.style.display = "none";
      m.style.opacity = 0;
      m.style.transform = "translateY(-5px)";
    }
  });

  const isOpen = menu.style.display === "block";

  if (isOpen) {
    menu.style.display = "none";
    menu.style.opacity = 0;
    menu.style.transform = "translateY(-5px)";
  } else {
    menu.style.display = "block";
    setTimeout(() => {
      menu.style.opacity = 1;
      menu.style.transform = "translateY(0)";
    }, 10);
  }
}

document.addEventListener("click", (e) => {
  const isMenu = e.target.closest(".dropdown-menu");
  const isButton = e.target.closest(".btn-save");

  if (!isMenu && !isButton) {
    document.querySelectorAll(".dropdown-menu").forEach((menu) => {
      menu.style.display = "none";
      menu.style.opacity = 0;
      menu.style.transform = "translateY(-5px)";
    });
  }
});

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

function closeEditPopup() {
  $("#editPopup").addClass("hidden");
}

function openDeletePopup(rfid) {
  deleteRFID = rfid;
  $("#deletePopup").removeClass("hidden");
}

function closeDeletePopup() {
  deleteRFID = null;
  $("#deletePopup").addClass("hidden");
}

function confirmDelete() {
  if (!deleteRFID) return;

  fetch(`/api/students/${deleteRFID}`, { method: "DELETE" })
    .then((res) => res.json())
    .then((data) => {
      if (data.message) {
        $(`tr[data-rfid="${deleteRFID}"]`).remove();
        showAlert("Student deleted successfully.");
        closeDeletePopup();
      } else {
        showAlert(data.error || "Delete failed.", "#f44336");
      }
    })
    .catch((err) => {
      showAlert("Error deleting student: " + err.message, "#f44336");
      closeDeletePopup();
    });
}

document.addEventListener("click", function (e) {
  const isMenu = e.target.closest(".dropdown-menu");
  const isButton = e.target.closest('button[onclick^="toggleMenu"]');

  if (!isMenu && !isButton) {
    document.querySelectorAll(".dropdown-menu").forEach((el) => {
      el.style.display = "none";
      el.style.opacity = 0;
      el.style.transform = "translateY(-5px)";
    });
  }
});
