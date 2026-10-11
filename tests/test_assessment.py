import pytest, assessment as A

def test_bank_is_well_formed():
    assert len(A.BANK) == 27 and {q["topic"] for q in A.BANK} == set(A.TOPICS)
    for q in A.BANK:
        assert 0 <= q["correct"] < len(q["options"]) and len(set(q["options"])) == len(q["options"])

def test_public_hides_answers():
    assert "correct" not in A.public(A.BANK[0]) and "explanation" not in A.public(A.BANK[0])

def test_grading_from_actual_responses():
    qs = A.select_questions(3, ["Probability", "Sampling Techniques"])
    ans = [{"question_id": q["id"], "selected": q["correct"] if q["topic"] == "Probability" else (q["correct"] + 1) % 4} for q in qs]
    g = A.grade(ans)
    assert g["topic_scores"]["Probability"]["pct"] == 100.0 and g["topic_scores"]["Sampling Techniques"]["pct"] == 0.0
    assert g["correct"] == 3 and g["total"] == 6 and g["accuracy"] == 50.0

def test_unanswered_counts_wrong():
    assert A.grade([{"question_id": 1, "selected": None}])["correct"] == 0

@pytest.mark.parametrize("bad", [[], [{"question_id": 999, "selected": 0}], [{"question_id": 1, "selected": 9}],
                                  [{"question_id": 1, "selected": 0}, {"question_id": 1, "selected": 1}]])
def test_invalid_input_rejected(bad):
    with pytest.raises(ValueError): A.grade(bad)

def test_known_answers_verified_by_calculation():
    import statistics
    assert round(statistics.variance([2, 4, 6, 8]), 2) == 6.67 and A.BY_ID[3]["options"][A.BY_ID[3]["correct"]] == "6.67"
    assert statistics.median([2, 4, 4, 6, 9]) == 4 and 10 / 5 == 2 and 1000 / 50 == 20 and 0.3 * 0.5 == pytest.approx(0.15)
