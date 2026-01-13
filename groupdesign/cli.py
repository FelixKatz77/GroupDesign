import argparse
import sys
import numpy as np
from groupdesign.best_of_greedy import greedy_design

def main():
    parser = argparse.ArgumentParser(description="Generate a greedy block design.")
    parser.add_argument("n", type=int, help="Total number of elements")
    parser.add_argument("k", type=int, help="Size of each block")
    parser.add_argument("--t", type=int, default=2, help="Tuple size to cover (default: 2)")
    parser.add_argument("--m", type=int, default=100, help="Number of design attempts (default: 100)")
    parser.add_argument("--lambda", dest="lambda_val", type=int, default=1, help="Coverage factor (default: 1)")
    parser.add_argument("--output", "-o", type=str, help="CSV output path")

    args = parser.parse_args()

    try:
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

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
