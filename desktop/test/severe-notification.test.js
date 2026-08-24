const assert = require("node:assert/strict");
const test = require("node:test");

const {
  createSevereNotifier,
} = require("../../server/static/js/severe-notification.js");

function makeElement() {
  return {
    hidden: true,
    classList: {
      values: new Set(),
      add(value) {
        this.values.add(value);
      },
      remove(value) {
        this.values.delete(value);
      },
      contains(value) {
        return this.values.has(value);
      },
    },
  };
}

test("continuous severe frames show one notification until recovery", () => {
  const element = makeElement();
  let scheduled = 0;
  const notifier = createSevereNotifier({
    element,
    schedule: () => {
      scheduled += 1;
      return scheduled;
    },
    cancelSchedule: () => {},
  });

  assert.equal(notifier.update("video", "severe"), true);
  assert.equal(notifier.update("video", "severe"), false);
  assert.equal(element.hidden, false);
  assert.equal(scheduled, 1);

  notifier.update("video", "normal");
  assert.equal(notifier.update("video", "severe"), true);
  assert.equal(scheduled, 2);
});

test("notification auto-dismisses without changing source state", () => {
  const element = makeElement();
  let dismiss;
  const notifier = createSevereNotifier({
    element,
    schedule: (callback) => {
      dismiss = callback;
      return 1;
    },
    cancelSchedule: () => {},
  });

  notifier.update("camera", "severe");
  dismiss();

  assert.equal(element.hidden, true);
  assert.equal(notifier.update("camera", "severe"), false);
});

test("manual dismissal hides the notification", () => {
  const element = makeElement();
  const notifier = createSevereNotifier({
    element,
    schedule: () => 1,
    cancelSchedule: () => {},
  });

  notifier.update("images", "severe");
  notifier.dismiss();

  assert.equal(element.hidden, true);
});
