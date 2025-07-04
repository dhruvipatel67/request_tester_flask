from flask import Flask, render_template, request, jsonify
from cURL import CurlConverter
import requests
import threading
from flask import render_template_string
import time
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
stop_flag = False


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        curl_command = request.form["curl_command"]
        expected_text = request.form["expected_text"]
        iterations = int(request.form["iterations"])

        try:
            method, url, headers, data, json_data = CurlConverter(curl_command).convert()
        except Exception as e:
            return jsonify({"error": str(e)})

        results = []
        summary = {"success": 0, "fail": 0, "found": 0, "total": iterations}
        session = requests.Session()

        def send_request(i):
            nonlocal summary
            try:
                if method == "POST":
                    response = session.post(url, headers=headers, data=data, json=json_data)
                else:
                    response = session.get(url, headers=headers)

                content = response.text
                if expected_text.lower() in content.lower():
                    summary["success"] += 1
                    summary["found"] += 1
                    idx = content.lower().find(expected_text.lower())
                    preview = content[max(0, idx - 30): idx + len(expected_text) + 30]
                    return f"✅ Iteration {i}: Found at index {idx}\n...{preview}..."
                else:
                    summary["fail"] += 1
                    return f"❌ Iteration {i}: Not Found (Status {response.status_code})"

            except Exception as e:
                summary["fail"] += 1
                return f"⚠️ Iteration {i}: ERROR - {str(e)}"

        start = time.time()
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(send_request, i) for i in range(1, iterations + 1)]
            for f in futures:
                results.append(f.result())
        total_time = time.time() - start

        return jsonify({
            "results": results,
            "summary": summary,
            "time": f"{total_time:.2f} seconds"
        })

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


if __name__ == "__main__":
    app.run(debug=True)