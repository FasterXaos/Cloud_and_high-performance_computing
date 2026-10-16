"""External entry point. Incoming HTTP is forwarded to the backend Service."""

import os

import requests
from flask import Flask, Response, jsonify, request

app = Flask(__name__)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://backend:8080").rstrip("/")
TIMEOUT = 5


@app.get("/health")
def health():
    return jsonify(status="ok", service="frontend")


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(path):
    url = f"{BACKEND_URL}/{path}"
    try:
        upstream = requests.request(
            method=request.method,
            url=url,
            params=request.args,
            data=request.get_data(),
            headers={
                key: value
                for key, value in request.headers
                if key.lower() not in ("host", "content-length")
            },
            timeout=TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        return jsonify(error="backend unreachable", detail=str(exc)), 502

    skipped = {"content-encoding", "content-length", "transfer-encoding", "connection"}
    headers = [
        (key, value)
        for key, value in upstream.headers.items()
        if key.lower() not in skipped
    ]
    headers.append(("X-Forwarded-By", "frontend"))
    return Response(upstream.content, upstream.status_code, headers)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
