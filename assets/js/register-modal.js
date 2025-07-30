  const modal = document.getElementById("registerModal");
          const openBtn = document.querySelector(".register-btn");
          const closeBtn = document.getElementById("closeModal");

          openBtn.addEventListener("click", () => {
            modal.classList.add("show");
          });

          closeBtn.addEventListener("click", () => {
            modal.classList.remove("show");
          });

          window.addEventListener("click", (e) => {
            if (e.target.classList.contains("modal-overlay")) {
              modal.classList.remove("show");
            }
          });