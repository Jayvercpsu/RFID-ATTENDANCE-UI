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
                    <td>${student.section || student.strandOrSec || ''}</td>
                    <td>${student.contact || ''}</td>
                    <td>${student.address || ''}</td>
                    <td>${student.guardian || ''}</td>
                    <td>${student.rfid_code || student.rfid || ''}</td>
                    <td>
                    ${student.avatar
                        ? `<img src="${student.avatar}" alt="Student Photo" width="50" />`
                        : 'N/A'}
                    </td>
                `;
                tbody.appendChild(row);
            });


            $('#studentsTable').DataTable();
        })
        .catch(err => {
            console.error('Failed to fetch student data:', err);
        });
});
