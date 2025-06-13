#!/usr/bin/env python3
"""Log file management utility."""

import argparse
from datetime import datetime, timedelta
from pathlib import Path


def cleanup_logs(log_dir: Path, days: int, dry_run: bool = False) -> int:
    """Remove log files older than specified days."""
    cutoff_date = datetime.now() - timedelta(days=days)
    removed_count = 0

    for log_file in log_dir.glob("*.log"):
        # Parse timestamp from filename (e.g., apply_20250113_123456.log)
        try:
            parts = log_file.stem.split('_')
            if len(parts) >= 3:
                date_str = parts[1]
                time_str = parts[2]
                file_date = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")

                if file_date < cutoff_date:
                    if dry_run:
                        print(f"Would remove: {log_file} ({file_date.date()})")
                    else:
                        log_file.unlink()
                        print(f"Removed: {log_file}")
                    removed_count += 1
        except (ValueError, IndexError):
            print(f"\u26a0\ufe0f  Skipping unparseable filename: {log_file}")

    return removed_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage conversion tool logs")
    parser.add_argument("--cleanup", action="store_true", help="Remove old logs")
    parser.add_argument("--days", type=int, default=30, help="Keep logs newer than N days")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be removed")

    args = parser.parse_args()
    log_dir = Path("log")

    if args.cleanup:
        count = cleanup_logs(log_dir, args.days, args.dry_run)
        print(f"{'Would remove' if args.dry_run else 'Removed'} {count} log files")


if __name__ == "__main__":
    main()
