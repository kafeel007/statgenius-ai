"""Regenerates sample_data/sampling_basics.pdf (needs reportlab: pip install reportlab)."""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
P = [["Sampling and Descriptive Statistics - Learning Notes", "",
 "A population is the complete set of units about which we want information.",
 "A sample is a subset of the population that is actually observed.",
 "A sampling frame is the list of units from which the sample is selected.",
 "Simple random sampling gives every unit an equal chance of being selected.",
 "A stratified sample is drawn from each homogeneous group of the population.",
 "Systematic sampling selects every k-th unit, where k = N / n.",
 "Cluster sampling selects whole groups such as villages instead of individuals."],
 ["Measures of Centre and Spread", "",
 "The mean is the sum of all values divided by the number of values.",
 "The median is the middle value of the sorted data and is not affected by extreme values.",
 "The mode is the most frequent value in the data.",
 "Variance measures the average squared deviation from the mean.",
 "The standard deviation is the square root of the variance.",
 "Mean = sum(x) / n",
 "Standard error = s / sqrt(n)"],
 ["Testing and Quality", "",
 "The null hypothesis is the default claim that there is no effect or difference.",
 "The p-value is the probability of data at least as extreme as observed if the null hypothesis is true.",
 "A confidence interval is an estimate range computed from sample data using the standard error.",
 "Non-response occurs when selected respondents do not provide answers.",
 "An outlier is a value that is unusually far from the rest of the data and should be validated."]]
c = canvas.Canvas("sample_data/sampling_basics.pdf", pagesize=A4)
for pg in P:
    y = 800
    for i, line in enumerate(pg):
        c.setFont("Helvetica-Bold" if i == 0 else "Helvetica", 14 if i == 0 else 11); c.drawString(50, y, line); y -= 26
    c.showPage()
c.save()
