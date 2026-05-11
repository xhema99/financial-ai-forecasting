#!/usr/bin/env python3
"""Keedio Financial AI — Streaming Pipeline Entry Point."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.streaming.stream_manager import StreamManager


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Keedio Financial AI Streaming Pipeline"
    )
    parser.add_argument(
        "--csv", default="data/raw/KEEDIO_Cierre_Mensual.csv",
        help="Path to CSV data file"
    )
    parser.add_argument(
        "--interval", type=float, default=0.3,
        help="Seconds between streaming messages"
    )
    parser.add_argument(
        "--mock", action="store_true", default=True,
        help="Use mock event bus (no Kafka broker needed)"
    )
    parser.add_argument(
        "--no-mock", action="store_false", dest="mock",
        help="Use real Kafka broker"
    )
    args = parser.parse_args()

    import os
    os.environ["KAFKA_MOCK_MODE"] = str(args.mock).lower()

    mgr = StreamManager(csv_path=args.csv, interval=args.interval)
    result = mgr.run()

    print("\nDone.")
    return result


if __name__ == "__main__":
    main()
