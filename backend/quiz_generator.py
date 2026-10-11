"""Quiz + notes generation. Deterministic, document-grounded generator (works offline); if an LLM is available,
ai_service output is used but every question is validated (see validate_question)."""
import re, random, math, statistics
import ai_service
from assessment import BANK, public as _pub

TERMS = {  # statistical vocabulary -> topic (used for grounding and topic detection)
 "mean":"Descriptive Statistics","median":"Descriptive Statistics","mode":"Descriptive Statistics","variance":"Descriptive Statistics",
 "standard deviation":"Descriptive Statistics","range":"Descriptive Statistics","probability":"Probability","independent":"Probability",
 "random variable":"Probability","sample":"Sampling Techniques","population":"Sampling Techniques","stratified":"Sampling Techniques",
 "cluster":"Sampling Techniques","systematic":"Sampling Techniques","sampling frame":"Sampling Techniques","standard error":"Statistical Inference",
 "confidence interval":"Statistical Inference","estimator":"Statistical Inference","null hypothesis":"Hypothesis Testing","p-value":"Hypothesis Testing",
 "significance level":"Hypothesis Testing","type i error":"Hypothesis Testing","correlation":"Regression Analysis","regression":"Regression Analysis",
 "slope":"Regression Analysis","histogram":"Data Visualization","bar chart":"Data Visualization","scatter plot":"Data Visualization",
 "questionnaire":"Survey Methodology","non-response":"Survey Methodology","respondent":"Survey Methodology","missing value":"Data Quality and Validation",
 "outlier":"Data Quality and Validation","validation":"Data Quality and Validation","duplicate":"Data Quality and Validation"}

KB = {  # general-knowledge study material per topic (clearly labelled "general" in the UI)
 "Descriptive Statistics": dict(notes="Descriptive statistics summarise data: centre (mean, median, mode) and spread (range, variance, SD).", formula="Mean = Σx/n;  s² = Σ(x−x̄)²/(n−1);  s = √s²", example="Data 2,4,6,8: mean=5; deviations² = 9,1,1,9; s² = 20/3 = 6.67; s = 2.58.", application="Summarising household income or monthly price indices."),
 "Probability": dict(notes="Probability measures chance on a 0–1 scale. Rules: complement, addition, multiplication.", formula="P(A∪B)=P(A)+P(B)−P(A∩B);  independent: P(A∩B)=P(A)P(B)", example="Two fair coin tosses: P(HH)=0.5×0.5=0.25.", application="Assessing response likelihood or error rates in field data collection."),
 "Sampling Techniques": dict(notes="Sampling selects part of a population to estimate its characteristics. Common designs: SRS, systematic, stratified, cluster.", formula="Sampling interval k = N/n;  SE(x̄)=s/√n", example="N=1000, n=50 → k=20: random start 1–20, then every 20th unit.", application="Designing household surveys across districts (stratify by state, cluster by village)."),
 "Statistical Inference": dict(notes="Inference uses sample data to estimate population values with a measure of uncertainty.", formula="SE = s/√n;  CI = x̄ ± t·SE", example="n=25, s=10 → SE=2; with t≈2.06, margin ≈ 4.1.", application="Reporting a survey estimate with its margin of error."),
 "Hypothesis Testing": dict(notes="A hypothesis test asks whether data are consistent with a null hypothesis, using a p-value.", formula="t = (x̄ − μ0)/(s/√n); reject H0 if p < α", example="x̄=5.43, μ0=5, s=0.43, n=6 → t≈2.46, p≈0.057 → not significant at 5%.", application="Checking whether average wages changed after a policy."),
 "Regression Analysis": dict(notes="Regression models how a response changes with predictors; correlation measures linear association.", formula="b1 = Sxy/Sxx;  b0 = ȳ − b1x̄;  r = Sxy/√(SxxSyy)", example="y=2+3x: x up by 1 → predicted y up by 3.", application="Relating crop yield to rainfall."),
 "Data Visualization": dict(notes="Choose charts to match data: histogram (distribution), line (trend), bar (categories), scatter (relationship).", formula="Histogram bins ≈ √n (rule of thumb)", example="Age of respondents → histogram; monthly CPI → line chart.", application="Dashboards and published statistical releases."),
 "Survey Methodology": dict(notes="Surveys need a good frame, neutral questions and a plan for non-response.", formula="Response rate = completed / eligible × 100", example="800 completed of 1000 eligible → 80%.", application="Designing questionnaires for national sample surveys."),
 "Data Quality and Validation": dict(notes="Quality checks: completeness, range, consistency, uniqueness, timeliness.", formula="Missing % = missing/total × 100", example="Age=250 fails a range check; duplicate IDs fail uniqueness.", application="Editing and validating survey microdata before tabulation."),
}

def _sentences(pages):
    out = []
    for p, text in pages:
        for s in re.split(r"(?<=[.!?])\s+|\n{2,}", re.sub(r"[ \t]+", " ", text.replace("\n", " \n"))):
            s = s.replace("\n", " ").strip()
            if 35 <= len(s) <= 220 and re.search(r"\b(is|are|refers to|measures|means|equals|used)\b", s): out.append((p, s))
    return out

def _term_in(s):
    low = s.lower()
    return [t for t in sorted(TERMS, key=len, reverse=True) if re.search(r"\b" + re.escape(t) + r"\b", low)]

def detect_topics(pages):
    low = " ".join(t for _, t in pages).lower(); cnt = {}
    for t, topic in TERMS.items():
        n = len(re.findall(r"\b" + re.escape(t) + r"\b", low))
        if n: cnt[topic] = cnt.get(topic, 0) + n
    return [t for t, _ in sorted(cnt.items(), key=lambda x: -x[1])]

def generate_notes(pages):
    sents = _sentences(pages); topics = detect_topics(pages)
    defs = [dict(text=s, page=p, source="document") for p, s in sents if _term_in(s)][:8]
    formulas = [dict(text=l.strip(), page=p, source="document") for p, t in pages for l in t.split("\n")
                if re.search(r"[=∑Σ√]", l) and 5 < len(l.strip()) < 100][:8]
    gen = [dict(topic=t, **KB[t], source="general knowledge (not from your document)") for t in topics[:3] if t in KB]
    summary = [dict(text=s, page=p, source="document") for p, s in sents[:5]]
    ai = ai_service.complete_json("You write simple-English statistics study notes grounded ONLY in the given text.",
        'Return {"summary":[str],"key_takeaways":[str],"revision_notes":[str]} from:\n' + "\n".join(f"[p{p}] {t}" for p, t in pages)[:7000])
    take = (ai or {}).get("key_takeaways") or [d["text"] for d in defs[:4]]
    rev = (ai or {}).get("revision_notes") or [f"{t}: {KB[t]['formula']}" for t in topics[:3] if t in KB]
    if ai and ai.get("summary"): summary = [dict(text=s, page=None, source="AI summary of document") for s in ai["summary"]]
    return dict(topics=topics, summary=summary, definitions=defs, formulas=formulas, general_support=gen,
                key_takeaways=take, revision_notes=rev, ai_generated=bool(ai))

def _numeric(rng, difficulty):
    n = {"easy": 4, "medium": 5, "hard": 6}.get(difficulty, 5)
    xs = [rng.randint(2, 20) for _ in range(n)]; m = sum(xs) / n
    kind = rng.choice(["mean", "median", "variance"]) if difficulty != "easy" else "mean"
    ans = {"mean": m, "median": statistics.median(xs), "variance": statistics.variance(xs)}[kind]
    label = {"mean": "mean", "median": "median", "variance": "sample variance (divide by n-1)"}[kind]
    return dict(type="numeric", topic="Descriptive Statistics", difficulty=difficulty, question=f"Compute the {label} of: {', '.join(map(str, xs))}. (2 decimals)",
                answer=round(ans, 2), explanation=f"Computed with the standard formula for the {label}: {round(ans, 2)}.", source="calculated (validated by code)")

def generate_quiz(pages, topic=None, n=5, difficulty="medium", fmt="mcq", seed=None):
    """fmt in mcq|tf|short|numeric|mixed. Returns list of questions (with answers; strip before sending)."""
    rng = random.Random(seed); sents = _sentences(pages) if pages else []
    cands = [(p, s, ts) for p, s in sents for ts in [_term_in(s)] if ts and (not topic or topic == "Any" or any(TERMS[t] == topic for t in ts))]
    rng.shuffle(cands); qs = []; pool = list(TERMS)
    fmts = [fmt] if fmt != "mixed" else ["mcq", "tf", "short", "numeric"]
    i = 0
    for p, s, ts in cands:
        if len(qs) >= n: break
        f = fmts[i % len(fmts)]; i += 1; t = ts[0]
        blank = re.sub(r"\b" + re.escape(t) + r"\b", "_____", s, count=1, flags=re.I)
        src = f"Page {p} of your document"
        if f == "numeric": qs.append(_numeric(rng, difficulty)); continue
        if f == "mcq":
            d = rng.sample([x for x in pool if x not in ts and TERMS[x] != TERMS[t]] or [x for x in pool if x != t], 3)
            opts = d + [t]; rng.shuffle(opts)
            qs.append(dict(type="mcq", topic=TERMS[t], difficulty=difficulty, question=f"Fill in the blank: {blank}", options=opts, answer=opts.index(t),
                           explanation=f'The source says: "{s}"', source=src))
        elif f == "tf":
            true = (len(qs) % 2 == 0)
            alt = rng.choice([x for x in pool if x != t and TERMS[x] != TERMS[t]])
            stmt = s if true else re.sub(r"\b" + re.escape(t) + r"\b", alt, s, count=1, flags=re.I)
            qs.append(dict(type="tf", topic=TERMS[t], difficulty=difficulty, question=f"True or false: {stmt}", options=["True", "False"], answer=0 if true else 1,
                           explanation=f'The original sentence is: "{s}"', source=src))
        else:
            qs.append(dict(type="short", topic=TERMS[t], difficulty=difficulty, question=f"Name the missing term: {blank}", answer=t,
                           explanation=f'The source says: "{s}"', source=src))
    # top up from the verified bank / calculators (labelled)
    bank = [q for q in BANK if (not topic or topic == "Any" or q["topic"] == topic)]
    rng.shuffle(bank)
    while len(qs) < n:
        if fmt == "numeric" or (fmt == "mixed" and (len(qs) % 2 == 1 or not bank)): qs.append(_numeric(rng, difficulty)); continue
        if not bank: qs.append(_numeric(rng, difficulty)); continue
        b = bank.pop()
        qs.append(dict(type="mcq", topic=b["topic"], difficulty=b["difficulty"], question=b["question"], options=b["options"], answer=b["correct"],
                       explanation=b["explanation"], source="Verified question bank (not from your document)", bank_id=b["id"]))
    for k, q in enumerate(qs[:n]): q["id"] = k + 1; validate_question(q)
    return qs[:n]

def validate_question(q):
    """Reject malformed items / answer keys. For numeric items, recompute where possible."""
    if q["type"] in ("mcq", "tf"):
        if not isinstance(q["answer"], int) or not 0 <= q["answer"] < len(q["options"]) or len(set(q["options"])) != len(q["options"]):
            raise ValueError("Invalid generated question")
    if q["type"] == "numeric":
        m = re.search(r"of: ([\d, ]+)\.", q["question"]); xs = [float(x) for x in m.group(1).split(",")] if m else None
        if xs:
            kind = "variance" if "variance" in q["question"] else "median" if "median" in q["question"] else "mean"
            exp = {"mean": sum(xs) / len(xs), "median": statistics.median(xs), "variance": statistics.variance(xs) if len(xs) > 1 else 0}[kind]
            if abs(round(exp, 2) - q["answer"]) > 1e-9: raise ValueError("Numeric answer key failed validation")
    return True

def public_question(q):
    return {k: v for k, v in q.items() if k not in ("answer", "explanation", "bank_id")}

def check_answer(q, given):
    if given is None or given == "": return False
    if q["type"] in ("mcq", "tf"): return given == q["answer"]
    if q["type"] == "short": return str(given).strip().lower() == str(q["answer"]).lower()
    try: return abs(float(given) - float(q["answer"])) <= 0.011
    except (TypeError, ValueError): return False

def similar_practice(topic, exclude_id=None, difficulty="easy"):
    """A different verified question on the same concept area (or a numeric item for Descriptive Statistics)."""
    pool = [b for b in BANK if b["topic"] == topic and b["id"] != exclude_id]
    if pool: return _pub(pool[0]) | {"bank_id": pool[0]["id"]}
    return None
