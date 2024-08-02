from typing import Dict

from repast4py.parameters import create_args_parser, init_params


def run(params: Dict):
    print(params)


def main():
    parser = create_args_parser()
    args = parser.parse_args()
    params = init_params(args.parameters_file, args.parameters)
    run(params)


if __name__ == "__main__":
    main()
