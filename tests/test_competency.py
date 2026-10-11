import pytest, competency as C, quiz_generator as QG, stats_lab as S, learning_engine as LE

SC = {"Descriptive Statistics": 85, "Probability": 45, "Sampling Techniques": 30, "Data Visualization": 70}

def test_gap_detection_example_from_brief():
    r = C.gap_report(SC); assert r["priority"][0] == "Sampling Techniques"
    assert {t["topic"]: t["level"] for t in r["topics"]} == {"Descriptive Statistics": "strong", "Probability": "weak", "Sampling Techniques": "weak", "Data Visualization": "moderate"}

def test_configurable_thresholds():
    th = C.check_thresholds({"weak": 40, "strong": 60}); assert C.classify(45, th) == "moderate" and C.classify(45) == "weak"
    with pytest.raises(ValueError): C.check_thresholds({"weak": 80, "strong": 60})

def test_compare_and_blend():
    assert C.compare({"A": 40}, {"A": 55, "B": 10})[0]["delta"] == 15 and C.compare({}, {"B": 10})[0]["delta"] is None
    assert C.blend(30, 90) == 60 and C.blend(None, 80) == 80

def test_confidence_insights():
    rows = [dict(topic="T", question_id=1, is_correct=True, confidence="low"), dict(topic="T", question_id=2, is_correct=False, confidence="high"),
            dict(topic="U", question_id=3, is_correct=True, confidence="high"), dict(topic="U", question_id=4, is_correct=True, confidence="high")]
    assert {i["type"] for i in C.confidence_insights(rows)} == {"reinforce", "review", "advance"}

def test_learning_path_is_rule_based_and_deterministic():
    th = C.DEFAULT_THRESHOLDS; p1 = LE.build_path(SC, set(), th); assert p1 == LE.build_path(SC, set(), th)
    assert p1["next"]["topic"] == "Sampling Techniques" and p1["next"]["kind"] == "notes"
    done = {("Sampling Techniques", k) for k in ("notes", "example", "practice", "followup")}
    assert LE.build_path(SC, done, th)["next"]["topic"] == "Probability"
    assert [i["priority"] for i in p1["path"]][0] == "High"

def test_goal_promotes_topic():
    assert LE.build_path({"A": 60, "B": 55}, set(), C.DEFAULT_THRESHOLDS, goals=["A"])["path"][0]["topic"] == "A"

PAGES = [(1, "A stratified sample is drawn from each group of the population. The median is the middle value of sorted data. "
             "The p-value is the probability of data as extreme as observed if the null hypothesis is true.")]
@pytest.mark.parametrize("fmt", ["mcq", "tf", "short", "numeric", "mixed"])
def test_quiz_generation_and_validation(fmt):
    qs = QG.generate_quiz(PAGES, n=4, fmt=fmt, seed=3); assert len(qs) == 4
    for q in qs: assert QG.validate_question(q)
    pub = QG.public_question(qs[0]); assert "answer" not in pub and "explanation" not in pub

def test_check_answer_and_numeric_tolerance():
    q = QG.generate_quiz([], n=1, fmt="numeric", seed=1)[0]
    assert QG.check_answer(q, q["answer"]) and QG.check_answer(q, str(q["answer"])) and not QG.check_answer(q, q["answer"] + 1) and not QG.check_answer(q, "abc")

def test_stats_lab_known_values():
    d = S.descriptive([2, 4, 6, 8])["result"]; assert d["mean"] == 5 and d["sample_variance"] == pytest.approx(6.6667, abs=1e-3)
    b = S.binomial(10, 0.5, 5)["result"]; assert b["P_equal"] == pytest.approx(0.246094, abs=1e-5)
    reg = S.regression([1, 2, 3, 4], [2, 4, 6, 8])["result"]; assert reg["slope"] == 2 and reg["r"] == 1
    t = S.one_sample_t([5.1, 4.9, 5.6, 5.8, 6.0, 5.2], 5)["result"]; assert t["p_value"] == pytest.approx(0.0575, abs=1e-3)
    assert S.confidence_interval([10, 12, 14, 16, 18])["result"]["t_critical"] == pytest.approx(2.776, abs=1e-3)
    q = S.data_quality(["5", "", "NA", "abc", "300", "5"], 0, 120)["result"]; assert q["missing_count"] == 2 and q["out_of_range_positions"] == [5] and q["repeated_values"] == [5.0]
    with pytest.raises(ValueError): S.descriptive([1])
