$(document).ready(function () {
  fetch('/api/logs')
    .then(response => response.json())
    .then(data => {
      const tbody = document.getElementById('logsBody');
      tbody.innerHTML = '';

      data.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>
            <img src="${log.avatar || profileIconUrl}" onerror="this.src='${profileIconUrl}'" alt="Photo" width="50" />
          </td>
          <td>${log.status || ''}</td>
          <td>${log.first_name || ''} ${log.last_name || ''}</td>
          <td>${new Date(log.timestamp).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })}</td>
          <td>${new Date(log.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
          <td>${log.occupation || 'Student'}</td>
          <td>${log.grade || ''}</td>
          <td>${log.strandOrSec || ''}</td>
          <td>${log.contact || ''}</td>
        `;
        tbody.appendChild(row);
      });

      $('#logsTable').DataTable();
    })
    .catch(err => {
      console.error('Failed to fetch attendance logs:', err);
    });
});
