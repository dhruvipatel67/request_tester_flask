import uuid
from flask import Flask, render_template, request, jsonify, render_template_string
from cURL import CurlConverter
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from method import run_iterations
from progressbar import start_background_task, get_task_progress

app = Flask(__name__)
tasks = {}


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        curl_command = request.form["curl_command"]
        expected_text = request.form["expected_text"]
        iterations = int(request.form["iterations"])
        result = run_iterations(curl_command, expected_text, iterations)
        return jsonify(result)
    return render_template("index.html")


@app.route("/snippet", methods=["POST"])
def snippet():
    curl_command = request.form.get("curl_command", "").strip()
    expected_text = request.form.get("expected_text", "").strip()

    try:
        method, url, headers, data, extra = CurlConverter(curl_command).convert()

    except Exception as e:
        return f"<h3>Error parsing cURL: {str(e)}</h3>"

    code = f'''import requests
import time

url = {repr(url)}
headers = {headers or '{}'}
{f"data = {repr(data)}" if data else ""}
expected_text = {repr(expected_text)}

print("Sending request...")

start_time = time.time()

try:
    response = requests.{method.lower()}(url, headers=headers{', data=data' if data else ''})
    end_time = time.time()
    elapsed = end_time - start_time

    print("Status Code:", response.status_code)

    if expected_text.lower() in response.text.lower():
        print(" Found expected text!")
    else:
        print(" Expected text not found.")

    print(f"Response received in {{elapsed:.2f}} seconds")

except Exception as e:
    print(" Request failed:", str(e))


'''

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <title>Generated Python Snippet</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script>hljs.highlightAll();</script>
    <style>
        body {
            background: #f5f7fb;
            font-family: 'Segoe UI', sans-serif;
            padding: 20px;
        }
        pre {
            padding: 15px;
            border-radius: 8px;
            background-color: #f8f9fa;
            border: 1px solid #ccc;
        }
        .copy-btn {
            position: absolute;
            top: 15px;
            right: 20px;
        }
    </style>
</head>
<body>
    <div class="container">

        <div class="position-relative">
            <button class="btn btn-sm btn-outline-secondary copy-btn" onclick="copyToClipboard()">📋 Copy</button>
            <pre><code class="language-python" id="codeBlock">{{ code }}</code></pre>
        </div>
    </div>

    <script>
        function copyToClipboard() {
            const text = document.getElementById("codeBlock").innerText;
            navigator.clipboard.writeText(text).then(() => {
                alert("✅ Code copied to clipboard!");
            });
        }
    </script>
</body>
</html>
""", code=code)


@app.route("/start_task", methods=["POST"])
def start_task():
    curl_command = request.form["curl_command"]
    expected_text = request.form["expected_text"]
    iterations = int(request.form["iterations"])
    task_id = start_background_task(curl_command, expected_text, iterations)
    return jsonify({"task_id": task_id})


@app.route("/progress/<task_id>")
def progress(task_id):
    task = get_task_progress(task_id)
    if not task:
        return jsonify({"error": "Task not found"}), 404
    resp = {
        "done": task["done"],
        "total": task["total"],
        "results": task.get("results", []),
        "summary": task.get("summary", {}),
        "finished": task.get("finished", False),
        "time": task.get("time", "0.00 seconds")
    }
    return jsonify(resp)


if __name__ == "__main__":
    app.run(debug=True)