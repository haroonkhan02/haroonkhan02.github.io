// Progressive enhancement only: the page is complete without this file.
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;
const saveData = navigator.connection && navigator.connection.saveData;

// Fade cards in as they reach the viewport.
const reveals = document.querySelectorAll(".reveal");
if (calm || !("IntersectionObserver" in window)) {
  reveals.forEach((el) => el.classList.add("in"));
} else {
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        observer.unobserve(entry.target);
      }
    }
  }, { rootMargin: "0px 0px -8% 0px" });
  reveals.forEach((el) => observer.observe(el));
}

// Load a card's clip the first time a mouse user hovers it. Touch devices keep the poster.
if (!calm && !saveData && matchMedia("(hover: hover)").matches) {
  for (const media of document.querySelectorAll("[data-video]")) {
    const card = media.closest(".card");
    let video;
    card.addEventListener("pointerenter", () => {
      if (!video) {
        video = document.createElement("video");
        video.src = media.dataset.video;
        video.muted = true;
        video.loop = true;
        video.playsInline = true;
        video.setAttribute("aria-hidden", "true");
        video.addEventListener("playing", () => media.classList.add("playing"));
        media.append(video);
      }
      video.play().catch(() => {});
    });
    card.addEventListener("pointerleave", () => {
      if (video) {
        video.pause();
        media.classList.remove("playing");
      }
    });
  }
}

// On a project page, play the clip once the figure is on screen, unless motion is reduced.
const figure = document.querySelector("[data-autoplay]");
if (figure && !calm && !saveData && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    if (!entries[0].isIntersecting) return;
    observer.disconnect();
    const video = document.createElement("video");
    video.src = figure.dataset.autoplay;
    video.muted = true;
    video.loop = true;
    video.playsInline = true;
    video.setAttribute("aria-hidden", "true");
    video.addEventListener("playing", () => figure.classList.add("playing"));
    figure.append(video);
    video.play().catch(() => {});
  });
  observer.observe(figure);
}
