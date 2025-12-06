import numpy as np
from scipy.stats import ks_2samp

def check_drift(reference_features, new_features):
    drifted = False
    for col in reference_features.columns:
        stat, p_val = ks_2samp(reference_features[col], new_features[col])
        if p_val < 0.01:
            drifted = True
            print(f"Drift detected in {col}: p={{p_val}}")
    return drifted
