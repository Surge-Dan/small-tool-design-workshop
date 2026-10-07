/* Evaluate this function in the actual prototype page; it does not mutate DOM. */
(options = {}) => {
  const selector = options.container;
  const maxWidth = options.maxWidth ?? 390;
  if (typeof selector !== "string" || !selector || !Number.isFinite(maxWidth) || maxWidth <= 0) {
    throw new Error("Provide container selector and positive maxWidth in CSS pixels");
  }
  const root = document.querySelector(selector);
  if (!root) return { checked: false, issue: "container_missing", selector };
  const rect = root.getBoundingClientRect();
  const rootStyle = getComputedStyle(root);
  if (rect.width <= 0 || rect.height <= 0 || rootStyle.display === "none" ||
      rootStyle.visibility === "hidden" || Number(rootStyle.opacity) === 0) {
    return { checked: false, issue: "container_not_visible", selector };
  }
  const viewportWidth = document.documentElement.clientWidth;
  const viewportHeight = window.innerHeight;
  const visible = element => {
    const style = getComputedStyle(element);
    const box = element.getBoundingClientRect();
    return style.display !== "none" && style.visibility !== "hidden" &&
      Number(style.opacity) !== 0 && box.width > 0 && box.height > 0;
  };
  const elements = [...root.querySelectorAll("*")].filter(visible);
  const describe = element => {
    const box = element.getBoundingClientRect();
    return { tag: element.tagName.toLowerCase(), id: element.id,
      text: (element.getAttribute("aria-label") || element.textContent || "").trim().slice(0, 60),
      left: box.left, right: box.right, top: box.top, bottom: box.bottom };
  };
  const outside = elements.filter(element => {
    const box = element.getBoundingClientRect();
    return box.left < rect.left - 1 || box.right > rect.right + 1;
  });
  const fixedOutside = [...document.querySelectorAll("*")].filter(visible).filter(element => {
    if (getComputedStyle(element).position !== "fixed") return false;
    const box = element.getBoundingClientRect();
    return box.left < rect.left - 1 || box.right > rect.right + 1 ||
      box.top < 0 || box.bottom > viewportHeight + 1;
  });
  const issues = [];
  if (rect.width > Math.min(viewportWidth, maxWidth) + 1) issues.push("container_too_wide");
  if (viewportWidth > maxWidth + 2 && Math.abs(rect.left + rect.width / 2 - viewportWidth / 2) > 2) {
    issues.push("container_not_centered");
  }
  if (document.documentElement.scrollWidth > viewportWidth + 1) issues.push("page_horizontal_overflow");
  if (outside.length) issues.push("elements_outside_container");
  if (fixedOutside.length) issues.push("fixed_elements_outside_bounds");
  return { checked: true, selector, maxWidth, viewport: { width: viewportWidth, height: viewportHeight },
    container: { left: rect.left, right: rect.right, width: rect.width },
    issues, outsideCount: outside.length, outside: outside.slice(0, 20).map(describe),
    fixedOutsideCount: fixedOutside.length, fixedOutside: fixedOutside.slice(0, 20).map(describe),
    fontsStatus: document.fonts?.status ?? "unavailable",
    declaredFontFamilies: [...new Set(elements.map(element => getComputedStyle(element).fontFamily))],
    limitation: "Geometry candidates only: inspect intentional scrolling, transforms and clipping. Font declarations/status do not prove actual glyph use; no aesthetic, motion, offline or device verification." };
}
