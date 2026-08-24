from server.domain.fatigue import FatigueClassifier, Observation


def test_sustained_eye_closure_escalates_from_mild_to_severe():
    classifier = FatigueClassifier(window_seconds=60)

    assert classifier.update(Observation(eyes_closed=True), 0).level == "normal"
    assert classifier.update(Observation(eyes_closed=True), 2.1).level == "mild"
    assert classifier.update(Observation(eyes_closed=True), 4.1).level == "severe"


def test_repeated_yawns_escalate_inside_rolling_window():
    classifier = FatigueClassifier(window_seconds=60)

    classifier.update(Observation(yawning=True), 0)
    classifier.update(Observation(yawning=False), 1)
    classifier.update(Observation(yawning=True), 10)
    classifier.update(Observation(yawning=False), 11)
    mild = classifier.update(Observation(yawning=True), 20)
    classifier.update(Observation(yawning=False), 21)
    severe = classifier.update(Observation(yawning=True), 30)

    assert mild.level == "mild"
    assert severe.level == "severe"
    assert severe.counts["yawn"] == 4


def test_old_events_expire_from_window():
    classifier = FatigueClassifier(window_seconds=10)

    classifier.update(Observation(head_down=True), 0)
    classifier.update(Observation(head_down=False), 1)
    snapshot = classifier.update(Observation(), 11)

    assert snapshot.level == "normal"
    assert snapshot.counts["head_down"] == 0


def test_level_labels_are_stable_for_the_ui():
    classifier = FatigueClassifier()
    assert classifier.labels == {
        "normal": "正常",
        "mild": "轻度疲劳",
        "moderate": "中度疲劳",
        "severe": "重度疲劳",
    }
