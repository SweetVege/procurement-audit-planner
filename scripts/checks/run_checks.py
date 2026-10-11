#!/usr/bin/env python3
"""Run the four QA checks on the pack and print one table and a verdict.

Usage (from the project root):
  .venv/bin/python scripts/checks/run_checks.py
  .venv/bin/python scripts/checks/run_checks.py --outputs DIR --data DIR

Exit code 0 = all four pass, 1 = at least one failed.
"""
import sys

import common as c
import check_numbers
import check_quotes
import check_samples
import check_trace

CHECKS = (check_quotes, check_numbers, check_trace, check_samples)


def main():
    outputs, data = c.args(__doc__)
    results = []
    for check in CHECKS:
        try:
            items, summary = check.run(outputs, data)
        except c.Missing as exc:
            items, summary = [str(exc)], "could not complete"
        results.append((check.NAME, items, summary))
        c.finish(check.NAME, items, summary)
        print()
    print("| Check | Result | Items | What was checked |")
    print("| --- | --- | --- | --- |")
    for name, items, summary in results:
        print(f"| {name} | {'FAIL' if items else 'PASS'} | {len(items)} | {summary} |")
    failed = [name for name, items, _ in results if items]
    print()
    print("VERDICT: ALL 4 CHECKS PASS" if not failed
          else f"VERDICT: {len(failed)} OF 4 CHECKS FAILED ({', '.join(failed)})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
