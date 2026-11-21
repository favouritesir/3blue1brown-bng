"""
Bangla Resource Factory - System Resource Governor & Agent Throttler
Prevents machine crashes, monitors CPU, RAM, and Network usage,
and dynamically regulates agent concurrency and task dispatching.
"""
import os
import sys
import time
import json
import psutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATUS_FILE = BASE_DIR / "governance" / "system_health.json"

# Safety Thresholds
MAX_RAM_PERCENT = 82.0      # Pause or slow down if RAM exceeds 82%
MAX_CPU_PERCENT = 85.0      # Back off if CPU exceeds 85%
MIN_FREE_RAM_GB = 2.5       # Require at least 2.5 GB free RAM for heavy media tasks
HEAVY_PROCESS_NAMES = ["ffmpeg.exe", "ffprobe.exe", "python.exe", "node.exe"]


def get_system_metrics():
    mem = psutil.virtual_memory()
    cpu_pct = psutil.cpu_percent(interval=0.5)
    
    # Process load
    heavy_procs = 0
    for p in psutil.process_iter(['name']):
        try:
            if p.info['name'] and p.info['name'].lower() in HEAVY_PROCESS_NAMES:
                heavy_procs += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    free_ram_gb = round(mem.available / (1024 ** 3), 2)
    total_ram_gb = round(mem.total / (1024 ** 3), 2)
    ram_pct = mem.percent

    # Determine load tier
    if ram_pct > MAX_RAM_PERCENT or cpu_pct > MAX_CPU_PERCENT or free_ram_gb < MIN_FREE_RAM_GB:
        safety_tier = "THROTTLED"
        can_run_heavy_tasks = False
        recommended_max_concurrency = 1
        status_message = "উচ্চ সিস্টেম চাপ শনাক্ত হয়েছে। ভারী কাজ সাময়িকভাবে ধীর করা হচ্ছে।"
    elif ram_pct > 70.0 or cpu_pct > 65.0:
        safety_tier = "MODERATE"
        can_run_heavy_tasks = True
        recommended_max_concurrency = 2
        status_message = "সিস্টেম পরিমিত লোডে রয়েছে। নিয়মিত কাজ চলমান।"
    else:
        safety_tier = "OPTIMAL"
        can_run_heavy_tasks = True
        recommended_max_concurrency = 4
        status_message = "সিস্টেম শতভাগ সুস্থ ও দ্রুতগতিতে প্রস্তুত।"

    metrics = {
        "timestamp": time.time(),
        "safety_tier": safety_tier,
        "can_run_heavy_tasks": can_run_heavy_tasks,
        "recommended_max_concurrency": recommended_max_concurrency,
        "status_message": status_message,
        "cpu_percent": cpu_pct,
        "ram_percent": ram_pct,
        "free_ram_gb": free_ram_gb,
        "total_ram_gb": total_ram_gb,
        "heavy_processes_count": heavy_procs
    }
    
    # Save to status file
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Warning: Could not save system status file: {e}")

    return metrics


def check_and_wait_if_overloaded(task_name="Heavy Task", timeout_sec=120):
    """
    Called before heavy jobs (video rendering, large TTS batch, browser automation).
    Waits proactively until system resource levels drop into safe territory.
    """
    start_t = time.time()
    while True:
        m = get_system_metrics()
        if m["can_run_heavy_tasks"]:
            return True
        
        if time.time() - start_t > timeout_sec:
            print(f"Governor warning: Task '{task_name}' proceeding after timeout.")
            return False
            
        print(f"[Resource Governor] High load: RAM {m['ram_percent']}%, CPU {m['cpu_percent']}%. Backing off 3s before '{task_name}'...")
        time.sleep(3)


if __name__ == "__main__":
    m = get_system_metrics()
    print("=== BANGLA RESOURCE FACTORY: SYSTEM GOVERNOR ===")
    print(f"Status Tier        : {m['safety_tier']}")
    print(f"CPU Usage          : {m['cpu_percent']}%")
    print(f"RAM Usage          : {m['ram_percent']}% (Free: {m['free_ram_gb']} GB / {m['total_ram_gb']} GB)")
    print(f"Heavy Processes    : {m['heavy_processes_count']}")
    print(f"Heavy Tasks Allowed: {m['can_run_heavy_tasks']}")
    print(f"Max Concurrency    : {m['recommended_max_concurrency']}")
    print(f"Message            : {m['status_message']}")
    print(f"Status logged to   : {STATUS_FILE}")
