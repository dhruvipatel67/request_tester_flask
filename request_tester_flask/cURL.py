import shlex
import json

class CurlConverter:
    def __init__(self, curl_command):
        self.curl_command = curl_command

    def convert(self):
        parsed = shlex.split(self.curl_command)
        method = "GET"
        url = ""
        headers = {}
        data = None
        json_data = None

        i = 0
        while i < len(parsed):
            part = parsed[i]
            if part.lower() == "curl":
                i += 1
                if i < len(parsed):
                    url = parsed[i]
            elif part in ["--url"]:
                i += 1
                url = parsed[i]
            elif part == "-X":
                i += 1
                method = parsed[i]
            elif part in ["-H", "--header"]:
                i += 1
                header_parts = parsed[i].split(":", 1)
                if len(header_parts) == 2:
                    headers[header_parts[0].strip()] = header_parts[1].strip()
            elif part in ["-d", "--data", "--data-raw", "--data-binary"]:
                i += 1
                data = parsed[i]
            i += 1

        # Remove unnecessary headers
        headers = {
            k: v for k, v in headers.items()
            if k.lower() not in ["if-modified-since", "if-none-match", "cache-control", "etag"]
        }

        # Detect if Content-Type is JSON and try to convert to dict
        content_type = headers.get("Content-Type", "").lower()
        if content_type == "application/json" and data:
            try:
                json_data = json.loads(data)
                data = None
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON format in -d flag")

        return method.upper(), url, headers, data, json_data
