const sidebar = document.getElementById("sidebar");
const sidebarDrawerToggle = document.getElementById("sidebar-drawer-toggle");
const mainContent = document.getElementById("main_content");
const htmxErrorToast = document.getElementById("error-alert-toast");
const htmxErrorContent = htmxErrorToast.querySelector(".toast-content");
const htmxSuccessToast = document.getElementById("success-alert-toast");
const htmxSuccessContent = htmxSuccessToast.querySelector(".toast-content");
const htmxSuccessButton = htmxSuccessToast.querySelector(".toast-button");
const htmxInfoToast = document.getElementById("info-alert-toast");
const htmxInfoContent = htmxInfoToast.querySelector(".toast-content");

if (localStorage.getItem("sidebar") === "open") {
  sidebar.dataset.state = "open";
  sidebarDrawerToggle.title = "Shrink sidebar";
  sidebarDrawerToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left-close-icon lucide-panel-left-close"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m16 15-3-3 3-3"/></svg>
    `;
}

sidebarDrawerToggle.addEventListener("click", () => {
  if (sidebar.dataset.state == "open") {
    sidebar.dataset.state = "closed";
    sidebarDrawerToggle.style.rotate = "-360deg";
    sidebarDrawerToggle.title = "Expand sidebar";
    sidebarDrawerToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left-open-icon lucide-panel-left-open"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m14 9 3 3-3 3"/></svg>
    `;
    localStorage.setItem("sidebar", "closed");
  } else if (sidebar.dataset.state == "closed") {
    sidebar.dataset.state = "open";
    sidebarDrawerToggle.style.rotate = "360deg";
    sidebarDrawerToggle.title = "Shrink sidebar";
    sidebarDrawerToggle.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left-close-icon lucide-panel-left-close"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/><path d="m16 15-3-3 3-3"/></svg>
    `;
    localStorage.setItem("sidebar", "open");
  }
});

function displayToast(toast, message = null, buttonUrl = null) {
  if (message) {
    toast.querySelector(".toast-content").innerHTML = message;
  }

  if (buttonUrl) {
    const button = toast.querySelector(".toast-button");
    button?.classList.remove("hidden");
    button?.setAttribute("hx-get", buttonUrl);
    htmx.process(button);
  }
  toast.classList.remove("toast-hidden");
  toast.classList.add("toast-visible");
}

function hideToast(toast, duration = 6000) {
  setTimeout(
    () => {
      toast.classList.remove("toast-visible");
      toast.classList.add("toast-hidden");

      const button = toast.querySelector(".toast-button");
      button?.classList.add("hidden");
      button?.removeAttribute("hx-get");
    },
    Math.min(6000, duration),
  );
}

document.body.addEventListener("form-error", (event) => {
  const { modalId } = event.detail;

  if (!modalId) return;

  const modal = document.getElementById(modalId);
  if (modal) {
    modal.showModal?.() || modal.classList.add("open");
  }
});

document.body.addEventListener("modal-response", (event) => {
  const { modalId } = event.detail;

  if (!modalId) return;

  const modal = document.getElementById(modalId);
  if (modal) {
    modal.showModal?.() || modal.classList.add("open");
  }
});

document.body.addEventListener("form-success", (event) => {
  const { modalId, message, detailsUrl } = event.detail;

  if (!modalId) return;

  displayToast(htmxSuccessToast, message, detailsUrl);
  hideToast(htmxSuccessToast);

  const modal = document.getElementById(modalId);
  if (modal) {
    const form = modal.getElementsByTagName("form");
    form.item(0)?.reset();

    modal.close?.() || modal.classList.add("closed");
  }
});

document.body.addEventListener("update-element-value", (event) => {
  const { elementId, value, message, detailsUrl } = event.detail;
  if (!elementId) return;

  const element = document.getElementById(elementId);
  if (element) {
    if (element instanceof HTMLInputElement && element.type === "checkbox") {
      element.checked = !element.checked;
    } else {
      element.value = value;
    }
  }

  displayToast(htmxInfoToast, message, detailsUrl);
  hideToast(htmxInfoToast);
});

let activeScrollInstance = null;

document.addEventListener("mousemove", function recordMouseMovement(e) {
  if (!activeScrollInstance) return;

  const {
    indicator,
    tableWrapper,
    startX,
    startScroll,
    MAX_DRAG_DISTANCE,
    SENSITIVITY,
    DAMPING_FACTOR,
  } = activeScrollInstance;

  let dx = e.clientX - startX;
  //   dx = Math.max(-MAX_DRAG_DISTANCE, Math.min(dx, MAX_DRAG_DISTANCE));

  const sign = Math.sign(dx);
  const rawMagnitude = Math.abs(dx);

  const dampedMagnitude = Math.pow(rawMagnitude, DAMPING_FACTOR);
  const dampedX = sign * dampedMagnitude;

  tableWrapper.scrollLeft = startScroll - dx * SENSITIVITY;
  indicator.style.transform = `translateX(${dampedX}px)`;
});

document.addEventListener("mouseup", function recordMouseLift() {
  if (!activeScrollInstance) return;

  const { indicator } = activeScrollInstance;

  indicator.style.transition = "transform 0.2s ease-out";
  indicator.style.transform = "translateX(0";

  activeScrollInstance = null;
});

function initScrollIndicatorSync(root) {
  if (root.dataset.initialized) return;
  root.dataset.initialized = "true";

  const indicator = root.querySelector(".scroll-indicator");
  const tableWrapper = root.querySelector(".table-wrapper");

  if (!indicator || !tableWrapper) return;

  indicator.addEventListener("mousedown", function recordDragStart(e) {
    activeScrollInstance = {
      indicator,
      tableWrapper,
      startX: e.clientX,
      startScroll: tableWrapper.scrollLeft,
      MAX_DRAG_DISTANCE: 250,
      SENSITIVITY: 1.5,
      DAMPING_FACTOR: 0.7,
    };

    e.preventDefault();
  });
}

function initAll(root = document) {
  root.querySelectorAll("[data-scroll-sync]").forEach(initScrollIndicatorSync);
}

document.addEventListener("DOMContentLoaded", () => {
  initAll(document);
});

document.body.addEventListener("htmx:load", function (e) {
  initAll(e.target);
});

const htmxProgressIndicator = document.getElementById(
  "htmx-progress-indicator",
);

let noAnimate = null;
document.body.addEventListener("htmx:beforeRequest", (event) => {
  console.log(event);
  htmxProgressIndicator.style.transform = "scaleX(0)";
  noAnimate = event.detail?.requestConfig?.parameters?.["noAnimate"];

  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(0.2)";
  }
});

document.body.addEventListener("htmx:beforeSend", (event) => {
  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(0.5)";
  }
});

document.body.addEventListener("htmx:afterRequest", (event) => {
  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(0.7)";
  }
});

document.body.addEventListener("htmx:sendError", (event) => {
  if (!noAnimate) {
    const color = htmxProgressIndicator.style.backgroundColor;

    htmxProgressIndicator.style.backgroundColor = "#e7000b";
    setTimeout(() => {
      htmxProgressIndicator.style.transform = "scaleX(0.85)";
      htmxProgressIndicator.style.transform = "scaleX(1.0)";
      htmxProgressIndicator.style.transform = "scaleX(0.0)";
      htmxProgressIndicator.style.backgroundColor = color;
    }, 500);
  }

  displayToast(htmxErrorToast);
  hideToast(
    htmxErrorToast,
    (Number(event.detail?.requestConfig?.parameters?.["poll"]) || 6500) - 500,
  );
});

document.body.addEventListener("htmx:beforeSwap", (event) => {
  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(0.85)";
  }
});

document.body.addEventListener("htmx:afterSwap", (event) => {
  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(1)";
  }
});

document.body.addEventListener("htmx:afterSettle", (event) => {
  if (!noAnimate) {
    htmxProgressIndicator.style.transform = "scaleX(0)";
  }

  if (event.target == document.getElementById("main_content")) {
    document.body.querySelector("main").scrollTop = 0;
  }
});

document.body.addEventListener("htmx:historyRestore", () => {
  htmx?.ajax("GET", window.location.pathname + window.location.search, {
    target: "#main_content",
    swap: "innerHTML",
  });
  const params = new URLSearchParams(window.location.search);

  for (const [key, val] of params.entries()) {
    const elt = document.getElementById(key);
    if (elt) {
      if (elt instanceof HTMLInputElement && elt.type == "checkbox") {
        if (val) {
          elt.checked = true;
        } else {
          elt.checked = false;
        }
      } else {
        elt.value = val;
      }
    }
  }
});

document.body.addEventListener("next-htmx-request", (event) => {
  const { nextUrl, nextTarget, nextSwap } = event.detail;

  if (nextUrl) {
    htmx.ajax("GET", nextUrl, {
      target: `#${nextTarget}`,
      swap: nextSwap,
    });
  }
});

document.body.addEventListener("trigger-change", (event) => {
  console.log("trigger change")
  const { id } = event.detail;
  const elt = document.getElementById(id);

  if (elt) {
    elt.dispatchEvent(new Event("change"));
  }
});

