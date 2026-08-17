document.addEventListener("DOMContentLoaded", function () {
  var toggle = document.querySelector(".mobile-toggle");
  var sidebar = document.querySelector(".sidebar");

  if (toggle && sidebar) {
    toggle.addEventListener("click", function () {
      sidebar.classList.toggle("open");
    });

    document.addEventListener("click", function (event) {
      if (
        sidebar.classList.contains("open") &&
        !sidebar.contains(event.target) &&
        !toggle.contains(event.target)
      ) {
        sidebar.classList.remove("open");
      }
    });
  }

  // Confirm before destructive delete form submissions
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      var message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        event.preventDefault();
      }
    });
  });

  // Auto-hide flash messages after a few seconds
  document.querySelectorAll(".messages li").forEach(function (item, index) {
    setTimeout(function () {
      item.style.transition = "opacity 0.4s ease";
      item.style.opacity = "0";
      setTimeout(function () {
        item.style.display = "none";
      }, 400);
    }, 5000 + index * 300);
  });
});
