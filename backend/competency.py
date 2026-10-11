"""Competency classification, gap detection, confidence insights. Pure functions, no AI."""
DEFAULT_THRESHOLDS = {"weak": 50.0, "strong": 75.0}

def check_thresholds(th):
    w, s = float(th.get("weak", 50)), float(th.get("strong", 75))
    if not (0 < w < s <= 100): raise ValueError("Thresholds must satisfy 0 < weak < strong <= 100")
    return {"weak": w, "strong": s}

def classify(score, th=DEFAULT_THRESHOLDS):
    return "weak" if score < th["weak"] else ("strong" if score >= th["strong"] else "moderate")

def overall(scores):
    return round(sum(scores.values()) / len(scores), 1) if scores else 0.0

def gap_report(scores, th=DEFAULT_THRESHOLDS):
    items = [dict(topic=t, score=s, level=classify(s, th)) for t, s in scores.items()]
    items.sort(key=lambda x: x["score"])
    return dict(topics=items, priority=[i["topic"] for i in items if i["level"] == "weak"],
                strong=[i["topic"] for i in items if i["level"] == "strong"],
                note="Scores come from quiz accuracy only; they are indicators, not a measure of professional competency.")

def compare(prev, cur):
    return [dict(topic=t, previous=prev.get(t), current=s,
                 delta=None if prev.get(t) is None else round(s - prev[t], 1)) for t, s in cur.items()]

def blend(old, quiz_pct, weight=0.5):
    """Update a competency score after practice: weighted blend of old score and new accuracy."""
    return round(quiz_pct if old is None else (1 - weight) * old + weight * quiz_pct, 1)

def confidence_insights(results):
    """results: graded rows with confidence in {low, medium, high, None}. Supplementary signal only."""
    out, by_topic = [], {}
    for r in results:
        c = r.get("confidence")
        if c == "low" and r["is_correct"]:
            out.append(dict(topic=r["topic"], type="reinforce", question_id=r["question_id"],
                            message="Correct but low confidence: reinforce this concept with a worked example."))
        elif c == "high" and not r["is_correct"]:
            out.append(dict(topic=r["topic"], type="review", question_id=r["question_id"],
                            message="Incorrect with high confidence: review the underlying concept - a possible misconception."))
        if c == "high" and r["is_correct"]:
            by_topic[r["topic"]] = by_topic.get(r["topic"], 0) + 1
    for t, n in by_topic.items():
        if n >= 2: out.append(dict(topic=t, type="advance", message="Repeated confident correct answers: try harder questions."))
    return out
