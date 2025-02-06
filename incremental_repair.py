import os
import argparse
from ibcl_convex_comb import *


# Simulated annealing subroutine
def simulated_annealing(region_id, net, bad_states, std=0.1, T=0.1, alpha=0.95, num_iter=200, benchmark='uuv'):

    start_time = time.time()

    print(f'Simulated annealing on region {region_id} ...')
    # task_name = f'iter_{iter_num}_region_{region_id}'

    if benchmark == 'uuv':
        current_obj_value = uuv_energy(bad_states, net)
    elif benchmark == 'mc':
        current_obj_value = mc_energy(bad_states, net)
    else:
        raise NotImplementedError

    for i in range(num_iter):
        rejected = False
        print(f"Annealing iteration {i} ...")
        old_params = [param.clone() for param in net.parameters()]

        # Perturb the control network
        for param in net.parameters():
            noise = torch.normal(mean=0.0, std=std, size=param.size())
            param.data += noise

        if benchmark == 'uuv':
            new_obj_value = uuv_energy(bad_states, net)
        elif benchmark == 'mc':
            new_obj_value = mc_energy(bad_states, net)
        else:
            raise NotImplementedError

        # Metropolis-Hastings criterion
        delta_E = new_obj_value - current_obj_value
        if delta_E < 0.001 and torch.rand(1).item() > np.exp(delta_E / T):
            print("Rejected due to M-H criterion violated, rollback to previous params")
            for old_param, param in zip(old_params, net.parameters()):
                param.data = old_param.data
            rejected = True

        # Not rejected, update params
        if not rejected:
            print("Better params identified")
            current_obj_value = new_obj_value  # Update current value

        # Cooling
        T *= alpha

    print(f'Execution time: {time.time() - start_time}')

    return net


# Main ISAR algorithm
def isari_main(verisig_result_path, sampled_result_path, net_path, output_path, benchmark='uuv'):

    # Directory to save all logs and checkpoints
    if not os.path.exists(output_path):
        os.mkdir(output_path)

    def check_red(region_id):
        return dict_color[region_id] == 'red'

    def check_yellow(region_id):
        return dict_color[region_id] == 'yellow'

    def check_green(region_id):
        return dict_color[region_id] == 'green'

    start_time = time.time()

    dict_color = color_regions(verisig_result_path, sampled_result_path)  # color regions
    df_sample = pd.read_csv(sampled_result_path)
    red_mask = df_sample['region'].apply(check_red)
    df_red = df_sample[red_mask]
    yellow_mask = df_sample['region'].apply(check_yellow)
    df_yellow = df_sample[yellow_mask]
    green_mask = df_sample['region'].apply(check_green)
    df_green = df_sample[green_mask]

    # Sort the red regions in decreasing avg robustness (greedy order in ease of repair)
    region_robustness = sort_regions(df_red)

    # Get good states - for computation efficiency, take one good state to be protected per region
    df_red_good = df_red[df_red['result'] >= 0.0]
    df_red_good_approx = df_red_good.groupby('region').apply(lambda x: x.head(5)).reset_index(drop=True)
    df_yellow_approx = df_yellow.groupby('region').apply(lambda x: x.head(5)).reset_index(drop=True)
    df_green_approx = df_green.groupby('region').apply(lambda x: x.head(5)).reset_index(drop=True)
    df_good_approx = pd.concat([df_red_good_approx, df_yellow_approx, df_green_approx])

    if benchmark == 'uuv':
        good_states = [(row['y'], row['h'], row['result']) for index, row in df_good_approx.iterrows()]
    elif benchmark == 'mc':
        good_states = [(row['pos'], row['vel'], row['result']) for index, row in df_good_approx.iterrows()]
    else:
        raise NotImplementedError

    # Load controller network to be repaired
    with open(net_path, 'rb') as f:
        model_dict = yaml.safe_load(f)
    if benchmark == 'uuv':
        net = UUV_Control_NN()
    elif benchmark == 'mc':
        net = MC_Control_NN()
    else:
        raise NotImplementedError
    load_model_dict(model_dict, net)

    iter_num = 0
    count_red_regions = len(region_robustness)
    print(f'Count red regions: {count_red_regions}')

    prev_regions = []
    cases_result = {'NS': 0, 'NF': 0, 'IS': 0, 'IF': 0}

    # Simulated annealing main loop
    while len(region_robustness) > 0:

        iter_start_time = time.time()

        print(f'Remaining regions to be repaired: {len(region_robustness)}')

        bad_region_id = region_robustness[0][0]  # get next region to repair
        df_region = df_sample[df_sample['region'] == bad_region_id]
        df_region_bad = df_region[df_region['result'] < 0.0]

        if benchmark == 'uuv':
            bad_states = [(row['y'], row['h']) for index, row in df_region_bad.iterrows()]
        elif benchmark == 'mc':
            bad_states = [(row['pos'], row['vel']) for index, row in df_region_bad.iterrows()]
        else:
            raise NotImplementedError

        if bad_region_id in prev_regions:
            print('Already worked on this region, pass')
            del region_robustness[0]
            iter_num += 1
            continue

        if len(bad_states) == 0:
            print('No bad states identified')
            del region_robustness[0]
            iter_num += 1
            continue

        print(f'Bad states identified: {bad_states}')

        # Simulated annealing
        net_updated = simulated_annealing(bad_region_id, net, bad_states, benchmark=benchmark)

        # Step 1 after sim annealing update: Check if bad region is repaired
        t1 = time.time()
        h_robustness_bad_prev = []
        h_robustness_bad = []
        repaired_states = []
        for bad_state in bad_states:
            if benchmark == 'uuv':
                _, traj_y_bad = uuv_simulate(net=net_updated, init_global_heading_deg=bad_state[0], init_pos_y=bad_state[1])
                robustness = uuv_robustness(traj_y_bad)
                _, traj_y_bad_prev = uuv_simulate(net=net, init_global_heading_deg=bad_state[0], init_pos_y=bad_state[1])
                robustness_prev = uuv_robustness(traj_y_bad_prev)
            elif benchmark == 'mc':
                traj_pos_bad, _ = mc_simulate(net=net_updated, pos_0=bad_state[0], vel_0=bad_state[1])
                robustness = mc_robustness(traj_pos_bad)
                traj_pos_bad_prev, _ = mc_simulate(net=net, pos_0=bad_state[0], vel_0=bad_state[1])
                robustness_prev = mc_robustness(traj_pos_bad_prev)
            else:
                raise NotImplementedError
            if robustness >= 0.0:
                repaired_states += [bad_state]
            h_robustness_bad += [robustness]
            h_robustness_bad_prev += [robustness_prev]

        print(f'Avg bad states robustness before and after sim annealing: {np.mean(h_robustness_bad_prev)}, {np.mean(h_robustness_bad)}')
        print(f'Computing bad states robustness takes {time.time() - t1}')

        if len(repaired_states) == 0:
            print('Case NF: bad region is not repaired, continue to next region')
            del region_robustness[0]
            cases_result['NF'] += 1
            iter_num += 1
            continue

        # Step 2: Check if any good state broken
        t2 = time.time()
        h_robustness_good_prev = []
        h_robustness_good = []
        for good_state in good_states:
            if benchmark == 'uuv':
                _, traj_y_good = uuv_simulate(net=net_updated, init_global_heading_deg=good_state[0], init_pos_y=good_state[1])
                robustness = uuv_robustness(traj_y_good)
                _, traj_y_good_prev = uuv_simulate(net=net, init_global_heading_deg=good_state[0], init_pos_y=good_state[1])
                robustness_prev = uuv_robustness(traj_y_good_prev)
            elif benchmark == 'mc':
                traj_pos_good, _ = mc_simulate(net=net_updated, pos_0=good_state[0], vel_0=good_state[1])
                robustness = mc_robustness(traj_pos_good)
                traj_pos_good_prev, _ = mc_simulate(net=net, pos_0=good_state[0], vel_0=good_state[1])
                robustness_prev = mc_robustness(traj_pos_good_prev)
            else:
                raise NotImplementedError
            h_robustness_good += [robustness]
            h_robustness_good_prev += [robustness_prev]

        print(f'Good states robustness before and after sim annealing, mean / min: {np.mean(h_robustness_good_prev)}, {np.min(h_robustness_good)}')
        print(f'Computing good states robustness takes {time.time() - t2}')

        if np.min(h_robustness_good) >= 0.0:  # No good state broken
            print('Case NS: No good state is broken, update net and continue to next region')
            good_states += repaired_states  # update good states, preserve our repaired outcome
            repaired_net_path = os.path.join(output_path, f'tanh_iter_{iter_num}_region_{bad_region_id}.pt')
            torch.save(net_updated, repaired_net_path)
            net_yml_path = os.path.join(output_path, f'tanh_iter_{iter_num}_region_{bad_region_id}.yml')
            dump_model_dict(net_yml_path, net_updated)
            net = net_updated

            # Recompute the red regions and sort
            t3 = time.time()
            sampled_checkpoint_path = os.path.join(output_path, f'sample_checkpoint_iter_{iter_num}_region_{bad_region_id}.csv')
            check_samples(repaired_net_path, sampled_result_path, sampled_checkpoint_path)
            dict_color = color_regions(verisig_result_path, sampled_checkpoint_path)  # recolor regions

            # Update df_sample here
            df_sample = pd.read_csv(sampled_checkpoint_path)  # Updated robustness of all sampled states
            red_mask = df_sample['region'].apply(check_red)
            region_robustness = sort_regions(df_red)  # Update to be repaired regions
            print(f'New sorted regions: {region_robustness}')
            print(f'Re-computing to-be-repaired regions takes {time.time() - t3}')
            cases_result['NS'] += 1
            iter_num += 1
            continue

        # Step 3: Bad region repaired, but good state broken, do IBCL interpolation
        if benchmark == 'uuv':
            net_mid, success = uuv_ibcl_convex_comb_binary_search(net_lo=net, net_hi=net_updated, bad_states=bad_states, good_states=good_states)
        elif benchmark == 'mc':
            net_mid, success = mc_ibcl_convex_comb_binary_search(net_lo=net, net_hi=net_updated, bad_states=bad_states, good_states=good_states)
        else:
            raise NotImplementedError

        if success:  # IBCL found an acceptable net
            print('Case IS: IBCL success')
            good_states += repaired_states  # update good states
            repaired_net_path = os.path.join(output_path, f'tanh_iter_{iter_num}_region_{bad_region_id}.pt')
            torch.save(net_updated, repaired_net_path)
            net_yml_path = os.path.join(output_path, f'tanh_iter_{iter_num}_region_{bad_region_id}.yml')
            dump_model_dict(net_yml_path, net_updated)
            net = net_updated
            del region_robustness[0]

            # Recompute the red regions and sort
            t4 = time.time()
            sampled_checkpoint_path = os.path.join(output_path, f'sample_checkpoint_iter_{iter_num}_region_{bad_region_id}.csv')
            check_samples(repaired_net_path, sampled_result_path, sampled_checkpoint_path)
            dict_color = color_regions(verisig_result_path, sampled_checkpoint_path)  # recolor regions

            # Update df_sample here
            df_sample = pd.read_csv(sampled_checkpoint_path)  # Updated robustness of all sampled states
            red_mask = df_sample['region'].apply(check_red)
            df_red = df_sample[red_mask]
            region_robustness = sort_regions(df_red)  # Update to be repaired regions

            print(f'New sorted regions: {region_robustness}')
            print(f'Re-computing to-be-repaired regions takes {time.time() - t4}')
            cases_result['IS'] += 1
            iter_num += 1
            continue

        # IBCL failure
        print('Case IF: IBCL failure')
        del region_robustness[0]
        cases_result['IF'] += 1
        iter_num += 1

    print(f'Total time: {time.time() - start_time}')
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", help="uuv or mc", default="uuv")
    parser.add_argument("--network", help="network yml file to be repaired", default=os.path.join('controllers', 'uuv_tanh_2_15_2x32_broken.yml'))
    parser.add_argument("--verisig_result_path", help="path to verisig result csv", default=os.path.join('uuv_output', 'uuv_broken_verisig_output.csv'))
    parser.add_argument("--sampled_result_path", help="path to sampling result csv", default=os.path.join('uuv_output', 'uuv_broken_sampling_output.csv'))
    parser.add_argument("--output_path", help="directory for all output files", default='uuv_output')
    args = parser.parse_args()

    isari_main(args.verisig_result_path, args.sampled_result_path, args.network, args.output_path, benchmark=args.benchmark)