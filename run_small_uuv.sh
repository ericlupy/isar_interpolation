#!/bin/bash

# Assign values to variables
BENCHMARK="uuv"
IF_SMALL=true
PATH_TO_CONTROL_NETWORK_YML="controllers/uuv_tanh_2_15_2x32_broken.yml"
PATH_TO_VERISIG="verisig"
PATH_TO_VERISIG_OUTPUT="uuv_verisig_output_small"
RATIO=0.25
PATH_TO_PARTITION_CSV="uuv_initial_state_regions_small.csv"
PATH_TO_SAMPLE_RESULT_CSV="uuv_sampling_result_small.csv"
PATH_TO_VERISIG_PARSED_CSV="uuv_verisig_result_small.csv"
N_SAMPLES=10
PATH_TO_OUTPUT="uuv_output_small"
PATH_TO_REPAIRED_CONTROL_NETWORK_YML="uuv_output_small/uuv_repaired_network_small.yml"
PATH_TO_REPAIRED_SAMPLE_RESULT_CSV="uuv_sampling_repaired_result_small.csv"
PATH_TO_REPAIRED_VERISIG_OUTPUT="uuv_verisig_repaired_output_small"
PATH_TO_REPAIRED_VERISIG_PARSED_CSV="uuv_verisig_repaired_result_small.csv"

# Step 1: generate partition
python3 generate_partition.py --benchmark="$BENCHMARK"  --small="$IF_SMALL"

# Step 2: call Verisig
python3 verisig_call.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_path="$PATH_TO_VERISIG" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --cpu_ratio="$RATIO" --initial_state_regions_path="$PATH_TO_PARTITION_CSV"
python3 verisig_parse_results.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --verisig_parsed_csv="$PATH_TO_VERISIG_PARSED_CSV" --initial_state_regions_csv="$PATH_TO_PARTITION_CSV"

# Step 3: incremental repair
python3 sample_states_in_regions.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --initial_state_regions_path="$PATH_TO_PARTITION_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --num_samples_per_region="$N_SAMPLES"
python3 incremental_repair.py --benchmark="$BENCHMARK"  --small="$IF_SMALL" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_result_path="$PATH_TO_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --output_path="$PATH_TO_OUTPUT"

# Step 4: call Verisig and sample again
python3 sample_states_in_regions.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --initial_state_regions_path="$PATH_TO_PARTITION_CSV" --sampled_result_path="$PATH_TO_REPAIRED_SAMPLE_RESULT_CSV" --num_samples_per_region="$N_SAMPLES"
python3 verisig_call.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --verisig_path="$PATH_TO_VERISIG" --verisig_output_path="$PATH_TO_REPAIRED_VERISIG_OUTPUT" --cpu_ratio="$RATIO" --initial_state_regions_path="$PATH_TO_PARTITION_CSV"
python3 verisig_parse_results.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --verisig_output_path="$PATH_TO_REPAIRED_VERISIG_OUTPUT" --verisig_parsed_csv="$PATH_TO_REPAIRED_VERISIG_PARSED_CSV" --initial_state_regions_csv="$PATH_TO_PARTITION_CSV"

# Step 5: visualization
python3 visualization.py --benchmark="$BENCHMARK" --verisig_result_path="$PATH_TO_REPAIRED_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_REPAIRED_SAMPLE_RESULT_CSV" --small="$IF_SMALL"