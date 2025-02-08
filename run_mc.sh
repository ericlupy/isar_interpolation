#!/bin/bash

# Assign values to variables
BENCHMARK="mc"
IF_SMALL=false
PATH_TO_CONTROL_NETWORK_YML="controllers/mc_sig_2x16_broken.yml"
PATH_TO_VERISIG="verisig"
PATH_TO_VERISIG_OUTPUT="mc_verisig_output"
RATIO=0.25
PATH_TO_PARTITION_CSV="mc_initial_state_regions.csv"
PATH_TO_SAMPLE_RESULT_CSV="mc_sampling_result.csv"
PATH_TO_VERISIG_PARSED_CSV="mc_verisig_result.csv"
N_SAMPLES=10
PATH_TO_OUTPUT="mc_output"
PATH_TO_REPAIRED_CONTROL_NETWORK_YML="mc_repaired_network.csv"
PATH_TO_REPAIRED_SAMPLE_RESULT_CSV="mc_sampling_repaired_result.csv"
PATH_TO_REPAIRED_VERISIG_OUTPUT="mc_verisig_repaired_output"
PATH_TO_REPAIRED_VERISIG_PARSED_CSV="mc_verisig_repaired_result.csv"

# Step 1: generate partition
python3 generate_partition.py --benchmark="$BENCHMARK"  --small="$IF_SMALL"

# Step 2: call Verisig
python3 verisig_call.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_path="$PATH_TO_VERISIG" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --cpu_ratio="$RATIO" --initial_state_regions_path="$PATH_TO_PARTITION_CSV"
python3 verisig_parse_results.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_output_path="$PATH_TO_VERISIG_OUTPUT" --verisig_parsed_csv="$PATH_TO_VERISIG_PARSED_CSV" --initial_state_regions_csv="$PATH_TO_PARTITION_CSV"

# Step 3: incremental repair
python3 sample_states_in_regions.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --initial_state_regions_path="$PATH_TO_PARTITION_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --num_samples_per_region="$N_SAMPLES"
python3 incremental_repair.py --benchmark="$BENCHMARK" --network="$PATH_TO_CONTROL_NETWORK_YML" --verisig_result_path="$PATH_TO_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_SAMPLE_RESULT_CSV" --output_path="$PATH_TO_OUTPUT"

# Step 4: call Verisig and sample again
python3 sample_states_in_regions.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --initial_state_regions_path="$PATH_TO_PARTITION_CSV" --sampled_result_path="$PATH_TO_REPAIRED_SAMPLE_RESULT_CSV" --num_samples_per_region="$N_SAMPLES"
python3 verisig_call.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --verisig_path="$PATH_TO_VERISIG" --verisig_output_path="$PATH_TO_REPAIRED_VERISIG_OUTPUT" --cpu_ratio="$RATIO" --initial_state_regions_path="$PATH_TO_PARTITION_CSV"
python3 verisig_parse_results.py --benchmark="$BENCHMARK" --network="$PATH_TO_REPAIRED_CONTROL_NETWORK_YML" --verisig_output_path="$PATH_TO_REPAIRED_VERISIG_OUTPUT" --verisig_parsed_csv="$PATH_TO_REPAIRED_VERISIG_PARSED_CSV" --initial_state_regions_csv="$PATH_TO_PARTITION_CSV"

# Step 5: visualization
python3 visualization.py --benchmark="$BENCHMARK" --verisig_result_path="$PATH_TO_REPAIRED_VERISIG_PARSED_CSV" --sampled_result_path="$PATH_TO_REPAIRED_SAMPLE_RESULT_CSV" --small="$IF_SMALL"