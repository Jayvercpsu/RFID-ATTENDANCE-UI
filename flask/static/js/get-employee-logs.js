$(document).ready(function () {
  // Global variable to store current edit data
  let currentEditData = null;

  // Function to open edit popup with data
  function openEditPopup(logData) {
    currentEditData = logData;

    // Split the timestamp into date and time components
    const dateTimeIn = logData.timeIn
      ? new Date(logData.timeIn.timestamp)
      : null;
    const dateTimeOut = logData.timeOut
      ? new Date(logData.timeOut.timestamp)
      : null;

    // Set form values using jQuery
    $("#edit_log_id").val(logData.logId || "");
    $("#edit_rfid").val(logData.rfid || "");

    // Use timeIn date if available, otherwise use timeOut date
    const dateToUse = dateTimeIn || dateTimeOut;
    if (dateToUse) {
      $("#edit_date").val(dateToUse.toISOString().split("T")[0]);
    }

    if (dateTimeIn) {
      $("#edit_time_in").val(
        `${String(dateTimeIn.getHours()).padStart(2, "0")}:${String(
          dateTimeIn.getMinutes()
        ).padStart(2, "0")}`
      );
    }

    if (dateTimeOut) {
      $("#edit_time_out").val(
        `${String(dateTimeOut.getHours()).padStart(2, "0")}:${String(
          dateTimeOut.getMinutes()
        ).padStart(2, "0")}`
      );
    } else {
      $("#edit_time_out").val("");
    }

    // Show popup using jQuery
    $("#editPopup").removeClass("hidden");
  }

  // Function to close edit popup
  function closeEditPopup() {
    $("#editPopup").addClass("hidden");
    currentEditData = null;
  }

  // Handle form submission
  $(document).on("submit", "#editForm", async function (e) {
    e.preventDefault();

    const date = $("#edit_date").val();
    const timeIn = $("#edit_time_in").val();
    const timeOut = $("#edit_time_out").val();
    const rfid = $("#edit_rfid").val();

    if (!currentEditData) {
      toastr.error("No record selected for editing");
      return;
    }

    try {
      // Prepare the data to send to the API
      const updateData = {
        rfid: rfid,
        date: date,
        time_in: timeIn,
        time_out: timeOut,
        original_time_in: currentEditData.timeIn
          ? currentEditData.timeIn.timestamp
          : null,
        original_time_out: currentEditData.timeOut
          ? currentEditData.timeOut.timestamp
          : null,
      };

      // Send to your API endpoint
      const response = await fetch("/api/update-employee", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updateData),
      });

      const result = await response.json();

      if (response.ok) {
         toastr.success("Attendance record updated successfully");
        closeEditPopup();
        // Refresh the table
        loadAttendanceData();
      } else {
        throw new Error(result.message || "Failed to update record");
      }
    } catch (error) {
      console.error("Error updating record:", error);
       toastr.error("Error updating record: " + error.message);
    }
  });

  function loadAttendanceData() {
    fetch("/api/logs?type=employee")
      .then((response) => response.json())
      .then((data) => {
        // Group logs by student_id and date
        const groupedLogs = groupLogsByStudentAndDate(data);
        const tbody = document.getElementById("logsBody");
        tbody.innerHTML = "";

        // Process each grouped log
        Object.values(groupedLogs).forEach((logGroup) => {
          const row = document.createElement("tr");
          const firstLog = logGroup.logs[0];
          const timeIn = logGroup.timeIn;
          const timeOut = logGroup.timeOut;
          const totalHours = calculateTotalHours(timeIn, timeOut);

          // Format date (e.g., "Aug 03, 2025")
          const date = new Date(firstLog.timestamp);
          const formattedDate = date.toLocaleString("en-US", {
            month: "short",
            day: "2-digit",
            year: "numeric",
          });

          row.innerHTML = `
          <td style="text-align: center; vertical-align: middle;"><img src="${
            firstLog.avatar
          }" alt="Student Photo" width="50" style="border-radius: 4px; display: block;" /></td>
          <td>${firstLog.first_name} ${firstLog.last_name}</td>
          <td>${formattedDate}</td>
          <td>${timeIn ? formatTime(timeIn.timestamp) : "N/A"}</td>
          <td>${timeOut ? formatTime(timeOut.timestamp) : "N/A"}</td>
          <td>${totalHours || "N/A"}</td>
          <td>${getStatus(timeIn, timeOut)}</td>
          <td>
              <button class="btn-save" onclick="openEditPopup(${JSON.stringify({
                logId:
                  firstLog.student_id + "_" + formattedDate.replace(/ /g, "_"),
                rfid: firstLog.rfid,
                timeIn: timeIn,
                timeOut: timeOut,
                firstName: firstLog.first_name,
                lastName: firstLog.last_name,
              }).replace(/"/g, "&quot;")})">
                Edit
              </button>
            </td>
        `;
          tbody.appendChild(row);
        });

        $("#employeeLogsTable").DataTable();
      })
      .catch((err) => {
        console.error("Failed to fetch attendance logs:", err);
      });
  }

  // Helper function to group logs by student and date
  function groupLogsByStudentAndDate(logs) {
    const grouped = {};

    logs.forEach((log) => {
      const date = new Date(log.timestamp);
      const dateKey = date.toISOString().split("T")[0]; // YYYY-MM-DD
      const key = `${log.student_id}_${dateKey}`;

      if (!grouped[key]) {
        grouped[key] = {
          logs: [],
          timeIn: null,
          timeOut: null,
        };
      }

      grouped[key].logs.push(log);

      // Determine if this is IN or OUT
      if (log.status === "IN") {
        if (
          !grouped[key].timeIn ||
          new Date(log.timestamp) < new Date(grouped[key].timeIn.timestamp)
        ) {
          grouped[key].timeIn = log;
        }
      } else if (log.status === "OUT") {
        if (
          !grouped[key].timeOut ||
          new Date(log.timestamp) > new Date(grouped[key].timeOut.timestamp)
        ) {
          grouped[key].timeOut = log;
        }
      }
    });

    return grouped;
  }

  // Format time as "3:23 AM"
  function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }

  // Calculate hours between time in and time out
  // Calculate hours between time in and time out
  function calculateTotalHours(timeIn, timeOut) {
    if (!timeIn || !timeOut) return "N/A";

    const inTime = new Date(timeIn.timestamp);
    const outTime = new Date(timeOut.timestamp);
    const diffMs = outTime - inTime;

    // Convert to hours with 1 decimal place
    const diffHrs = diffMs / (1000 * 60 * 60);

    if (diffHrs < 1) {
      // If less than 1 hour, show minutes
      const diffMins = Math.round(diffMs / (1000 * 60));
      return `${diffMins} mins`;
    } else {
      // If 1 hour or more, show hours with 1 decimal
      const roundedHrs = Math.round(diffHrs * 10) / 10;
      return `${roundedHrs} hrs`;
    }
  }

  // Determine status based on time in/out
  function getStatus(timeIn, timeOut) {
    if (!timeIn) return "Absent";
    if (!timeOut) return "Present (No checkout)";
    return "Present";
  }

  function exportToExcel() {
    // Get the DataTable instance
    const table = $("#employeeLogsTable").DataTable();

    // Get the filtered/sorted data from the table
    const data = table.rows({ search: "applied" }).data().toArray();

    // Prepare Excel data
    const excelData = [
      [
        "Employee Name",
        "Date",
        "Time In",
        "Time Out",
        "Total Hours",
        "Status",
      ], // Headers
    ];

    data.forEach((row) => {
      const fullName = row[1];
      const date = row[2];
      const timeIn = row[3];
      const timeOut = row[4];
      const totalHours = row[5];
      const status = row[6];

      excelData.push([
        fullName,
        date,
        timeIn,
        timeOut,
        totalHours,
        status,
      ]);
    });

    // Create workbook
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.aoa_to_sheet(excelData);

    // Add worksheet to workbook
    XLSX.utils.book_append_sheet(wb, ws, "Attendance");

    // Generate Excel file and trigger download
    const currentDate = new Date().toISOString().split("T")[0];
    XLSX.writeFile(wb, `Employee_Attendance_${currentDate}.xlsx`);
  }

  loadAttendanceData();

  window.openEditPopup = openEditPopup;
  window.closeEditPopup = closeEditPopup;
  window.exportToExcel = exportToExcel;
});
