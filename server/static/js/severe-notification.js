(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.createSevereNotifier = api.createSevereNotifier;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function createSevereNotifier({
    element,
    timeoutMs = 8000,
    schedule = setTimeout,
    cancelSchedule = clearTimeout,
  }) {
    const sourceLevels = new Map();
    let dismissTimer = null;

    function dismiss() {
      if (dismissTimer !== null) cancelSchedule(dismissTimer);
      dismissTimer = null;
      element.classList.remove("is-visible");
      element.hidden = true;
    }

    function show() {
      if (dismissTimer !== null) cancelSchedule(dismissTimer);
      element.hidden = false;
      element.classList.remove("is-visible");
      void element.offsetWidth;
      element.classList.add("is-visible");
      dismissTimer = schedule(dismiss, timeoutMs);
    }

    function update(source, level) {
      const previousLevel = sourceLevels.get(source);
      sourceLevels.set(source, level);
      if (level !== "severe" || previousLevel === "severe") return false;
      show();
      return true;
    }

    function reset(source) {
      sourceLevels.delete(source);
    }

    return { update, dismiss, reset };
  }

  return { createSevereNotifier };
});
