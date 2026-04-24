from scipy.stats import bootstrap
import numpy as np
import scipy


# Find the 95% Confidence Interval, Standard Error, and Margin of Error for Correctness and Hallucination

def compute_bootstrap(df, column):
    """Compute the CI high, CI Low,
    standard error and margin of error (MOE) for a given dataframe and column"""
    clean_values = df[column].dropna() # drop NaNs
    df_array = clean_values.values #values converts and pandas Series into a numpy array
    result = bootstrap(
        data=(df_array,),  # tuple containing array — what bootstrap wants
        method='BCa',
        statistic=np.mean,
        rng=42
    )
    
  
    return result

def print_bootstrap_results(result, df_name: str, column_name: str):
    """With the copnute_bootstrap result, print the CI high, CI Low,
    standard error and margin of error (MOE), denormalizing the results.""" 
    print(f"--- {df_name}: {column_name} ---")
    print(f"95% CI Low: {result.confidence_interval.low * 2}")
    print(f"95% CI High: {result.confidence_interval.high * 2}")
    print(f"Standard error: {result.standard_error * 2}")
    MOE = (result.confidence_interval.high *2 - result.confidence_interval.low *2)
    print(f"MOE: {MOE:.2f}")
    

def get_score(df, column: str):
    """Print the mean score for the column in the dataframe"""
    df_clean = df[column].dropna()
    df_array = df_clean.values
    score = df_array.mean() * 2
    print(f"Score: {score}")

def do_t_test(baseline_df, new_df, column):
    baseline_score = baseline_df[column].dropna()
    new_score = new_df[column].dropna()

    result = scipy.stats.ttest_rel(baseline_score, new_score)
    return result