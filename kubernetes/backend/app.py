"""Internal API. Each replica answers with its own pod name."""

import os

from flask import Flask, jsonify

app = Flask(__name__)
REPLICA = os.environ.get("HOSTNAME", "unknown")


@app.get("/health")
def health():
    return jsonify(status="ok", service="backend", replica=REPLICA)


@app.get("/")
def root():
    return jsonify(
        service="backend",
        replica=REPLICA,
        message="request received",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
