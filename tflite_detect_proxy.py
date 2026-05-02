import cv2
import numpy as np
import requests
from flask import Flask, Response
import tflite_runtime.interpreter as tflite

MODEL = "/home/matt/follow_project/models/detect.tflite"
LABEL = "/home/matt/follow_project/models/labelmap.txt"

labels = {}
with open(LABEL) as f:
    for i, line in enumerate(f):
        labels[i] = line.strip()

interpreter = tflite.Interpreter(model_path=MODEL)
interpreter.allocate_tensors()

input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

h = input_details[0]["shape"][1]
w = input_details[0]["shape"][2]

app = Flask(__name__)

def detect(frame):
    img = cv2.resize(frame, (w, h))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = np.expand_dims(img, 0)

    interpreter.set_tensor(input_details[0]["index"], img)
    interpreter.invoke()

    boxes = interpreter.get_tensor(output_details[0]["index"])[0]
    classes = interpreter.get_tensor(output_details[1]["index"])[0]
    scores = interpreter.get_tensor(output_details[2]["index"])[0]

    for i in range(len(scores)):
        if scores[i] > 0.5:
            ymin, xmin, ymax, xmax = boxes[i]

            x1 = int(xmin * frame.shape[1])
            y1 = int(ymin * frame.shape[0])
            x2 = int(xmax * frame.shape[1])
            y2 = int(ymax * frame.shape[0])

            label = labels.get(int(classes[i]), "obj")

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, max(20, y1 - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
    return frame

@app.route("/")
def index():
    return """
    <html>
      <head><title>TFLite Detect Proxy</title></head>
      <body>
        <h2>TFLite Detect Proxy</h2>
        <p><a href="/health">health</a></p>
        <p><a href="/stream">stream</a></p>
        <img src="/stream" width="640">
      </body>
    </html>
    """

@app.route("/health")
def health():
    return "ok", 200

def gen():
    print("Connecting to upstream 8000 stream...")
    stream = requests.get("http://127.0.0.1:8000/stream", stream=True, timeout=10)
    print("Connected to upstream 8000 stream")

    bytes_data = b""

    for chunk in stream.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b"\xff\xd8")
        b = bytes_data.find(b"\xff\xd9")

        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]

            frame = cv2.imdecode(np.frombuffer(jpg, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                continue

            frame = detect(frame)

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                frame_bytes +
                b"\r\n"
            )

@app.route("/stream")
def stream():
    return Response(
        gen(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    print("AI stream on http://0.0.0.0:8001/")
    app.run(host="0.0.0.0", port=8001, threaded=True)