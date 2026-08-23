import time
import urllib.request
import json
from flask import Flask, jsonify

app = Flask(__name__)

STATUS_URL = "http://127.0.0.1:8080/status"


@app.route("/data")
def data():
    try:
        with urllib.request.urlopen(STATUS_URL, timeout=0.2) as r:
            s = json.loads(r.read())

        return jsonify({
            "time": time.monotonic(),
            "command": float(s["yaw"])
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    return """
<!DOCTYPE html>
<html>
<body style="background:#111;color:white;font-family:Arial">

<h2>Yaw Command</h2>

<canvas id="c" width="1000" height="500"
style="border:1px solid #555;background:#181818"></canvas>

<h3 id="value">Command: --</h3>

<script>
const c = document.getElementById("c");
const ctx = c.getContext("2d");

let data = [];
let start = null;

async function update() {
    try {
        const r = await fetch("/data");
        const d = await r.json();

        if (d.error) return;

        if (start === null) start = d.time;

        data.push({
            t: d.time - start,
            y: d.command
        });

        if (data.length > 300)
            data.shift();

        document.getElementById("value").innerText =
            "Command: " + d.command.toFixed(2) + " deg/s";

        draw();

    } catch(e) {}
}


function draw() {

    const W = c.width;
    const H = c.height;

    ctx.clearRect(0, 0, W, H);

    // 固定显示 -30 到 +30
    const MIN = -30;
    const MAX = 30;

    // zero line
    const zeroY = H / 2;

    ctx.strokeStyle = "#555";
    ctx.beginPath();
    ctx.moveTo(50, zeroY);
    ctx.lineTo(W - 20, zeroY);
    ctx.stroke();

    // labels
    ctx.fillStyle = "white";
    ctx.font = "14px Arial";

    ctx.fillText("+30", 10, 20);
    ctx.fillText("0", 20, zeroY);
    ctx.fillText("-30", 10, H - 10);

    if (data.length < 2)
        return;

    const minT = data[0].t;
    const maxT = data[data.length - 1].t;

    ctx.strokeStyle = "#00ff88";
    ctx.lineWidth = 2;
    ctx.beginPath();

    for (let i = 0; i < data.length; i++) {

        const x =
            50 +
            ((data[i].t - minT) /
            Math.max(0.001, maxT - minT)) *
            (W - 70);

        const y =
            H -
            ((data[i].y - MIN) /
            (MAX - MIN)) *
            H;

        if (i === 0)
            ctx.moveTo(x, y);
        else
            ctx.lineTo(x, y);
    }

    ctx.stroke();
}

setInterval(update, 100);
</script>

</body>
</html>
"""


if __name__ == "__main__":
    print("Command monitor running on port 8090")
    app.run(host="0.0.0.0", port=8090)