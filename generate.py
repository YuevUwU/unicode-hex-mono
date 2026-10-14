import argparse

import config
from generator import generate_ascii_subset, generate_multi_file


def parse_codepoint(value: str) -> int:
    """Parse decimal or prefixed hexadecimal Unicode codepoint."""
    try:
        cp = int(value, 0)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid codepoint: {value!r}") from exc

    if not 0 <= cp <= 0x10FFFF:
        raise argparse.ArgumentTypeError(f"Codepoint out of range: {value}")

    return cp


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate UnicodeHexMono font files.")

    # Generation mode: ASCII subset or a specific Unicode range.
    mode_group = parser.add_mutually_exclusive_group(required=True)

    _ = mode_group.add_argument(
        "--ascii-subset",
        action="store_true",
        help="Generate only ASCII & Extended ASCII subset (U+0000-U+00FF).",
    )

    _ = mode_group.add_argument(
        "--range",
        nargs=2,
        type=parse_codepoint,
        metavar=("START", "END"),
        help="Generate a Unicode range, inclusive (e.g. --range 0x0100 0x80FF).",
    )

    _ = mode_group.add_argument(
        "--all",
        action="store_true",
        help="Generate whole unicode range and ascii subset",
    )

    _ = parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned generation without writing font files.",
    )

    _ = parser.add_argument(
        "--woff",
        action="store_true",
        help="Also generate WOFF2 files.",
    )

    args = parser.parse_args()

    # Generate ASCII subset only.
    if args.ascii_subset:
        _generated_files = generate_ascii_subset(
            dry_run=args.dry_run,
            generate_woff=args.woff,
        )
        return

    # Generate the specified Unicode range, or the full configured range.
    if args.range is not None:
        start, end = args.range

        if start > end:
            parser.error("--range START must be less than or equal to END")

        if start < config.UNICODE_MIN or end > config.UNICODE_MAX:
            parser.error(
                f"--range must be within U+{config.UNICODE_MIN:04X} - U+{config.UNICODE_MAX:04X}"
            )

        wanted_range = range(start, end + 1)
    else:
        # --all
        wanted_range = None

    generate_multi_file(
        wanted_range=wanted_range,
        dry_run=args.dry_run,
        generate_ascii=args.all,
        generate_woff=args.woff,
    )


if __name__ == "__main__":
    main()
