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
  // B2B page: the brand machines take turns on the counter while the scene is on screen.
  var machines = document.querySelectorAll(".scene-machine");
  if (machines.length < 2 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var scene = document.querySelector(".scene");
  var tag = document.querySelector(".scene-machine-tag");
  var index = 0;
  window.setInterval(function () {
    var box = scene.getBoundingClientRect();
    if (document.hidden || box.bottom < 0 || box.top > window.innerHeight) return;
    machines[index].classList.remove("is-current");
    index = (index + 1) % machines.length;
    machines[index].classList.add("is-current");
    if (tag) tag.textContent = machines[index].dataset.name;
  }, 3200);
})();

(function () {
  // B2B page: each chapter scrolled into view adds its pieces to the counter scene.
  var story = document.querySelector(".story");
  if (!story) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  var parts = story.querySelectorAll(".scene [data-step]");
  var rail = story.querySelectorAll(".story-rail a");
  var chapters = story.querySelectorAll(".chapter");

  function show(step) {
    parts.forEach(function (part) { part.classList.toggle("on", Number(part.dataset.step) <= step); });
    rail.forEach(function (link) {
      var s = Number(link.dataset.step);
      link.classList.toggle("is-active", s === step);
      link.classList.toggle("is-done", s < step);
    });
    chapters.forEach(function (chapter) { chapter.classList.toggle("is-active", Number(chapter.dataset.step) === step); });
  }

  // The active chapter is the last one whose top has passed the middle of the screen.
  var current = -1;
  function update() {
    var line = window.innerHeight * 0.55;
    var step = 0;
    chapters.forEach(function (chapter) {
      if (chapter.getBoundingClientRect().top <= line) step = Number(chapter.dataset.step);
    });
    if (step !== current) {
      current = step;
      show(step);
    }
  }

  story.classList.add("story-live");
  update();
  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
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
