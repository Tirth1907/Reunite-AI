import subprocess

def run_test(script_name):
    print(f"Running {script_name}...")
    result = subprocess.run([r"..\.venv\Scripts\python.exe", script_name], capture_output=True, text=True, encoding="utf-8")
    with open(f"{script_name}_output.log", "w", encoding="utf-8") as f:
        f.write("STDOUT:\n")
        f.write(result.stdout)
        f.write("\nSTDERR:\n")
        f.write(result.stderr)
        f.write(f"\nReturn Code: {result.returncode}\n")

run_test("test_speed.py")
run_test("test_registration.py")
print("Done.")
