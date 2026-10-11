"""Validated numerical routines for the Practice Lab (no LLM). Every function returns result + steps."""
import math, statistics
from collections import Counter

def _nums(xs, minimum=1):
    try: v = [float(x) for x in xs]
    except (TypeError, ValueError): raise ValueError("Values must be numbers")
    if len(v) < minimum: raise ValueError(f"Enter at least {minimum} value(s)")
    if any(math.isnan(x) or math.isinf(x) for x in v): raise ValueError("Invalid number")
    return v
def r(x, d=4): return round(x, d)

def descriptive(values):
    v = _nums(values, 2); n = len(v); m = sum(v) / n
    s = sorted(v); med = statistics.median(s)
    c = Counter(v); top = max(c.values()); modes = sorted(k for k, f in c.items() if f == top) if top > 1 else []
    ss = sum((x - m) ** 2 for x in v)
    var_s, var_p = ss / (n - 1), ss / n
    steps = [f"n = {n}; sum = {r(sum(v))}", f"Mean = sum/n = {r(m)}", f"Sorted: {s}; median = {r(med)}",
             f"Mode = {modes if modes else 'none (no repeated value)'}",
             f"Sum of squared deviations = {r(ss)}", f"Sample variance = SS/(n-1) = {r(var_s)}",
             f"Population variance = SS/n = {r(var_p)}", f"Sample SD = sqrt({r(var_s)}) = {r(math.sqrt(var_s))}"]
    return dict(result=dict(n=n, mean=r(m), median=r(med), modes=modes, sample_variance=r(var_s),
                population_variance=r(var_p), sample_sd=r(math.sqrt(var_s)), min=min(v), max=max(v)),
                steps=steps, meaning="The mean is the balance point; SD describes typical distance from the mean. Use the sample formulas when your data are a sample.")

def binomial(n, p, k):
    n, k, p = int(n), int(k), float(p)
    if n < 1 or n > 1000 or not 0 <= k <= n or not 0 <= p <= 1: raise ValueError("Need 1<=n<=1000, 0<=k<=n, 0<=p<=1")
    pk = math.comb(n, k) * p ** k * (1 - p) ** (n - k)
    cum = sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k + 1))
    return dict(result=dict(P_equal=r(pk, 6), P_at_most=r(cum, 6), mean=r(n * p), sd=r(math.sqrt(n * p * (1 - p)))),
                steps=[f"P(X={k}) = C({n},{k}) * {p}^{k} * {r(1-p)}^{n-k} = {r(pk,6)}", f"P(X<={k}) = sum of P(X=0..{k}) = {r(cum,6)}",
                       f"Mean = np = {r(n*p)}"], meaning=f"Out of {n} independent trials with success chance {p}, the probability of exactly {k} successes is {r(pk,4)}.")

_T = {90: [6.314, 2.920, 2.353, 2.132], 95: [12.706, 4.303, 3.182, 2.776], 99: [63.657, 9.925, 5.841, 4.604]}
def t_crit(conf, df):
    if conf not in _T: raise ValueError("Confidence must be 90, 95 or 99")
    if df <= 4: return _T[conf][df - 1]
    z = statistics.NormalDist().inv_cdf(0.5 + conf / 200)  # Cornish-Fisher expansion (accurate to ~0.01 for df>=5)
    return z + (z**3 + z) / (4 * df) + (5 * z**5 + 16 * z**3 + 3 * z) / (96 * df**2) + (3 * z**7 + 19 * z**5 + 17 * z**3 - 15 * z) / (384 * df**3)

def confidence_interval(values, confidence=95):
    v = _nums(values, 2); n = len(v); m = sum(v) / n; sd = statistics.stdev(v); se = sd / math.sqrt(n)
    conf = int(confidence); tc = t_crit(conf, n - 1); moe = tc * se
    return dict(result=dict(mean=r(m), sd=r(sd), se=r(se), t_critical=r(tc, 3), margin_of_error=r(moe), lower=r(m - moe), upper=r(m + moe)),
                steps=[f"Mean = {r(m)}, s = {r(sd)}, n = {n}", f"SE = s/sqrt(n) = {r(se)}", f"t critical ({conf}%, df={n-1}) = {r(tc,3)}",
                       f"Margin = t x SE = {r(moe)}", f"Interval = {r(m)} +/- {r(moe)} = ({r(m-moe)}, {r(m+moe)})"],
                meaning=f"The procedure produces intervals that contain the true mean in about {conf}% of repeated samples. This is not a {conf}% probability for this one interval.")

def _t_cdf_two_tail(t, df):
    t = abs(t); c = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))
    f = lambda x: c * (1 + x * x / df) ** (-(df + 1) / 2)
    N = 4000; h = t / N
    s = f(0) + f(t) + sum((4 if i % 2 else 2) * f(i * h) for i in range(1, N))
    return max(0.0, min(1.0, 1 - 2 * s * h / 3 * 1)) if False else max(0.0, min(1.0, 1 - (2 * s * h / 3)))

def one_sample_t(values, mu0, alpha=0.05):
    v = _nums(values, 2); n = len(v); m = sum(v) / n; sd = statistics.stdev(v); se = sd / math.sqrt(n)
    if sd == 0: raise ValueError("All values identical: test undefined")
    t = (m - float(mu0)) / se; p = _t_cdf_two_tail(t, n - 1); rej = p < alpha
    return dict(result=dict(t=r(t), df=n - 1, p_value=r(p, 5), alpha=alpha, reject_null=rej),
                steps=[f"H0: mu = {mu0}; H1: mu != {mu0} (two-tailed)", f"Mean = {r(m)}, SE = {r(se)}", f"t = (mean - mu0)/SE = {r(t)}",
                       f"df = {n-1}; two-tailed p = {r(p,5)}", f"p {'<' if rej else '>='} alpha ({alpha}) -> {'reject' if rej else 'fail to reject'} H0"],
                meaning="Reject H0: the data are unlikely under H0." if rej else "Fail to reject H0: the data do not provide enough evidence of a difference. This does not prove H0.")

def regression(x, y):
    xs, ys = _nums(x, 3), _nums(y, 3)
    if len(xs) != len(ys): raise ValueError("x and y must have the same length")
    n = len(xs); mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((a - mx) ** 2 for a in xs); syy = sum((b - my) ** 2 for b in ys); sxy = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    if sxx == 0 or syy == 0: raise ValueError("x and y must both vary")
    b1 = sxy / sxx; b0 = my - b1 * mx; rr = sxy / math.sqrt(sxx * syy)
    return dict(result=dict(n=n, r=r(rr), r_squared=r(rr * rr), slope=r(b1), intercept=r(b0)),
                steps=[f"mean x = {r(mx)}, mean y = {r(my)}", f"Sxy = {r(sxy)}, Sxx = {r(sxx)}, Syy = {r(syy)}", f"slope = Sxy/Sxx = {r(b1)}",
                       f"intercept = ybar - slope*xbar = {r(b0)}", f"r = Sxy/sqrt(Sxx*Syy) = {r(rr)}; R^2 = {r(rr*rr)}"],
                meaning=f"Fitted line: y = {r(b0,3)} + {r(b1,3)}x. {r(rr*rr*100,1)}% of the variation in y is linearly associated with x. Correlation is not causation.")

def sampling_error(sd, n, population=None):
    sd, n = float(sd), int(n)
    if sd < 0 or n < 2: raise ValueError("Need sd>=0 and n>=2")
    se = sd / math.sqrt(n); steps = [f"SE = sd/sqrt(n) = {r(se)}"]
    if population:
        N = int(population)
        if n > N: raise ValueError("n cannot exceed population size")
        fpc = math.sqrt((N - n) / (N - 1)); se *= fpc; steps.append(f"Finite population correction = sqrt((N-n)/(N-1)) = {r(fpc)}; SE = {r(se)}")
    return dict(result=dict(standard_error=r(se), n_for_half_se=4 * n), steps=steps,
                meaning="Standard error is the typical size of sampling error for the mean. Quadrupling n halves it.")

def data_quality(values, minimum=None, maximum=None):
    """values: list of raw strings/numbers; blanks/NA/null = missing. Reports missing, invalid, out-of-range, duplicates."""
    rows = list(values)
    if not rows: raise ValueError("No values given")
    missing, invalid, outr, nums = [], [], [], []
    for i, x in enumerate(rows, 1):
        s = str(x).strip()
        if s == "" or s.lower() in ("na", "n/a", "nan", "null", "none"): missing.append(i); continue
        try: f = float(s)
        except ValueError: invalid.append(i); continue
        nums.append((i, f))
        if (minimum is not None and f < float(minimum)) or (maximum is not None and f > float(maximum)): outr.append(i)
    c = Counter(f for _, f in nums); dups = sorted(k for k, n in c.items() if n > 1)
    pct = round(100 * len(missing) / len(rows), 1)
    return dict(result=dict(records=len(rows), missing_count=len(missing), missing_pct=pct, missing_positions=missing, non_numeric_positions=invalid,
                out_of_range_positions=outr, repeated_values=dups),
                steps=[f"{len(rows)} records checked", f"Missing: {len(missing)} ({pct}%) at {missing}", f"Non-numeric: {invalid}",
                       f"Outside [{minimum},{maximum}]: {outr}", f"Repeated values (check IDs if unique expected): {dups}"],
                meaning="Resolve invalid and out-of-range values first; then decide how to treat missing data (and document the assumption).")

CALCS = {"descriptive": lambda d: descriptive(d["values"]), "binomial": lambda d: binomial(d["n"], d["p"], d["k"]),
         "ci": lambda d: confidence_interval(d["values"], d.get("confidence", 95)),
         "ttest": lambda d: one_sample_t(d["values"], d["mu0"], float(d.get("alpha", 0.05))),
         "regression": lambda d: regression(d["x"], d["y"]), "sampling_error": lambda d: sampling_error(d["sd"], d["n"], d.get("population") or None),
         "quality": lambda d: data_quality(d["values"], d.get("minimum"), d.get("maximum"))}
