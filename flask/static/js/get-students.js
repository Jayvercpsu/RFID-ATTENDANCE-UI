let deleteRFID = null;
let studentsTable = null; // Store the DataTable instance

$(document).ready(function () {
  fetch('/api/students')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('studentsBody');
      tbody.innerHTML = '';

      data.forEach(student => {
        const row = document.createElement('tr');
        row.setAttribute('data-rfid', student.rfid || student.rfid_code);

        row.innerHTML = `
  <td class="col-first_name">${student.first_name || ''}</td>
  <td class="col-middle_name">${student.middle_name || ''}</td>
  <td class="col-last_name">${student.last_name || ''}</td>
  <td class="col-age">${student.age || ''}</td>
  <td class="col-gender">${student.gender || ''}</td>
  <td class="col-grade">${student.grade || ''}</td>
  <td class="col-section">${student.strandOrSec || student.section || ''}</td>
  <td class="col-contact">${student.contact || ''}</td>
  <td class="col-address">${student.address || ''}</td>
  <td class="col-guardian">${student.guardian || ''}</td>
  <td class="col-rfid">${student.rfid || student.rfid_code || ''}</td>
  <td class="col-avatar">
    ${student.avatar
            ? `<img src="${student.avatar}" alt="Student Photo" width="50" style="border-radius: 4px;" />`
            : 'N/A'}
  </td>
 <td style="position: relative;">
  <div style="position: relative; display: inline-block;">
    <!-- Three Dots Button -->
    <button onclick="toggleMenu(this)" style="
      background: none; 
      border: none; 
      font-size: 20px; 
      cursor: pointer;
    ">
      <i class="fas fa-ellipsis-v"></i>
    </button>

    <!-- Dropdown Menu -->
    <div class="dropdown-menu" style="
      display: none;
      opacity: 0;
      transform: translateY(-5px);
      transition: opacity 0.2s ease, transform 0.2s ease;
      position: absolute;
      top: -5px;
      right: 28px;
      background: #fff;
      border: 1px solid #ccc;
      border-radius: 6px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.15);
      z-index: 1000;
      min-width: 140px;
      padding: 4px 0;
    ">
      <button onclick='openEditPopup(${JSON.stringify(student)})' style="
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
      <button onclick='openDeletePopup("${student.rfid || student.rfid_code}")' style="
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
        <i class="fas fa-trash"></i>
      </button>
    </div>
  </div>
</td>
  `;
        tbody.appendChild(row);
      });



      if (studentsTable) {
        studentsTable.clear().destroy(); // Reset if already initialized
      }
      studentsTable = $('#studentsTable').DataTable();

    });

  // Submit edited data
  $('#editForm').submit(function (e) {
    e.preventDefault();

    const updated = {
      rfid: $('#edit_rfid').val(),
      first_name: $('#edit_first_name').val(),
      middle_name: $('#edit_middle_name').val(),
      last_name: $('#edit_last_name').val(),
      age: $('#edit_age').val(),
      gender: $('#edit_gender').val(),
      grade: $('#edit_grade').val(),
      section: $('#edit_section').val(),
      contact: $('#edit_contact').val(),
      address: $('#edit_address').val(),
      guardian: $('#edit_guardian').val()
    };

    fetch(`/api/student/${updated.rfid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    })
      .then(res => res.json())
      .then(() => {
        const row = $(`tr[data-rfid="${updated.rfid}"]`);
        if (row.length) {
          const cells = row[0].children;

          cells[0].textContent = updated.first_name;
          cells[2].textContent = updated.last_name;
          cells[3].textContent = updated.age;
          cells[4].textContent = updated.gender;
          cells[5].textContent = updated.grade;
          cells[6].textContent = updated.section;
          cells[7].textContent = updated.contact;
          cells[8].textContent = updated.address;
          cells[9].textContent = updated.guardian;

          const editBtn = $(cells[12]).find('button')[0];
          const updatedData = {
            ...updated,
            middle_name: updated.middle_name,
            avatar: $(cells[11]).find('img').attr('src') || ''
          };
          editBtn.setAttribute('onclick', `openEditPopup(${JSON.stringify(updatedData)})`);
        }

        closeEditPopup();
      });
  });

});

function toggleMenu(button) {
  const menu = button.nextElementSibling;
  const isVisible = menu.style.display === 'block';

  // Close any other open menus
  document.querySelectorAll('.dropdown-menu').forEach(el => {
    el.style.display = 'none';
    el.style.opacity = 0;
    el.style.transform = 'translateY(-5px)';
  });

  if (!isVisible) {
    menu.style.display = 'block';
    requestAnimationFrame(() => {
      menu.style.opacity = 1;
      menu.style.transform = 'translateY(0)';
    });
  }
}
// Optional: Close dropdown when clicking outside
document.addEventListener('click', function (e) {
  if (!e.target.closest('td')) {
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
      menu.style.display = 'none';
      menu.style.opacity = 0;
      menu.style.transform = 'translateY(-5px)';
    });
  }
});

document.getElementById('editForm').addEventListener('submit', async function (e) {
  e.preventDefault();

  const rfid = document.getElementById('edit_rfid').value;
  const updatedStudent = {
    first_name: document.getElementById('edit_first_name').value,
    middle_name: document.getElementById('edit_middle_name').value,
    last_name: document.getElementById('edit_last_name').value,
    age: document.getElementById('edit_age').value,
    gender: document.getElementById('edit_gender').value,
    grade: document.getElementById('edit_grade').value,
    section: document.getElementById('edit_section').value,
    contact: document.getElementById('edit_contact').value,
    address: document.getElementById('edit_address').value,
    guardian: document.getElementById('edit_guardian').value
  };

  try {
    const response = await fetch(`/api/students/${rfid}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updatedStudent)
    });

    const result = await response.json();

    if (response.ok) {
      showAlert('Student updated successfully.');
      closeEditPopup();

      // Find the updated row
      const row = document.querySelector(`tr[data-rfid="${rfid}"]`);
      if (row) {
        // Update each cell (make sure your HTML <td>s have matching classes)
        row.querySelector('.col-first_name').textContent = updatedStudent.first_name;
        row.querySelector('.col-middle_name').textContent = updatedStudent.middle_name;
        row.querySelector('.col-last_name').textContent = updatedStudent.last_name;
        row.querySelector('.col-age').textContent = updatedStudent.age;
        row.querySelector('.col-gender').textContent = updatedStudent.gender;
        row.querySelector('.col-grade').textContent = updatedStudent.grade;
        row.querySelector('.col-section').textContent = updatedStudent.section;
        row.querySelector('.col-contact').textContent = updatedStudent.contact;
        row.querySelector('.col-address').textContent = updatedStudent.address;
        row.querySelector('.col-guardian').textContent = updatedStudent.guardian;
      }
    } else {
      showAlert(result.error || 'Update failed.', '#f44336');
    }
  } catch (error) {
    showAlert('Error updating student: ' + error.message, '#f44336');
  }
});

function showAlert(message, color = '#4CAF50') {
  const alertBox = document.getElementById('alertBox');
  const alertMessage = document.getElementById('alertMessage');
  const progressBar = document.getElementById('alertProgress');

  alertMessage.textContent = message;
  alertBox.style.backgroundColor = color;
  alertBox.style.right = '20px';
  alertBox.style.opacity = '1';

  // Reset progress
  progressBar.style.transition = 'none';
  progressBar.style.width = '0%';

  // Trigger progress animation after short delay
  setTimeout(() => {
    progressBar.style.transition = 'width 4s linear';
    progressBar.style.width = '100%';
  }, 50);

  // Hide after 4 seconds
  setTimeout(() => {
    alertBox.style.opacity = '0';
    alertBox.style.right = '-400px';
  }, 4000);
}

function openEditPopup(student) {
  // Always fetch the latest data from the server
  fetch('/api/students')
    .then(res => res.json())
    .then(data => {
      // Find the most up-to-date student by RFID or RFID code
      const freshStudent = data.find(s => s.rfid === student.rfid || s.rfid_code === student.rfid);

      if (!freshStudent) {
        alert("Student not found in latest records.");
        return;
      }

      // Populate modal form fields
      $('#edit_rfid').val(freshStudent.rfid);
      $('#edit_first_name').val(freshStudent.first_name);
      $('#edit_middle_name').val(freshStudent.middle_name || '');
      $('#edit_last_name').val(freshStudent.last_name);
      $('#edit_age').val(freshStudent.age);
      $('#edit_gender').val(freshStudent.gender);
      $('#edit_grade').val(freshStudent.grade);
      $('#edit_section').val(freshStudent.strandOrSec || freshStudent.section || '');
      $('#edit_contact').val(freshStudent.contact);
      $('#edit_address').val(freshStudent.address);
      $('#edit_guardian').val(freshStudent.guardian);

      // Show modal
      $('#editPopup').removeClass('hidden');
    })
    .catch(err => {
      console.error("Failed to fetch student data:", err);
      alert("Error fetching student data. See console for details.");
    });
}

function closeEditPopup() {
  $('#editPopup').addClass('hidden');
}

function openDeletePopup(rfid) {
  deleteRFID = rfid;
  $('#deletePopup').removeClass('hidden');
}

function closeDeletePopup() {
  deleteRFID = null;
  $('#deletePopup').addClass('hidden');
}

function confirmDelete() {
  if (!deleteRFID) return;

  fetch(`/api/student/${deleteRFID}`, { method: 'DELETE' })
    .then(res => res.json())
    .then(() => {
      $(`tr[data-rfid="${deleteRFID}"]`).remove(); // Remove from table
      closeDeletePopup();
    });
}
