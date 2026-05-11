import os


KAFKA_BOOTSTRAP_SERVERS = os.getenv(
    "KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"
)
KAFKA_TOPIC_RAW = os.getenv("KAFKA_TOPIC_RAW", "financial.records")
KAFKA_TOPIC_AGGREGATES = os.getenv(
    "KAFKA_TOPIC_AGGREGATES", "financial.aggregates"
)
KAFKA_TOPIC_ALERTS = os.getenv("KAFKA_TOPIC_ALERTS", "financial.alerts")

MOCK_MODE = os.getenv("KAFKA_MOCK_MODE", "true").lower() == "true"

CONSUMER_GROUP = os.getenv("KAFKA_CONSUMER_GROUP", "financial-ai-group")
POLL_TIMEOUT_MS = int(os.getenv("KAFKA_POLL_TIMEOUT_MS", "1000"))
