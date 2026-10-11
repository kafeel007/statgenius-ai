"""iGOT Karmayogi integration layer (SEPARATE from the core engine).
STATUS: DEMONSTRATION ONLY. These are SAMPLE course records, not data from iGOT Karmayogi.
Path to real integration: implement `fetch_courses` against an officially authorised iGOT API with
approved credentials, keep the same return shape, and switch INTEGRATION_MODE to 'live'."""
INTEGRATION_MODE = "sample"
DISCLAIMER = "Sample course records for demonstration. Not connected to iGOT Karmayogi."
_S = {
 "Descriptive Statistics": ("Sample: Summarising Data with Averages and Spread", "Mean, median, mode, variance and standard deviation for official data.", "3 hrs"),
 "Probability": ("Sample: Probability Foundations for Statisticians", "Rules of probability, independence and distributions.", "4 hrs"),
 "Sampling Techniques": ("Sample: Sampling Methods for Official Surveys", "SRS, stratified, cluster and systematic sampling with design effects.", "5 hrs"),
 "Statistical Inference": ("Sample: Estimation and Confidence Intervals", "Standard error, confidence intervals and interpretation.", "4 hrs"),
 "Hypothesis Testing": ("Sample: Hypothesis Testing in Practice", "p-values, errors and common tests.", "4 hrs"),
 "Regression Analysis": ("Sample: Correlation and Regression Basics", "Fitting and interpreting linear models.", "5 hrs"),
 "Data Visualization": ("Sample: Effective Statistical Charts", "Choosing and designing honest charts.", "2 hrs"),
 "Survey Methodology": ("Sample: Survey Design and Questionnaires", "Frames, questionnaire design and non-response.", "4 hrs"),
 "Data Quality and Validation": ("Sample: Data Validation and Editing", "Range, consistency and uniqueness checks; missing data.", "3 hrs"),
}
def fetch_courses(topic):
    if INTEGRATION_MODE != "sample": raise NotImplementedError("Live iGOT integration not implemented")
    t = _S.get(topic)
    return [] if not t else [dict(topic=topic, title=t[0], description=t[1], duration=t[2], source="SAMPLE", disclaimer=DISCLAIMER)]
