$(document).ready(function () {
  fetch('/api/logs')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('logsBody');
      tbody.innerHTML = '';

      data.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${log.status || ''}</td>
          <td>${new Date(log.timestamp).toLocaleString()}</td>
          <td>${log.first_name || ''}</td>
          <td>${log.middle_name || ''}</td>
          <td>${log.last_name || ''}</td>
          <td>${log.grade || ''}</td>
          <td>${log.strandOrSec || ''}</td>
          <td>${log.gender || ''}</td>
          <td>${log.contact || ''}</td>
          <td>${log.guardian || ''}</td>
          <td>
            ${log.avatar
              ? `<img src="${log.avatar}" alt="Photo" width="50" />`
              : 'N/A'}
          </td>
        `;
        tbody.appendChild(row);
      });

      $('#logsTable').DataTable();
    })
    .catch(err => {
      console.error('Failed to fetch attendance logs:', err);
    });
});
