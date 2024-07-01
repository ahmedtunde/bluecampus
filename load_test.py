# load_test_app/load_test_script.py
import threading
import requests
import time
import statistics

TARGET_URL = "https://demo.edves.net"
NUM_REQUESTS = 1000  # Increase the number of requests for a more aggressive test

# Lists to store response times and success/failure status
response_times = []
success_count = 0
failure_count = 0

def send_request():
    global success_count, failure_count

    start_time = time.time()
    try:
        response = requests.get(TARGET_URL)
        print(f"Request Status Code: {response.status_code}")
        success_count += 1
    except Exception as e:
        print(f"Error: {str(e)}")
        failure_count += 1
    finally:
        end_time = time.time()
        elapsed_time = end_time - start_time
        response_times.append(elapsed_time)

def simulate_bot_traffic():
    global success_count, failure_count
    print(f"Simulating {NUM_REQUESTS} aggressive bot requests to {TARGET_URL}")
    threads = []

    for _ in range(NUM_REQUESTS):
        thread = threading.Thread(target=send_request)
        threads.append(thread)

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    print("\nAggressive load testing completed.")
    print(f"Success count: {success_count}")
    print(f"Failure count: {failure_count}")

    if response_times:
        avg_response_time = statistics.mean(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)

        print(f"Average Response Time: {avg_response_time:.4f} seconds")
        print(f"Min Response Time: {min_response_time:.4f} seconds")
        print(f"Max Response Time: {max_response_time:.4f} seconds")

if __name__ == "__main__":
    start_time = time.time()
    simulate_bot_traffic()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"\nTotal elapsed time: {elapsed_time:.2f} seconds")