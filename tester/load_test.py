import requests
import time

url = "http://127.0.0.1:8000/ivr/start"

def load_test(n=20):
    start = time.time()

    for i in range(n):
        res = requests.post(
            url,
            json={"caller_number": "test_user"}
        )

        if res.status_code != 200:
            print("Error:", res.status_code)

    total = time.time() - start
    print(f"Sent {n} requests")
    print(f"Avg response time: {total/n:.2f} sec")

if __name__ == "__main__":
    load_test(20)