const test = require('node:test');
const assert = require('node:assert/strict');

const {orderedValues} = require('../../server/static/js/chart-data');


test('orderedValues follows the chart label order instead of JSON key order', () => {
  const alphabeticallySortedRisk = {mild: 2, moderate: 3, normal: 7, severe: 1};
  const alphabeticallySortedEvents = {eye_closed: 4, head_down: 1, yawn: 2};
  const alphabeticallySortedSources = {camera: 0, image: 8, video: 3};

  assert.deepEqual(orderedValues(alphabeticallySortedRisk, ['normal', 'mild', 'moderate', 'severe']), [7, 2, 3, 1]);
  assert.deepEqual(orderedValues(alphabeticallySortedEvents, ['eye_closed', 'yawn', 'head_down']), [4, 2, 1]);
  assert.deepEqual(orderedValues(alphabeticallySortedSources, ['image', 'video', 'camera']), [8, 3, 0]);
});
