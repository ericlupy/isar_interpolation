#!/bin/bash

# Assign values to variables
BENCHMARK="mc"
PATH_TO_VERISIG_PARSED_CSV="mc_verisig_repaired_result.csv"  # replace it with the path of Verisig parsed result file you want
PATH_TO_SAMPLE_RESULT_CSV="mc_sampling_repaired_result.csv"  # replace it with the name of sample result file you want
IF_SMALL=false

# Python execution
python3 visualization.py --benchmark="$BENCHMARK" --verisig_result_path="$PATH_TO_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --small="$IF_SMALL"