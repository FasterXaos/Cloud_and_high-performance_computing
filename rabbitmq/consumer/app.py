"""Apply the operation named by the routing key. Failures go to the DLQ."""

import json
import os
import time

import pika

RABBITMQ_URL = os.environ.get("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")


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
    channel.exchange_declare(exchange="calc", exchange_type="topic", durable=True)
    channel.exchange_declare(exchange="calc.dlx", exchange_type="fanout", durable=True)
    channel.queue_declare(queue="calc.dlq", durable=True)
    channel.queue_bind(queue="calc.dlq", exchange="calc.dlx")
    channel.queue_declare(
        queue="calc.tasks",
        durable=True,
        arguments={"x-dead-letter-exchange": "calc.dlx"},
    )
    channel.queue_bind(queue="calc.tasks", exchange="calc", routing_key="calc.*")


def apply_op(op, left, right):
    if op == "add":
        return left + right
    if op == "sub":
        return left - right
    if op == "mul":
        return left * right
    if op == "div":
        if right == 0:
            raise ZeroDivisionError("division by zero")
        return left / right
    raise ValueError(f"unknown operation {op}")


def on_message(channel, method, _properties, body):
    op = method.routing_key.rsplit(".", 1)[-1]
    try:
        payload = json.loads(body.decode())
        left = payload["a"]
        right = payload["b"]
        if isinstance(left, bool) or isinstance(right, bool):
            raise TypeError("a and b must be numbers")
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise TypeError("a and b must be numbers")
        result = apply_op(op, left, right)
    except (KeyError, TypeError, ValueError, ZeroDivisionError, json.JSONDecodeError) as exc:
        print(
            f"fail routing_key={method.routing_key} body={body.decode(errors='replace')} error={exc} -> dlq",
            flush=True,
        )
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    print(
        f"ok routing_key={method.routing_key} a={left} b={right} result={result}",
        flush=True,
    )
    channel.basic_ack(delivery_tag=method.delivery_tag)


def main():
    connection = connect()
    channel = connection.channel()
    declare(channel)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue="calc.tasks", on_message_callback=on_message)
    print("waiting for calc.*", flush=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()
