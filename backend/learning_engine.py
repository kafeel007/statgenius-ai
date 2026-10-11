"""Rule-based adaptive engine. No randomness: recommendations derive from stored scores and completed activities.
RULES (documented):
 R1 weak topic   (score < weak):    notes -> worked example -> practice (5 Q) -> follow-up assessment
 R2 moderate     (weak..strong):    practice (5 Q) -> follow-up assessment
 R3 strong       (>= strong):       advanced practice (hard difficulty)
 R4 priority = ascending score; learner's selected goal topics break ties and are promoted by one rank bucket.
 R5 next activity = first incomplete step of the highest-priority topic.
 R6 two or more consecutive improving assessments in a topic -> suggest the next difficulty level."""
from competency import classify

STEPS = {"weak": [("notes", "Read introductory notes", 15), ("example", "Study a worked example", 10),
                  ("practice", "Practice: 5 questions", 15), ("followup", "Follow-up assessment", 10)],
         "moderate": [("practice", "Practice: 5 questions", 15), ("followup", "Follow-up assessment", 10)],
         "strong": [("practice", "Advanced practice (hard)", 15)]}
RANK = {"weak": 0, "moderate": 1, "strong": 2}

def difficulty_for(topic, history):
    """history: list of scores (oldest first) for the topic."""
    if len(history) >= 3 and history[-3] < history[-2] < history[-1]: return "hard"
    if len(history) >= 2 and history[-2] < history[-1] and history[-1] >= 50: return "medium"
    return "easy" if (history and history[-1] < 50) else "medium"

def build_path(scores, completed, th, goals=(), history=None):
    """completed: set of (topic, kind). Returns list of path items + next activity."""
    items = []
    for topic, sc in scores.items():
        lvl = classify(sc, th); bucket = max(0, RANK[lvl] - (1 if topic in goals else 0))
        steps = [dict(kind=k, label=l, minutes=m, done=(topic, k) in completed) for k, l, m in STEPS[lvl]]
        done = sum(s["done"] for s in steps)
        items.append(dict(topic=topic, score=sc, level=lvl, priority={0: "High", 1: "Medium", 2: "Low"}[RANK[lvl]],
                          goal=topic in goals, steps=steps, status="Completed" if done == len(steps) else "In progress" if done else "Not started",
                          est_minutes=sum(s["minutes"] for s in steps if not s["done"]),
                          next_difficulty=difficulty_for(topic, (history or {}).get(topic, [sc])), _b=bucket))
    items.sort(key=lambda i: (i["_b"], i["score"], i["topic"]))
    nxt = None
    for it in items:
        s = next((s for s in it["steps"] if not s["done"]), None)
        if s: nxt = dict(topic=it["topic"], kind=s["kind"], label=s["label"], minutes=s["minutes"], difficulty=it["next_difficulty"],
                        reason=f"{it['topic']} is {it['level']} ({it['score']}%). Rule: {'R1' if it['level']=='weak' else 'R2' if it['level']=='moderate' else 'R3'}."); break
    for it in items: it.pop("_b")
    return dict(path=items, next=nxt)
