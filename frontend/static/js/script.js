document.addEventListener("DOMContentLoaded", () => {
  const nav = document.querySelector(".site-nav");
  const toggle = document.querySelector(".nav-toggle");
  const menu = document.querySelector("#nav-menu");

  if (toggle && nav && menu) {
    toggle.addEventListener("click", () => {
      const isOpen = nav.classList.toggle("nav-open");
      toggle.setAttribute("aria-expanded", String(isOpen));
    });

    menu.querySelectorAll("a").forEach((link) => {
      link.addEventListener("click", () => {
        nav.classList.remove("nav-open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  const loginForm = document.querySelector("#loginForm");
  const formError = document.querySelector("#formError");

  if (loginForm) {
    loginForm.addEventListener("submit", (event) => {
      const requiredInputs = loginForm.querySelectorAll("input[required]");
      let hasMissing = false;

      requiredInputs.forEach((input) => {
        if (!input.value.trim()) {
          hasMissing = true;
        }
      });

      if (hasMissing) {
        event.preventDefault();
        if (formError) {
          formError.hidden = false;
        }
      } else if (formError) {
        formError.hidden = true;
      }
    });
  }

  const passwordToggles = document.querySelectorAll(".password-toggle");
  passwordToggles.forEach((toggleButton) => {
    toggleButton.addEventListener("click", () => {
      const targetId = toggleButton.getAttribute("data-target");
      const targetInput = document.getElementById(targetId);

      if (!targetInput) {
        return;
      }

      const isPassword = targetInput.type === "password";
      targetInput.type = isPassword ? "text" : "password";
      toggleButton.textContent = isPassword ? "Hide" : "Show";
    });
  });
});
