"""Small validation harness for the standardized rubric.

Replace the example assessor scores with anonymized real assessor scores before
claiming an inter-assessor agreement result. The script intentionally reports
metrics rather than declaring improvement.
"""
from statistics import mean

def absolute_differences(a, b):
    return [abs(x-y) for x,y in zip(a,b)]

def pass_agreement(a, b, threshold=70):
    return sum((x >= threshold) == (y >= threshold) for x,y in zip(a,b)) / max(1,len(a))

if __name__ == "__main__":
    assessor_a = [72, 81, 64, 91, 76]
    assessor_b = [70, 79, 66, 88, 74]
    diffs = absolute_differences(assessor_a, assessor_b)
    print({"n":len(diffs),"mean_absolute_score_difference":round(mean(diffs),2),
           "pass_fail_agreement":round(pass_agreement(assessor_a,assessor_b),3),
           "note":"Example values only; replace with collected assessor scores."})
