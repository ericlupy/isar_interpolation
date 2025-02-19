import numpy as np
import time
from incremental_repair_utils import *


def uuv_control_nn_convex_comb(net_1: UUV_Control_NN, net_2: UUV_Control_NN, w=0.5):
    assert 0.0 <= w <= 1.0
    net_comb = UUV_Control_NN()
    for param1, param2, param_avg in zip(net_1.parameters(), net_2.parameters(), net_comb.parameters()):
        param_avg.data.copy_(param1.data * w + param2.data * (1 - w))
    return net_comb


# net_lo: old network before sim annealing, net_hi: new network after sim annealing
def uuv_ibcl_convex_comb_binary_search(net_lo: UUV_Control_NN, net_hi: UUV_Control_NN, bad_states: list, good_states: list, epsilon_step=1e-7):

    w_lo = 0.0
    w_hi = 1.0
    w_mid = 0.5
    net_mid = net_hi  # init to new network
    success = False

    start_time = time.time()

    while w_hi - w_lo >= epsilon_step:

        print(f'IBCL convex comb binary search with w_mid = {w_mid} ...')

        # Convex combination in Gaussian space - equivalent to NN weights
        net_mid = uuv_control_nn_convex_comb(net_lo, net_hi, w=w_mid)

        # Check if any good state is broken
        h_robustness_good = []
        for good_state in good_states:
            _, traj_y_good = uuv_simulate(net=net_mid, init_pos_y=good_state[0],
                                      init_global_heading_deg=good_state[1])
            h_robustness_good += [uuv_robustness(traj_y_good)]

        if len(h_robustness_good) > 0:
            print(f'Good states robustness after comb, min: {np.min(h_robustness_good)}')

        if len(h_robustness_good) == 0 or np.min(h_robustness_good) < 0.0:  # Good state broken, step closer to old network
            w_hi = w_mid
            w_mid = (w_lo + w_hi) / 2
            net_hi = net_mid
            continue

        # No good state is broken, check if any bad state is repaired
        h_robustness_bad = []
        for bad_state in bad_states:
            _, traj_y_bad = uuv_simulate(net=net_mid, init_pos_y=bad_state[0],
                                          init_global_heading_deg=bad_state[1])
            h_robustness_bad += [uuv_robustness(traj_y_bad)]

        if len(h_robustness_bad) > 0:
            print(f'Bad states robustness after comb, min: {np.min(h_robustness_bad)}')

        if len(h_robustness_bad) == 0 or np.max(h_robustness_bad) >= 0.0:  # No good state is broken and a bad state repaired, succeed
            print('Success')
            success = True
            break

        # No good state is broken and bad region is not repaired, step closer to new network
        w_lo = w_mid
        w_mid = (w_lo + w_hi) / 2
        net_lo = net_mid

    print(f'Computing IBCL convex comb takes {time.time() - start_time}')

    return net_mid, success


def mc_control_nn_convex_comb(net_1: MC_Control_NN, net_2: MC_Control_NN, w=0.5):
    assert 0.0 <= w <= 1.0
    net_comb = MC_Control_NN()
    for param1, param2, param_avg in zip(net_1.parameters(), net_2.parameters(), net_comb.parameters()):
        param_avg.data.copy_(param1.data * w + param2.data * (1 - w))
    return net_comb


# net_lo: old network before sim annealing, net_hi: new network after sim annealing
def mc_ibcl_convex_comb_binary_search(net_lo: MC_Control_NN, net_hi: MC_Control_NN, bad_states: list, good_states: list, epsilon_step=1e-7):

    w_lo = 0.0
    w_hi = 1.0
    w_mid = 0.5
    net_mid = net_hi  # init to new network
    success = False

    start_time = time.time()

    while w_hi - w_lo >= epsilon_step:

        print(f'IBCL convex comb binary search with w_mid = {w_mid} ...')

        # Convex combination in Gaussian space - equivalent to NN weights
        net_mid = mc_control_nn_convex_comb(net_lo, net_hi, w=w_mid)

        # Check if any good state is broken
        h_robustness_good = []
        for good_state in good_states:
            traj_pos_good, _ = mc_simulate(net=net_mid, pos_0=good_state[0], vel_0=good_state[1])
            h_robustness_good += [mc_robustness(traj_pos_good)]

        if len(h_robustness_good) > 0:
            print(f'Good states robustness after comb, min: {np.min(h_robustness_good)}')

        if len(h_robustness_good) == 0 or np.min(h_robustness_good) < 0.0:  # Good state broken, step closer to old network
            w_hi = w_mid
            w_mid = (w_lo + w_hi) / 2
            net_hi = net_mid
            continue

        # No good state is broken, check if any bad state is repaired
        h_robustness_bad = []
        for bad_state in bad_states:
            traj_pos_bad, _ = mc_simulate(net=net_mid, pos_0=bad_state[0], vel_0=bad_state[1])
            h_robustness_bad += [mc_robustness(traj_pos_bad)]

        if len(h_robustness_bad) > 0:
            print(f'Bad states robustness after comb, min: {np.min(h_robustness_bad)}')

        if len(h_robustness_bad) == 0 or np.max(h_robustness_bad) >= 0.0:  # No good state is broken and a bad state repaired, succeed
            print('Success')
            success = True
            break

        # No good state is broken and bad region is not repaired, step closer to new network
        w_lo = w_mid
        w_mid = (w_lo + w_hi) / 2
        net_lo = net_mid

    print(f'Computing IBCL convex comb takes {time.time() - start_time}')

    return net_mid, success