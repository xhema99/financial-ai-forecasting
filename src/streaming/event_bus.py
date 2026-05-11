from __future__ import annotations
import json
import threading
from abc import ABC, abstractmethod
from queue import Queue, Empty
from typing import Callable

import src.streaming.config as cfg


class EventBus(ABC):
    @abstractmethod
    def send(self, topic: str, key: str, value: dict):
        ...

    @abstractmethod
    def subscribe(self, topic: str, callback: Callable[[str, dict], None]):
        ...

    @abstractmethod
    def start_consuming(self):
        ...

    @abstractmethod
    def stop(self):
        ...


class MockEventBus(EventBus):
    def __init__(self):
        self._topics: dict[str, Queue] = {}
        self._subscriptions: dict[str, list[Callable]] = {}
        self._running = False
        self._threads: list[threading.Thread] = []

    def _ensure_topic(self, topic: str):
        if topic not in self._topics:
            self._topics[topic] = Queue()
            self._subscriptions[topic] = []

    def send(self, topic: str, key: str, value: dict):
        self._ensure_topic(topic)
        msg = {"key": key, "value": value}
        self._topics[topic].put(msg)

    def subscribe(self, topic: str, callback: Callable[[str, dict], None]):
        self._ensure_topic(topic)
        self._subscriptions[topic].append(callback)

    def start_consuming(self):
        self._running = True
        for topic in list(self._topics.keys()):
            t = threading.Thread(
                target=self._consume_loop, args=(topic,), daemon=True
            )
            self._threads.append(t)
            t.start()

    def _consume_loop(self, topic: str):
        while self._running:
            try:
                msg = self._topics[topic].get(timeout=0.5)
                for cb in self._subscriptions.get(topic, []):
                    cb(msg["key"], msg["value"])
            except Empty:
                continue

    def stop(self):
        self._running = False
        for t in self._threads:
            t.join(timeout=2)


class KafkaEventBus(EventBus):
    def __init__(self):
        from kafka import KafkaProducer, KafkaConsumer

        self._producer = KafkaProducer(
            bootstrap_servers=cfg.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8"),
        )
        self._consumer = KafkaConsumer(
            bootstrap_servers=cfg.KAFKA_BOOTSTRAP_SERVERS,
            group_id=cfg.CONSUMER_GROUP,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            key_deserializer=lambda k: k.decode("utf-8"),
            auto_offset_reset="earliest",
        )
        self._subscriptions: dict[str, list[Callable]] = {}
        self._running = False

    def send(self, topic: str, key: str, value: dict):
        self._producer.send(topic, key=key, value=value)
        self._producer.flush()

    def subscribe(self, topic: str, callback: Callable[[str, dict], None]):
        self._consumer.subscribe([topic])
        self._subscriptions.setdefault(topic, []).append(callback)

    def start_consuming(self):
        self._running = True
        while self._running:
            msg_pack = self._consumer.poll(timeout_ms=cfg.POLL_TIMEOUT_MS)
            for topic_partition, messages in msg_pack.items():
                topic = topic_partition.topic
                for msg in messages:
                    for cb in self._subscriptions.get(topic, []):
                        cb(msg.key, msg.value)

    def stop(self):
        self._running = False
        self._producer.close()
        self._consumer.close()


def create_event_bus() -> EventBus:
    if cfg.MOCK_MODE:
        return MockEventBus()
    return KafkaEventBus()
