import pandas as pd
from scipy.stats import bootstrap
import numpy as np


# Find the 95% Confidence Interval, Standard Error, and Margin of Error for Correctness and Hallucination

def correctness_score(df, df_name):
    # 1. turn score into list for boostrap function
    correctness_array = df["correctness"].values
    #2. Use bootstrap function to dinf the Confidence Interval (default is 0.95) and standard error
    bootstrapped_hallucination = bootstrap(data=(correctness_array,), statistic=np.mean, method='BCa', rng=42)
    result = bootstrapped_hallucination
    print(f"95% CI Correctness Low - {df_name}: {result.confidence_interval.low * 2}") # denormalized
    print(f"95% CI Correctness High - {df_name}: {result.confidence_interval.high * 2}") # deormalized
    standard_erorr_correctness_normalized = result.standard_error *2 # denormalized
    print(f"Standard Error - Correctness - {df_name}: {standard_erorr_correctness_normalized:.4f}")
    # 3. find the margin of error for Hallucination: MOE = (CI High - CI Low) / 2
    correctness_MOE = (result.confidence_interval.high *2 - result.confidence_interval.low *2) / 2 
    print(f"Correctness MOE - {df_name}: {correctness_MOE:.2f}")


def hallucination_score(df, df_name):
    # 1. turn score into list for boostrap function
    hallucination_array = df["hallucination"].values
    #2. Use bootstrap function to dinf the Confidence Interval (default is 0.95) and standard error
    bootstrapped_hallucination = bootstrap(data=(hallucination_array,), statistic=np.mean, method='BCa', rng=42)
    result = bootstrapped_hallucination
    print(f"95% CI Hallucination Low - {df_name}: {result.confidence_interval.low}")
    print(f"95% CI Hallucination High - {df_name}: {result.confidence_interval.high}")
    print(f"Standard Error - Hallucination - {df_name}: {result.standard_error:.4f}")
    # 3. find the margin of error for Hallucination: MOE = (CI High - CI Low) / 2
    hallucination_MOE = (result.confidence_interval.high - result.confidence_interval.low) / 2
    print(f"hallucination_MOE - {df_name}: {hallucination_MOE:.2f}")



def hallucination_score_noramlized(df, df_name):
    # 1. turn score into list for boostrap function
    hallucination_array = df["hallucination"].values
    #2. Use bootstrap function to dinf the Confidence Interval (default is 0.95) and standard error
    bootstrapped_hallucination = bootstrap(data=(hallucination_array,), statistic=np.mean, method='BCa', rng=42)
    result = bootstrapped_hallucination
    print(f"95% CI Hallucination Low - {df_name}: {result.confidence_interval.low * 2}")
    print(f"95% CI Hallucination High - {df_name}: {result.confidence_interval.high * 2}")
    standard_erorr_hallucination_normalized = result.standard_error *2 # denormalized
    print(f"Standard Error - Hallucination - {df_name}: {standard_erorr_hallucination_normalized:.4f}") # denormalize
    # 3. find the margin of error for Hallucination: MOE = (CI High - CI Low) / 2
    hallucination_MOE = (result.confidence_interval.high *2 - result.confidence_interval.low *2) / 2
    print(f"hallucination_MOE - {df_name}: {hallucination_MOE:.2f}")