document.addEventListener("DOMContentLoaded", () => {
    fetch('/api/dashboard-stats')
        .then(res => res.json())
        .then(data => {
            document.getElementById("presentToday").textContent = data.present_today;
            document.getElementById("totalStudents").textContent = data.total_students;
            document.getElementById("totalEmployees").textContent = data.total_employees;
            document.getElementById("timeInToday").textContent = data.time_in_today;
            document.getElementById("timeOutToday").textContent = data.time_out_today;


            const container = document.getElementById("recentActivityContainer");
            container.innerHTML = `
          <div class="data names">
            <span class="data-title">Name</span>
            ${data.recent_logs.map(log => `<span class="data-list">${log.first_name} ${log.last_name}</span>`).join('')}
          </div>
          <div class="data email">
            <span class="data-title">ID Number</span>
            ${data.recent_logs.map(log => `<span class="data-list">${log.id_number}</span>`).join('')}
          </div>
          <div class="data joined">
            <span class="data-title">Time In</span>
            ${data.recent_logs.map(log => `<span class="data-list">${new Date(log.timestamp).toLocaleTimeString()}</span>`).join('')}
          </div>
          <div class="data type">
            <span class="data-title">RFID Status</span>
            ${data.recent_logs.map(log => `<span class="data-list">${log.status}</span>`).join('')}
          </div>
          <div class="data status">
            <span class="data-title">Remarks</span>
            ${data.recent_logs.map(log => {
                if (log.status === 'IN') return '<span class="data-list">On Time</span>';
                if (log.status === 'OUT') return '<span class="data-list">Left</span>';
                return '<span class="data-list">-</span>';
            }).join('')}
          </div>
        `;
        })
        .catch(err => {
            console.error("Error loading dashboard stats:", err);
        });
});