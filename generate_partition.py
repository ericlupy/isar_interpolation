import pandas as pd
import argparse


def uuv_partition(small=False):
    test_set = []  # 100 * 20 = 2000 regions

    if not small:
        y_lb = 12.0
        y_ub = 22.0
        y_step = 0.1  # pos_y, 100 intervals
        h_lb = 10.0
        h_ub = 30.0
        h_step = 1.0  # headings in degrees, will be converted to radians during verification, 20 intervals
    else:
        y_lb = 14.0
        y_ub = 20.0
        y_step = 1.0  # pos_y, 6 intervals
        h_lb = 10.0
        h_ub = 11.0
        h_step = 1.0  # headings, 1 interval

    y = y_lb
    while y < y_ub:
        h = h_lb
        while h < h_ub:
            test_set.append([round(y, 3), round(y + y_step, 3), round(h, 3), round((h + h_step), 3)])
            h += h_step
        y += y_step

    return test_set


def mc_partition(small=False):
    test_set = []  # 90 * 10 = 900 regions

    if not small:
        pos_lb = -0.505
        pos_ub = 0.395
        pos_step = 0.01  # position, 90 intervals
        vel_lb = -0.055
        vel_ub = 0.045
        vel_step = 0.01  # velocity, 10 intervals
    else:
        pos_lb = 0.0
        pos_ub = 0.1
        pos_step = 0.05  # position, 2 intervals
        vel_lb = -0.04
        vel_ub = -0.02
        vel_step = 0.01  # velocity, 2 intervals

    pos = pos_lb
    while pos < pos_ub:
        vel = vel_lb
        while vel < vel_ub:
            test_set.append([round(pos, 3), round(pos + pos_step, 3), round(vel, 3), round(vel + vel_step, 3)])
            vel += vel_step
        pos += pos_step

    return test_set


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", help="uuv or mc", default='uuv')
    parser.add_argument("--small", help="True or False", default=False)
    args = parser.parse_args()

    if not bool(args.small):
        if args.benchmark == 'uuv':
            test_set = uuv_partition()
            df_test_set = pd.DataFrame(test_set, columns=['y_lo', 'y_hi', 'h_lo', 'h_hi'])
            df_test_set.to_csv('uuv_initial_state_regions.csv', index=False)
        elif args.benchmark == 'mc':
            test_set = mc_partition()
            df_test_set = pd.DataFrame(test_set, columns=['pos_lo', 'pos_hi', 'vel_lo', 'vel_hi'])
            df_test_set.to_csv('mc_initial_state_regions.csv', index=False)
        else:
            raise NotImplementedError
    else:
        if args.benchmark == 'uuv':
            test_set = uuv_partition(small=True)
            df_test_set = pd.DataFrame(test_set, columns=['y_lo', 'y_hi', 'h_lo', 'h_hi'])
            df_test_set.to_csv('uuv_initial_state_regions_small.csv', index=False)
        elif args.benchmark == 'mc':
            test_set = mc_partition(small=True)
            df_test_set = pd.DataFrame(test_set, columns=['pos_lo', 'pos_hi', 'vel_lo', 'vel_hi'])
            df_test_set.to_csv('mc_initial_state_regions_small.csv', index=False)
        else:
            raise NotImplementedError
