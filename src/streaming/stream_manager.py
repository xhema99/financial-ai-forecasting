import time
import threading
import signal
import sys

from src.streaming.event_bus import create_event_bus
from src.streaming.producer import FinancialDataProducer
from src.streaming.consumer import FinancialDataConsumer
import src.streaming.config as cfg


class StreamManager:
    def __init__(self, csv_path: str = "data/raw/KEEDIO_Cierre_Mensual.csv",
                 interval: float = 0.3):
        self.csv_path = csv_path
        self.interval = interval
        self.event_bus = create_event_bus()
        self.producer = FinancialDataProducer(
            self.event_bus, csv_path, interval_seconds=interval
        )
        self.consumer = FinancialDataConsumer(self.event_bus)
        self._running = False

    def run(self, process_every: int = 10):
        print("=" * 60)
        print("  KEEDIO Financial AI — Streaming Mode")
        print(f"  Mode: {'MOCK' if cfg.MOCK_MODE else 'REAL KAFKA'}")
        print(f"  Topic: {cfg.KAFKA_TOPIC_RAW}")
        print("=" * 60)

        self._running = True
        self.consumer.start()

        cons_thread = threading.Thread(
            target=self.event_bus.start_consuming, daemon=True
        )
        cons_thread.start()

        time.sleep(1)

        print(f"\nStreaming {self.csv_path} to event bus...\n")
        records_before = 0
        self.producer.stream_all()

        print("\nProcessing streamed data...")
        result = self.consumer.process_batch()
        print(f"Result: {result}")

        self._running = False
        self.event_bus.stop()
        print("\nStreaming session complete.")

        return result

    def run_interactive(self, process_every: int = 10):
        self._running = True
        self.consumer.start()

        cons_thread = threading.Thread(
            target=self.event_bus.start_consuming, daemon=True
        )
        cons_thread.start()

        time.sleep(1)

        prod_thread = threading.Thread(
            target=self.producer.stream_all, daemon=True
        )
        prod_thread.start()

        try:
            while self._running:
                if self.consumer.record_count % process_every == 0:
                    print(f"Records so far: {self.consumer.record_count}")
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self._running = False
            self.event_bus.stop()
