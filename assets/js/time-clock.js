function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString("en-US", {
        hour12: true,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
    document.getElementById("live-clock").textContent = timeStr;
}

setInterval(updateClock, 1000);
updateClock();

window.addEventListener("load", () => {
    document.querySelector(".dashboard").classList.add("loading");
});

const logEntries = document.querySelectorAll(".log-entry");
logEntries.forEach((entry, index) => {
    entry.style.animationDelay = `${index * 0.1}s`;
}); 