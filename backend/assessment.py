"""Verified assessment question bank + deterministic grading (no AI involved)."""
TOPICS = ["Descriptive Statistics", "Probability", "Sampling Techniques", "Statistical Inference",
          "Hypothesis Testing", "Regression Analysis", "Data Visualization", "Survey Methodology",
          "Data Quality and Validation"]

# (id, topic, difficulty, question, options, correct_index, concept, explanation)
_RAW = [
 (1,"Descriptive Statistics","easy","Which measure of central tendency is most affected by extreme values?",["Mean","Median","Mode","Interquartile range"],0,"Sensitivity of the mean to outliers","The mean uses every observation, so unusually large or small values pull it strongly. The median and mode depend only on position/frequency."),
 (2,"Descriptive Statistics","easy","For the data 2, 4, 4, 6, 9 what is the median?",["4","5","4.5","6"],0,"Median","Sorted data has 5 values; the middle (3rd) value is 4. (The mean is 5 and the mode is 4.)"),
 (3,"Descriptive Statistics","medium","The sample variance of 2, 4, 6, 8 is:",["5.00","6.67","20.00","2.58"],1,"Sample variance (n-1)","Mean = 5; squared deviations = 9+1+1+9 = 20; sample variance = 20/(n-1) = 20/3 = 6.67. Dividing by n would give the population variance 5.00."),
 (4,"Probability","easy","A fair coin is tossed twice. What is the probability of two heads?",["0.25","0.50","0.75","0.125"],0,"Independent events","The tosses are independent: 0.5 x 0.5 = 0.25."),
 (5,"Probability","medium","If A and B are independent with P(A)=0.3 and P(B)=0.5, then P(A and B) equals:",["0.80","0.15","0.20","0.65"],1,"Multiplication rule","For independent events P(A and B) = P(A) x P(B) = 0.3 x 0.5 = 0.15."),
 (6,"Probability","medium","A and B are mutually exclusive with P(A)=0.40 and P(B)=0.35. P(A or B) is:",["0.14","0.05","0.75","0.60"],2,"Addition rule","For mutually exclusive events P(A or B) = P(A) + P(B) = 0.75 (there is no overlap to subtract)."),
 (7,"Sampling Techniques","easy","Every unit in the population has an equal chance of selection and units are drawn at random. This is:",["Stratified sampling","Simple random sampling","Cluster sampling","Quota sampling"],1,"Simple random sampling","Equal selection probability with random draws defines simple random sampling (SRS)."),
 (8,"Sampling Techniques","medium","The population is divided into homogeneous groups (e.g. states) and a sample is drawn from every group. This is:",["Stratified sampling","Systematic sampling","Convenience sampling","Cluster sampling"],0,"Stratified sampling","Stratified sampling splits the population into strata and samples within each stratum, which guarantees representation and often reduces variance. In cluster sampling only some groups are chosen."),
 (9,"Sampling Techniques","medium","From a population of 1,000 units a systematic sample of 50 is needed. The sampling interval k is:",["10","20","50","25"],1,"Systematic sampling interval","k = N/n = 1000/50 = 20: choose a random start in 1-20, then every 20th unit."),
 (10,"Statistical Inference","medium","A sample of n=25 has standard deviation s=10. The standard error of the mean is:",["10","2","0.4","5"],1,"Standard error","SE = s/sqrt(n) = 10/5 = 2."),
 (11,"Statistical Inference","easy","With confidence level and variability fixed, increasing the sample size makes a confidence interval:",["Wider","Narrower","Unchanged","Biased"],1,"CI width vs n","SE falls as n grows, so the margin of error and the interval width shrink."),
 (12,"Statistical Inference","hard","A 95% confidence interval is best interpreted as:",["There is a 95% probability the true mean lies in this particular interval","95% of the sample data lie in the interval","The method captures the true parameter in about 95% of repeated samples","The sample mean is 95% accurate"],2,"Meaning of confidence","Confidence refers to the long-run success rate of the procedure over repeated sampling, not the probability for one fixed interval."),
 (13,"Hypothesis Testing","easy","If the p-value is smaller than the significance level alpha, we:",["Reject the null hypothesis","Accept the null hypothesis","Increase the sample size","Reject the alternative"],0,"Decision rule","A small p-value means data this extreme would be unlikely if H0 were true, so H0 is rejected at that alpha."),
 (14,"Hypothesis Testing","easy","A Type I error occurs when we:",["Fail to reject a false null","Reject a true null hypothesis","Use the wrong sample","Compute the mean wrongly"],1,"Type I error","Type I error = rejecting a true null hypothesis; its probability is alpha."),
 (15,"Hypothesis Testing","medium","A two-tailed test is appropriate when the alternative hypothesis is:",["mu > mu0","mu < mu0","mu is not equal to mu0","mu = mu0"],2,"One- vs two-tailed","A two-tailed test looks for a difference in either direction, i.e. H1: mu != mu0."),
 (16,"Regression Analysis","easy","A correlation coefficient r = -0.9 indicates:",["A weak positive relationship","A strong negative linear relationship","No relationship","A perfect relationship"],1,"Correlation","The sign gives direction (negative) and |r| near 1 gives a strong linear association."),
 (17,"Regression Analysis","easy","In the fitted line y = 2 + 3x, a one-unit increase in x changes predicted y by:",["2","3","5","1"],1,"Slope interpretation","The slope (3) is the change in predicted y per one-unit change in x."),
 (18,"Regression Analysis","medium","R-squared = 0.64 means:",["64% of the variation in y is explained by the model","The correlation is 0.64","64% of predictions are exact","The slope is 0.64"],0,"Coefficient of determination","R^2 is the proportion of variance in the response explained by the model (here r = +/-0.8)."),
 (19,"Data Visualization","easy","Which chart is best for the distribution of a continuous variable such as age?",["Pie chart","Histogram","Line chart","Stacked bar"],1,"Choosing charts","A histogram bins continuous values and shows shape, centre and spread."),
 (20,"Data Visualization","easy","Which chart is best for showing a trend over time?",["Line chart","Pie chart","Histogram","Scatter of categories"],0,"Choosing charts","Line charts connect ordered time points and make trends visible."),
 (21,"Data Visualization","medium","Starting the y-axis of a bar chart at a value well above zero tends to:",["Make differences look larger than they are","Hide outliers","Improve accuracy","Have no effect"],0,"Misleading axes","Bar length encodes magnitude, so truncating the axis exaggerates relative differences."),
 (22,"Survey Methodology","easy","Which is a leading question?",["How old are you?","Don't you agree the new scheme is excellent?","Which state do you live in?","How many members are in your household?"],1,"Question wording bias","A leading question nudges respondents toward a particular answer and biases results."),
 (23,"Survey Methodology","medium","Non-response bias arises when:",["The sample is too large","Respondents differ systematically from non-respondents","Questions are too short","The frame is a list"],1,"Non-response bias","If those who do not respond differ from those who do, estimates are biased even with a good design."),
 (24,"Survey Methodology","easy","A sampling frame is:",["The final survey report","A list of units from which the sample is drawn","The questionnaire layout","A confidence interval"],1,"Sampling frame","The frame is the list/material that identifies population units for selection."),
 (25,"Data Quality and Validation","easy","A record showing age = 250 years is an example of:",["A valid value","A range-check violation (invalid value)","A duplicate","A missing value"],1,"Range checks","Values outside plausible limits fail a range check and should be queried or corrected."),
 (26,"Data Quality and Validation","medium","Two different respondents share the same ID. Which rule is violated?",["Uniqueness of identifiers","Range check","Consistency of units","Completeness"],0,"Uniqueness checks","IDs are meant to be unique keys; duplicates break record linkage."),
 (27,"Data Quality and Validation","hard","Listwise deletion of missing data is least likely to bias estimates when data are:",["Missing not at random","Missing completely at random","Missing in the largest group only","Missing because of the value itself"],1,"Missing-data mechanisms","Under MCAR the complete cases are a random subset, so deletion loses precision but not unbiasedness."),
]
BANK = [dict(id=r[0], topic=r[1], difficulty=r[2], question=r[3], options=r[4], correct=r[5],
             concept=r[6], explanation=r[7]) for r in _RAW]
BY_ID = {q["id"]: q for q in BANK}

def public(q):
    """Question without answer key (safe to send before submission)."""
    return {k: q[k] for k in ("id", "topic", "difficulty", "question", "options")}

def select_questions(per_topic=3, topics=None):
    topics = topics or TOPICS
    out = []
    for t in topics:
        out += [q for q in BANK if q["topic"] == t][:per_topic]
    return out

def grade(answers):
    """answers: [{question_id, selected, confidence?}] -> dict with per-question results and topic scores.
    Raises ValueError on invalid input."""
    if not answers: raise ValueError("No answers submitted")
    results, seen = [], set()
    for a in answers:
        qid = a.get("question_id"); q = BY_ID.get(qid)
        if q is None: raise ValueError(f"Unknown question id {qid}")
        if qid in seen: raise ValueError(f"Duplicate answer for question {qid}")
        seen.add(qid)
        sel = a.get("selected")
        if sel is not None and (not isinstance(sel, int) or not 0 <= sel < len(q["options"])):
            raise ValueError(f"Invalid option for question {qid}")
        results.append(dict(question_id=qid, topic=q["topic"], difficulty=q["difficulty"], selected=sel,
                            correct_index=q["correct"], is_correct=(sel == q["correct"]),
                            confidence=a.get("confidence")))
    topic_scores = {}
    for r in results:
        t = topic_scores.setdefault(r["topic"], {"correct": 0, "total": 0})
        t["total"] += 1; t["correct"] += int(r["is_correct"])
    for t in topic_scores.values(): t["pct"] = round(100 * t["correct"] / t["total"], 1)
    c = sum(r["is_correct"] for r in results)
    return dict(results=results, topic_scores=topic_scores, correct=c, total=len(results),
                accuracy=round(100 * c / len(results), 1))
