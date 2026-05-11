from __future__ import annotations
import json
import time
import pandas as pd
from pathlib import Path

from src.streaming.event_bus import EventBus
import src.streaming.config as cfg


class FinancialDataProducer:
    def __init__(self, event_bus: EventBus, csv_path: str,
                 interval_seconds: float = 0.5):
        self.event_bus = event_bus
        self.csv_path = Path(csv_path)
        self.interval = interval_seconds

    def stream_all(self):
        df = pd.read_csv(self.csv_path, encoding="utf-8-sig")
        print(f"Streaming {len(df)} records to topic '{cfg.KAFKA_TOPIC_RAW}'...")
        for _, row in df.iterrows():
            record = row.to_dict()
            record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
            key = f"{record.get('Mes', 'unknown')}_{record.get('Proyecto', 'unknown')}"
            self.event_bus.send(cfg.KAFKA_TOPIC_RAW, key=key, value=record)
            print(f"  sent: {key}")
            time.sleep(self.interval)
        print("Streaming complete.")
