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
      $("#edit_time_out").prop("disabled", true);
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
      showAlert("No record selected for editing", "#f44336");
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
        showAlert("Attendance record updated successfully");
        closeEditPopup();
        // Refresh the table
        loadAttendanceData();
      } else {
        throw new Error(result.message || "Failed to update record");
      }
    } catch (error) {
      console.error("Error updating record:", error);
      showAlert("Error updating record: " + error.message, "#f44336");
    }
  });

  function loadAttendanceData() {
    $("#employeeLogsTable").DataTable({
      destroy: true,
      serverSide: true,
      processing: true,
      language: {
        searchPlaceholder: "Search employees...",
      },
      ajax: {
        url: "/api/logs?type=employee&export=true",
        type: "GET",
        dataSrc: function (json) {
          // json.data => raw rows from API
          const grouped = groupLogsByStudentAndDate(json.data);
          // Convert grouped object back into array of "summary rows"
          const summaryRows = Object.values(grouped).map((g) => {
            const first = g.logs[0];
            const timeIn = g.timeIn;
            const timeOut = g.timeOut;
            return {
              avatar: first.avatar,
              first_name: first.first_name,
              last_name: first.last_name,
              timestamp: first.timestamp, // for date/time display
              timeIn: timeIn,
              timeOut: timeOut,
              id_number: first.id_number,
              rfid: first.rfid,
            };
          });
          json.data = summaryRows; // replace raw rows with summary rows
          return json.data;
        },
      },
      columns: [
        {
          data: "avatar",
          render: function (data) {
            return `<img src="${
              data || profileIconUrl
            }" onerror="this.src='${profileIconUrl}'" width="50"/>`;
          },
        },
        {
          data: null,
          render: function (data) {
            return `${data.first_name || ""} ${data.last_name || ""}`;
          },
        },
        {
          data: "timestamp",
          render: function (data) {
            return new Date(data).toLocaleDateString("en-US", {
              month: "short",
              day: "2-digit",
              year: "numeric",
            });
          },
        },
        {
          data: "timeIn",
          render: function (timeIn) {
            return timeIn ? formatTime(timeIn.timestamp) : "N/A";
          },
        },
        {
          data: "timeOut",
          render: function (timeOut) {
            return timeOut ? formatTime(timeOut.timestamp) : "N/A";
          },
        },
        {
          data: null,
          render: function (data) {
            const total =
              calculateTotalHours(data.timeIn, data.timeOut) || "N/A";
            return total;
          },
        },
        {
          data: null,
          render: function (data) {
            return getStatus(data.timeIn, data.timeOut);
          },
        },
        {
          data: null,
          orderable: false,
          render: function (data) {
            const date = new Date(data.timestamp);
            const formattedDate = date
              .toLocaleDateString("en-US", {
                month: "short",
                day: "2-digit",
                year: "numeric",
              })
              .replace(/ /g, "_");
            const obj = {
              logId: data.id_number + "_" + formattedDate,
              rfid: data.rfid,
              timeIn: data.timeIn,
              timeOut: data.timeOut,
              firstName: data.first_name,
              lastName: data.last_name,
            };
            return `<button class="btn-save" onclick="openEditPopup(${JSON.stringify(
              obj
            ).replace(/"/g, "&quot;")})">Edit</button>`;
          },
        },
      ],
    });
  }

  // Helper function to group logs by student and date
  function groupLogsByStudentAndDate(logs) {
    const grouped = {};

    logs.forEach((log) => {
      const date = new Date(log.timestamp);
      const dateKey = date.toISOString().split("T")[0]; // YYYY-MM-DD
      const key = `${log.id_number}_${dateKey}`;

      if (!grouped[key]) {
        9;
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

  async function exportToExcel() {
    try {
      const res = await fetch("/api/logs?type=employee&length=500");
      const raw = await res.json();

      // Group them exactly how your table is displayed
      const grouped = groupLogsByStudentAndDate(raw.data);

      const excelData = [
        [
          "Employee Name",
          "Date",
          "Time In",
          "Time Out",
          "Total Hours",
          "Status",
        ],
      ];

      Object.values(grouped).forEach((g) => {
        const first = g.logs[0];
        const dateObj = new Date(first.timestamp);
        const formattedDate = dateObj.toLocaleDateString("en-US", {
          month: "short",
          day: "2-digit",
          year: "numeric",
        });
        excelData.push([
          `${first.first_name} ${first.last_name}`,
          formattedDate,
          g.timeIn ? formatTime(g.timeIn.timestamp) : "N/A",
          g.timeOut ? formatTime(g.timeOut.timestamp) : "N/A",
          calculateTotalHours(g.timeIn, g.timeOut) || "N/A",
          getStatus(g.timeIn, g.timeOut),
        ]);
      });

      const wb = XLSX.utils.book_new();
      const ws = XLSX.utils.aoa_to_sheet(excelData);
      XLSX.utils.book_append_sheet(wb, ws, "Attendance");

      const currentDate = new Date().toISOString().split("T")[0];
      XLSX.writeFile(wb, `Employee_Attendance_${currentDate}.xlsx`);
      // showAlert("Successfully downloading excel");
    } catch (error) {
      showAlert("Error downloading excel: " + error.message, "#f44336");
    }
  }

  function showAlert(message, color = "#4CAF50") {
    const $alertBox = $("#alertBox");
    const $alertMessage = $("#alertMessage");
    const $progressBar = $("#alertProgress");

    $alertMessage.text(message);
    $alertBox.css({ backgroundColor: color, right: "20px", opacity: 1 });

    $progressBar.css({ transition: "none", width: "0%" });

    setTimeout(() => {
      $progressBar.css({ transition: "width 4s linear", width: "100%" });
    }, 50);

    setTimeout(() => {
      $alertBox.css({ opacity: 0, right: "-400px" });
    }, 4000);
  }

  loadAttendanceData();

  window.openEditPopup = openEditPopup;
  window.closeEditPopup = closeEditPopup;
  window.exportToExcel = exportToExcel;
});
