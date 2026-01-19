import argparse
import sys
import numpy as np
from groupdesign.best_of_greedy import greedy_design

import argparse
import sys
import csv
import numpy as np
from groupdesign.best_of_greedy import greedy_design
from groupdesign.interval_sectioning import interval_sectioning


def get_int_input(prompt, required=True):
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                if required:
                    print("This field is required.")
                    continue
                return None
            return int(val)
        except ValueError:
            print("Please enter a valid integer.")


def interactive_mode():
    print("Welcome to GroupDesign CLI.")
    print("Select an algorithm:")
    print("1. Best of Greedy (Design Generation)")
    print("2. Interval Sectioning (Active Tuple Search)")

    while True:
        choice = input("Enter 1 or 2: ").strip()
        if choice in ('1', '2'):
            break
        print("Invalid choice.")

    algorithm = "greedy" if choice == "1" else "interval"

    n = get_int_input("Enter n (Total number of elements): ")
    t = get_int_input("Enter t (Tuple size, default 2): ", required=False)
    if t is None: t = 2

    k = None
    m = 100
    lambda_val = 1
    max_hits = None

    if algorithm == "greedy":
        k = get_int_input("Enter k (Size of each block): ")

        m_in = get_int_input("Enter m (Number of attempts, default 100): ", required=False)
        if m_in is not None: m = m_in

        l_in = get_int_input("Enter lambda (Coverage factor, default 1): ", required=False)
        if l_in is not None: lambda_val = l_in

    else:  # interval
        hits_in = get_int_input("Enter max_hits (Max active tuples to find, optional): ", required=False)
        if hits_in is not None: max_hits = hits_in

    output = input("Enter output CSV path (optional): ").strip()
    if not output: output = None

    return argparse.Namespace(
        n=n, k=k, t=t, m=m, lambda_val=lambda_val,
        max_hits=max_hits, output=output, algorithm=algorithm
    )


def main():
    # Check if arguments were passed. If not, go to interactive mode.
    if len(sys.argv) == 1:
        args = interactive_mode()
    else:
        parser = argparse.ArgumentParser(description="GroupDesign CLI: Generate designs or search for active tuples.")
        parser.add_argument("n", type=int, help="Total number of elements")
        parser.add_argument("k", type=int, nargs="?", help="Size of each block (required for greedy algorithm)")
        parser.add_argument("--algorithm", choices=["greedy", "interval"], default="greedy",
                            help="Algorithm to run (default: greedy)")
        parser.add_argument("--t", type=int, default=2, help="Tuple size to cover (default: 2)")
        parser.add_argument("--m", type=int, default=100, help="Number of design attempts (default: 100)")
        parser.add_argument("--lambda", dest="lambda_val", type=int, default=1, help="Coverage factor (default: 1)")
        parser.add_argument("--max-hits", type=int,
                            help="Maximum number of active tuples to find (for interval algorithm)")
        parser.add_argument("--output", "-o", type=str, help="CSV output path")

        args = parser.parse_args()

    try:
        if args.algorithm == "greedy":
            if args.k is None:
                # If using CLI args, this check is needed.
                # Interactive mode guarantees k is set for greedy.
                print("Error: Argument 'k' is required for greedy algorithm.", file=sys.stderr)
                sys.exit(1)

            design = greedy_design(
                n=args.n,
                k=args.k,
                t=args.t,
                m=args.m,
                _lambda=args.lambda_val
            )

            if args.output:
                np.savetxt(args.output, design, delimiter=',', fmt='%d')
                print(f"Design saved to {args.output}")
            else:
                print(design)

        elif args.algorithm == "interval":
            active_tuples = interval_sectioning(
                n=args.n,
                t=args.t,
                max_hits=args.max_hits
            )

            if args.output:
                with open(args.output, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerows(active_tuples)
                print(f"Active tuples saved to {args.output}")
            else:
                pass  # interval_sectioning already prints the results

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()