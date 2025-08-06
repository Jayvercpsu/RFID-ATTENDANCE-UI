$(document).ready(function () {
  $('#logsTable').DataTable({
    serverSide: true,
    processing: true,
    language: {
      searchPlaceholder: "Search for details...",
    },
    ajax: {
      url: '/api/logs',
      type: 'GET'
    },
    columns: [
      { data: 'avatar', render: function (data) {
          return `<img src="${data || profileIconUrl}" onerror="this.src='${profileIconUrl}'" width="50"/>`
        }},
      { data: 'status' },
      { data: null, render: function (data) {
          return `${data.first_name || ''} ${data.last_name || ''}`;
        }},
      { data: 'timestamp', render: function (data) {
          return new Date(data).toLocaleTimeString([], { hour:'numeric', minute:'2-digit' });
        }},
      { data: 'timestamp', render: function (data) {
          return new Date(data).toLocaleDateString('en-US', { month:'short', day:'numeric', year:'numeric' });
        }},
      { data: 'occupation' },
      { data: 'grade' },
      { data: 'strandOrSec' },
      { data: 'contact' }
    ]
  });
});
