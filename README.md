# Tasks

## Basic cloud functionality

Browser [Arkanoid](https://github.com/FasterXaos/XArcanoid) with registration, sessions, and a leaderboard. 

## Fundamentals of containerization

Two containers on one Docker network: a PostgreSQL leaderboard for XArcanoid and an HTTP entry point. Runs live in a named volume and stay after the containers are restarted or recreated.

See [containerization/README.md](containerization/README.md).

## Kubernetes

A replicated backend behind a frontend that is reachable from outside the cluster.

See [kubernetes/README.md](kubernetes/README.md).

## Microservices

High-level design of XArcanoid Online: services, traffic and data estimates, and the patterns between them.

See [msa/README.md](msa/README.md).

## RabbitMQ

A producer publishes calculation tasks through a topic exchange. A consumer writes the result to its log and dead-letters failed operations.

See [rabbitmq/README.md](rabbitmq/README.md).
