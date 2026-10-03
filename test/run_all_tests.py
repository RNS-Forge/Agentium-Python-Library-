import os
import sys
import subprocess

# Set stdout encoding to utf-8 if possible
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_suite():
    test_dir = os.path.dirname(os.path.abspath(__file__))
    test_files = [
        "test_condenser.py",
        "test_optimizer.py",
        "test_rearranger.py",
        "test_extractor.py",
        "test_communicator.py",
        "test_translator.py",
        "test_insight_generator.py",
        "test_workflow_helper.py",
        "test_template_manager.py",
        "test_memory_helper.py",
        "test_summarizer.py",
        "test_logger_utils.py",
        "test_agentium_facade.py",
        "test_ai_env.py",
    ]
    
    print("=" * 60)
    print("RUNNING ALL INDIVIDUAL AGENTIUM MODULE TESTS")
    print("=" * 60)
    
    results = {}
    for tf in test_files:
        path = os.path.join(test_dir, tf)
        if not os.path.exists(path):
            continue
        print(f"\n>> Running {tf}...")
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        proc = subprocess.run([sys.executable, path], capture_output=True, text=True, env=env)
        if proc.returncode == 0:
            print(f"[PASS] {tf}")
            results[tf] = "PASSED"
        else:
            print(f"[FAIL] {tf}")
            print(proc.stderr or proc.stdout)
            results[tf] = "FAILED"
            
    print("\n" + "=" * 60)
    print("FINAL TEST SUITE REPORT")
    print("=" * 60)
    passed_count = sum(1 for status in results.values() if status == "PASSED")
    for tf, status in results.items():
        flag = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"{flag} {tf:28} : {status}")
    print(f"\nTotal: {passed_count}/{len(results)} tests passed.")
    print("=" * 60)

if __name__ == "__main__":
    run_suite()
