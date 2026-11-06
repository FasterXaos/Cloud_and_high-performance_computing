"""Publish calculation tasks on a topic exchange."""

import json
import os
import random
import time

import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE = "calc"
INTERVAL = float(os.environ.get("INTERVAL", "2"))
OPS = ("add", "sub", "mul", "div")


def connect():
    for attempt in range(1, 31):
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            params.heartbeat = 30
            connection = pika.BlockingConnection(params)
            print(f"broker is ready (attempt {attempt})", flush=True)
            return connection
        except pika.exceptions.AMQPConnectionError as exc:
            print(f"waiting for broker ({attempt}/30): {exc}", flush=True)
            time.sleep(2)
    raise SystemExit("broker did not become ready")


def declare(channel):
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange="calc.dlx", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="calc.dlq", durable=True)
    channel.queue_bind(queue="calc.dlq", exchange="calc.dlx")
    channel.queue_declare(
        queue="calc.tasks",
        durable=True,
        arguments={"x-dead-letter-exchange": "calc.dlx"},
    )
    channel.queue_bind(queue="calc.tasks", exchange=EXCHANGE, routing_key="calc.*")


def main():
    connection = connect()
    channel = connection.channel()
    declare(channel)
    sent = 0
    while True:
        op = OPS[sent % len(OPS)]
        # Every other division is by zero so the consumer can show the DLQ path.
        bad = op == "div" and (sent // len(OPS)) % 2 == 0
        payload = {"a": random.randint(1, 20), "b": 0 if bad else random.randint(1, 9)}
        routing_key = f"calc.{op}"
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=json.dumps(payload).encode(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,
            ),
        )
        print(f"sent routing_key={routing_key} {payload}", flush=True)
        sent += 1
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
