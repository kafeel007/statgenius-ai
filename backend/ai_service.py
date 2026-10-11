"""LLM access (server side only). Keys come from environment. Returns None when AI is unavailable so
callers fall back to deterministic demo logic."""
import os, json, re
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")

def available():
    if not os.getenv("ANTHROPIC_API_KEY"): return False
    try: import anthropic  # noqa
    except ImportError: return False
    return True

def complete(system, prompt, max_tokens=1500):
    if not available(): return None
    try:
        import anthropic
        c = anthropic.Anthropic()
        m = c.messages.create(model=MODEL, max_tokens=max_tokens, system=system, messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in m.content if getattr(b, "type", "") == "text")
    except Exception:
        return None

def complete_json(system, prompt, max_tokens=2500):
    t = complete(system + " Respond with JSON only, no markdown fences.", prompt, max_tokens)
    if not t: return None
    try: return json.loads(re.sub(r"^```(?:json)?|```$", "", t.strip(), flags=re.M).strip())
    except Exception: return None

TUTOR_SYSTEM = ("You are StatGenius AI Tutor for statistics learners in India's Official Statistical System. Stay on statistics "
    "learning. Use simple English and short step-by-step explanations. If given document excerpts, say 'From your document:' for "
    "claims based on them and 'General explanation:' otherwise. Politely decline unrelated topics.")

_LIB = [
 (("standard deviation","std dev","sd "), "Standard deviation shows how far values typically sit from the mean. Example: 2, 4, 6, 8 has mean 5. Squared deviations are 9, 1, 1, 9 (sum 20). Sample variance = 20/3 = 6.67, so SD = sqrt(6.67) = 2.58. A bigger SD means more spread."),
 (("population","sample"), "A population is every unit you care about (e.g. all households in a state). A sample is the part you actually observe. Statistics (sample mean) estimate parameters (population mean). Good sampling lets you generalise from one to the other."),
 (("sampling",), "Main sampling techniques: Simple random (equal chance for all), Systematic (every k-th unit, k=N/n), Stratified (sample within groups such as states), Cluster (select whole groups, e.g. villages). Stratified improves precision when groups differ; cluster saves cost."),
 (("hypothesis",), "Hypothesis testing: 1) State H0 (no effect) and H1. 2) Pick alpha (e.g. 0.05). 3) Compute a test statistic and p-value. 4) If p < alpha, reject H0; otherwise fail to reject. A small p-value means the data would be unlikely if H0 were true."),
 (("probability",), "Probability measures how likely an event is (0 to 1). Independent events: P(A and B)=P(A)P(B). Mutually exclusive: P(A or B)=P(A)+P(B). Try the Probability questions in the assessment, or ask me to generate five."),
 (("mean","median","mode"), "Mean = sum/n (sensitive to extremes). Median = middle value of sorted data (robust). Mode = most frequent value. For skewed data such as incomes, the median is usually the better summary."),
 (("confidence interval","confidence"), "A confidence interval is mean +/- critical value x standard error. A 95% interval means the method captures the true value in about 95% of repeated samples. Larger samples give narrower intervals."),
 (("regression","correlation"), "Correlation r (-1 to 1) measures linear association. Regression fits y = b0 + b1x; b1 is the change in y per unit of x. R-squared is the share of variation explained. Correlation does not prove causation."),
]
def demo_tutor(message, doc_text=None):
    m = message.lower()
    for keys, ans in _LIB:
        if any(k in m for k in keys):
            return dict(answer="General explanation (demo library, no AI key configured): " + ans, grounded=False)
    return dict(answer="I'm in demo mode with a limited library. Try: standard deviation, population vs sample, sampling techniques, hypothesis testing, probability, mean/median/mode, confidence intervals, regression. I only help with statistics learning.", grounded=False)

def tutor(message, history=None, doc_text=None):
    ctx = f"\n\nDocument excerpts:\n{doc_text[:6000]}" if doc_text else ""
    hist = "\n".join(f"{h['role']}: {h['content']}" for h in (history or [])[-6:])
    out = complete(TUTOR_SYSTEM, f"{hist}\nuser: {message}{ctx}", 700)
    if out: return dict(answer=out, grounded=bool(doc_text), ai=True)
    r = demo_tutor(message, doc_text); r["ai"] = False
    return r
