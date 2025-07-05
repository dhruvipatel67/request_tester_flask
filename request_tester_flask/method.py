import requests
from concurrent.futures import ThreadPoolExecutor
import time
from cURL import CurlConverter

def run_iterations(curl_command, expected_text, iterations):
    try:
        method, url, headers, data, json_data = CurlConverter(curl_command).convert()
    except Exception as e:
        return {"error": str(e)}

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

    return {
        "results": results,
        "summary": summary,
        "time": f"{total_time:.2f} seconds"
    }