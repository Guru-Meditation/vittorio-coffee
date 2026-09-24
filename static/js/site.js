(function () {
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!toggle || !nav) return;

  function setOpen(open) {
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    document.body.classList.toggle("nav-open", open);
    if (open) {
      var first = nav.querySelector("a");
      if (first) first.focus();
    }
  }

  toggle.addEventListener("click", function () {
    setOpen(toggle.getAttribute("aria-expanded") !== "true");
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") setOpen(false);
  });

  nav.querySelectorAll("a").forEach(function (link) {
    link.addEventListener("click", function () {
      setOpen(false);
    });
  });
})();

(function () {
  // Touch screens cannot hover: the first tap on a hero pack opens its card, the second follows the link.
  var wraps = document.querySelectorAll(".pack-wrap");
  if (!wraps.length) return;
  var noHover = window.matchMedia("(hover: none)");

  function closeAll(except) {
    wraps.forEach(function (wrap) {
      if (wrap !== except) wrap.classList.remove("is-open");
    });
  }

  wraps.forEach(function (wrap) {
    var link = wrap.querySelector(".pack");
    link.addEventListener("click", function (event) {
      if (!noHover.matches || wrap.classList.contains("is-open")) return;
      event.preventDefault();
      closeAll(wrap);
      wrap.classList.add("is-open");
    });
  });

  document.addEventListener("click", function (event) {
    if (!event.target.closest(".pack-wrap")) closeAll(null);
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeAll(null);
  });
})();

(function () {
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 24);
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
  }

  var items = document.querySelectorAll("[data-reveal]");
  var calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (calm || !("IntersectionObserver" in window)) {
    items.forEach(function (el) { el.classList.add("is-in"); });
    return;
  }
  var observer = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      entry.target.classList.add("is-in");
      observer.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
  items.forEach(function (el) { observer.observe(el); });
})();
