import uuid
import threading
import time
import requests
from cURL import CurlConverter

tasks = {}

def start_background_task(curl_command, expected_text, iterations):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "done": 0,
        "total": iterations,
        "results": [],
        "summary": {"success": 0, "fail": 0, "found": 0, "total": iterations},
        "finished": False,
        "time": "0.00 seconds"
    }

    def run_task():
        try:
            method, url, headers, data, json_data = CurlConverter(curl_command).convert()
        except Exception as e:
            tasks[task_id]["error"] = str(e)
            tasks[task_id]["finished"] = True
            return

        session = requests.Session()
        summary = tasks[task_id]["summary"]
        results = tasks[task_id]["results"]
        start = time.time()

        for i in range(1, iterations + 1):
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
                    results.append(f"✅ Iteration {i}: Found at index {idx}\n...{preview}...")
                else:
                    summary["fail"] += 1
                    results.append(f"❌ Iteration {i}: Not Found (Status {response.status_code})")
            except Exception as e:
                summary["fail"] += 1
                results.append(f"⚠️ Iteration {i}: ERROR - {str(e)}")
            tasks[task_id]["done"] = i

        total_time = time.time() - start
        tasks[task_id]["finished"] = True
        tasks[task_id]["time"] = f"{total_time:.2f} seconds"

    threading.Thread(target=run_task).start()
    return task_id

def get_task_progress(task_id):
    return tasks.get(task_id)