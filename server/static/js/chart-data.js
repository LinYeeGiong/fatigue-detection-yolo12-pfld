(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.ChartData = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  function orderedValues(distribution, keys) {
    return keys.map((key) => Number(distribution?.[key] || 0));
  }
  return { orderedValues };
});
