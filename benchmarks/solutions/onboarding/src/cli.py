import argparse
import json
import sys

from src.rank import rank_items


def main():
    parser = argparse.ArgumentParser(description="Rank JSON items by descending priority.")
    parser.add_argument("--limit", type=int, help="return at most this many items (positive integer)")
    args = parser.parse_args()
    try:
        items = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        parser.error(f"invalid JSON: {exc.msg}")
    try:
        ranked = rank_items(items, limit=args.limit)
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(ranked))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
