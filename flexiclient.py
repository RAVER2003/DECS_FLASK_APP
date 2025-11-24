import socket
import time
import threading
import statistics
import random
import matplotlib.pyplot as plt
from InquirerPy import inquirer

HOST = "192.168.38.79"
PORT = 8080

# ----------------------------
# Load Generator Settings
# ----------------------------
START_THREADS = 10
END_THREADS = 300
STEP = 20
STAGE_DURATION = 5

MODE = "cold"   # hot or cold
REQ_TYPE = "GET"
# ----------------------------


# ---------- KEY GENERATOR ----------
def random_key():
    if MODE == "hot":
        i = random.randint(1, 5000)
    else:
        i = random.randint(1, 1_000_000)
    return f"key{i:07d}"


# ---------- WORKER THREAD ----------
def worker(stop_flag, latencies, req_type):
    s = socket.socket()
    s.connect((HOST, PORT))
    s.settimeout(3)

    while not stop_flag["stop"]:
        key = random_key()

        if req_type == "GET":
            cmd = f"GET {key}\n"
        else:
            value = f"val{random.randint(1,999999)}"
            cmd = f"PUT {key} {value}\n"

        start = time.time()
        try:
            s.sendall(cmd.encode())
            s.recv(4096)
        except:
            continue
        end = time.time()

        latencies.append((end - start) * 1000)

    s.close()


# ---------- RUN A SINGLE STAGE ----------
def run_stage(thread_count, req_type):

    print(f"\n==============================")
    print(f"Running stage: {thread_count} threads ({req_type})")
    print(f"==============================")

    latencies = []
    stop_flag = {"stop": False}
    threads = []

    for _ in range(thread_count):
        t = threading.Thread(target=worker, args=(stop_flag, latencies, req_type))
        t.start()
        threads.append(t)

    time.sleep(STAGE_DURATION)
    stop_flag["stop"] = True

    for t in threads:
        t.join()

    if len(latencies) == 0:
        print("ERROR: no responses")
        return {"thr": 0, "avg": 0, "p95": 0}

    lat_sorted = sorted(latencies)
    thr = len(latencies) / STAGE_DURATION
    avg = statistics.mean(latencies)
    p95 = lat_sorted[int(0.95 * len(lat_sorted))]

    print(f"Requests: {len(latencies)}")
    print(f"Throughput: {thr:.2f} req/s")
    print(f"Avg latency: {avg:.2f} ms")
    print(f"P95 latency: {p95:.2f} ms")

    return {"thr": thr, "avg": avg, "p95": p95}


# -----------------------------------------------------
#               LOAD GENERATOR MAIN
# -----------------------------------------------------
def load_generator():
    global REQ_TYPE

    req_type = inquirer.select(
        message="Select request type:",
        choices=["GET", "PUT"],
        default="GET",
    ).execute()

    REQ_TYPE = req_type

    print(f"\nRunning load generator with: {REQ_TYPE}\n")

    thread_counts = list(range(START_THREADS, END_THREADS + 1, STEP))
    throughputs = []
    avg_latencies = []
    p95_latencies = []

    for tc in thread_counts:
        result = run_stage(tc, REQ_TYPE)
        throughputs.append(result["thr"])
        avg_latencies.append(result["avg"])
        p95_latencies.append(result["p95"])

    # ---------- PLOTS ----------
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.plot(thread_counts, throughputs, marker="o")
    plt.title("Throughput vs Threads")
    plt.xlabel("Threads")
    plt.ylabel("Throughput (req/sec)")
    plt.grid(True)

    plt.subplot(1, 2, 2)
    plt.plot(thread_counts, avg_latencies, marker="o", label="Avg Lat")
    plt.plot(thread_counts, p95_latencies, marker="o", label="P95")
    plt.title("Latency vs Threads")
    plt.xlabel("Threads")
    plt.ylabel("Latency (ms)")
    plt.grid(True)
    plt.legend()

    plt.tight_layout()
    plt.show()


# -----------------------------------------------------
#               NORMAL QUERY MODE (REPL)
# -----------------------------------------------------
def query_mode():

    print("Connected to KV-store terminal (type 'exit' to quit)\n")

    s = socket.socket()
    s.connect((HOST, PORT))
    s.settimeout(3)

    while True:
        cmd = input("kvdb> ").strip()

        if cmd == "" or cmd == "\n":
            continue

        if cmd.lower() in ("exit", "quit"):
            break

        try:
            s.sendall((cmd + "\n").encode())
            resp = s.recv(4096).decode()
            print(resp.strip())
        except Exception as e:
            print("Error:", e)

    s.close()


# -----------------------------------------------------
#                   MAIN ENTRY WITH MENU
# -----------------------------------------------------
if __name__ == "__main__":

    choice = inquirer.select(
        message="Choose mode:",
        choices=[
            "Load Generator",
            "Query Mode",
            "Exit"
        ],
        default="Load Generator",
    ).execute()

    if choice == "Load Generator":
        load_generator()

    elif choice == "Query Mode":
        query_mode()

    else:
        print("Goodbye!")
