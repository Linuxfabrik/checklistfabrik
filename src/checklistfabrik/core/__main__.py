import argparse
import importlib.metadata


def main():
    distribution = importlib.metadata.distribution('checklistfabrik')

    entry_points = {
        entry_point.name: entry_point
        for entry_point in distribution.entry_points
        if entry_point.group == 'console_scripts'
    }

    parser = argparse.ArgumentParser(prog='python -m checklistfabrik.core', add_help=False)
    parser.add_argument('entry_point', choices=entry_points.keys())
    args, extra = parser.parse_known_args()

    entry_points[args.entry_point].load()([args.entry_point] + extra)


if __name__ == '__main__':
    main()
