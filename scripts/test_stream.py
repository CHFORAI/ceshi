import json
import sys

import requests


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_stream.py <session_id>")
        raise SystemExit(2)
    sid = sys.argv[1]
    url = f"http://localhost:8000/api/chat/{sid}/stream"
    r = requests.post(url, json={"content": "按月份统计订单金额总和，生成折线图"}, stream=True, timeout=60)
    print("status", r.status_code)
    i = 0
    for raw in r.iter_lines(decode_unicode=True):
        if not raw:
            continue
        print(raw)
        i += 1
        if i >= 60:
            break


if __name__ == "__main__":
    main()

