import os
import sys
import time
import re
import pyperclip
import subprocess

# --------- Configuration ---------
QA_FILE = "p.txt"
DETACHED_PROCESS = 0x00000008
PID_FILE = "p.pid"  # store background process ID
# ---------------------------------

def clean_text(text):
    """Normalize text for exact comparison: lowercase and single spaces."""
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_qa_pairs(filename):
    """Load Q&A pairs from a text file."""
    if not os.path.exists(filename):
        print(f"❌ File not found: {filename}")
        return []

    with open(filename, 'r', encoding='utf-8') as file:
        content = file.read()
        entries = content.split('---')
        qa_pairs = []
        for entry in entries:
            match = re.search(r'Q:\s*(.*?)\s*A:\s*(.*)', entry, re.DOTALL)
            if match:
                question = clean_text(match.group(1))
                answer = match.group(2).strip()
                qa_pairs.append((question, answer))
        return qa_pairs

def get_answer(input_question, qa_pairs):
    """Return the answer if an exact match (case-insensitive) is found."""
    cleaned_input = clean_text(input_question)
    for q, a in qa_pairs:
        if cleaned_input == q:  # exact match only
            return a
    return None  # No match found

def monitor_clipboard():
    """Continuously monitor clipboard and copy answer if found."""
    qa_data = load_qa_pairs(QA_FILE)
    if not qa_data:
        return

    last_clipboard = ""
    print("📋 Clipboard monitor running... (use `python p.py stop` to quit)")

    while True:
        clipboard_data = pyperclip.paste()
        cleaned_clipboard = clean_text(clipboard_data)

        if cleaned_clipboard and cleaned_clipboard != last_clipboard:
            answer = get_answer(clipboard_data, qa_data)
            if answer:  # Only overwrite if exact match is found
                pyperclip.copy(answer)
            last_clipboard = cleaned_clipboard

        time.sleep(1)

def start_background_process():
    """Start a detached background process and save its PID."""
    process = subprocess.Popen(
        [sys.executable, __file__, "--background"],
        creationflags=DETACHED_PROCESS,
        close_fds=True
    )
    with open(PID_FILE, "w") as f:
        f.write(str(process.pid))
    print(f"✅ Clipboard monitor started in background (PID {process.pid}). You can close this window.")

def stop_background():
    """Stop the background process using the saved PID."""
    if not os.path.exists(PID_FILE):
        print("❌ No running background process found.")
        return
    with open(PID_FILE, "r") as f:
        pid = int(f.read())
    try:
        subprocess.run(["taskkill", "/F", "/PID", str(pid)],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"🛑 Clipboard monitor (PID {pid}) stopped.")
    except Exception as e:
        print(f"❌ Failed to stop process: {e}")
    finally:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)

if __name__ == "__main__":
    if "--background" in sys.argv:
        monitor_clipboard()
    elif "stop" in sys.argv:
        stop_background()
    else:
        start_background_process()
