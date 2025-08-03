let deleteRFID = null;
let studentsTable = null; // Store the DataTable instance

$(document).ready(function () {
  fetch('/api/logs')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('studentsBody');
      tbody.innerHTML = '';

            data.forEach(student => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${student.first_name || ''}</td>
                    <td>${student.middle_name || ''}</td>
                    <td>${student.last_name || ''}</td>
                    <td>${student.age || ''}</td>
                    <td>${student.gender || ''}</td>
                    <td>${student.grade || ''}</td>
                    <td>${student.strandOrSec || ''}</td>
                    <td>${student.contact || ''}</td>
                    <td>${student.address || ''}</td>
                    <td>${student.guardian || ''}</td>
                    <td>${student.rfid || student.rfid_code || ''}</td>
                    <td>
                        ${student.avatar
                            ? `<img src="${student.avatar}" alt="Student Photo" width="50" style="border-radius: 4px;" />`
                            : 'N/A'}
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

          // Update the onclick attribute for Edit button with the new data
          const updatedData = JSON.stringify({
            ...updated,
            middle_name: updated.middle_name,
            avatar: $(cells[11]).find('img').attr('src') || '',
          });

          const editBtn = $(cells[12]).find('button')[0];
          editBtn.setAttribute('onclick', `openEditPopup(${updatedData})`);
        }

        closeEditPopup();
      });
  });

});

function openEditPopup(student) {
  $('#edit_rfid').val(student.rfid);
  $('#edit_first_name').val(student.first_name);
  $('#edit_middle_name').val(student.middle_name || '');
  $('#edit_last_name').val(student.last_name);
  $('#edit_age').val(student.age);
  $('#edit_gender').val(student.gender);
  $('#edit_grade').val(student.grade);
  $('#edit_section').val(student.strandOrSec || student.section || '');
  $('#edit_contact').val(student.contact);
  $('#edit_address').val(student.address);
  $('#edit_guardian').val(student.guardian);
  $('#editPopup').removeClass('hidden');
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
