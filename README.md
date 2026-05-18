#!/usr/bin/env python3
import ollama, sys, subprocess, threading, os, time

STATUS_FILE = "/tmp/deathstar_ai_status"
MODEL = "phi3:mini"

def update_status(text):
    with open(STATUS_FILE, "w") as f:
        f.write(text)

def run_gui(cmd):
    """Запускає GUI-додаток без пісочниці (але з nice)"""
    def worker():
        update_status(f"🖥️ {cmd[:50]}")
        try:
            env = os.environ.copy()
            subprocess.Popen(cmd, shell=True, env=env,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            # GUI-програма запустилась, вона сама живе
            time.sleep(1)
            update_status("🌑 Готовий")
        except Exception as e:
            update_status(f"❌ Помилка: {str(e)[:30]}")
    threading.Thread(target=worker, daemon=True).start()

def run_cli(cmd):
    """Запускає термінальну команду в пісочниці"""
    def worker():
        update_status(f"⚡ {cmd[:50]}")
        try:
            proc = subprocess.Popen(
                f"nice -n 10 firejail --profile=/etc/firejail/untrusted.profile {cmd}",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            out, _ = proc.communicate()
            with open("/tmp/deathstar_ai_output.log", "ab") as log:
                log.write(out)
            update_status("🌑 Готовий")
        except Exception as e:
            update_status(f"❌ Помилка: {str(e)[:30]}")
    threading.Thread(target=worker, daemon=True).start()

def query_agent(prompt):
    update_status("🤔 Думаю...")
    system_msg = (
        "Ти агент Death Star OS. Відповідай ТІЛЬКИ командою Linux, яку треба виконати. "
        "Не пояснюй, не коментуй. "
        "Якщо просять відкрити термінал з програмою — використовуй 'kitty -e <програма>'. "
        "Мова — англійська або українська команда."
    )
    try:
        response = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': prompt}
        ])
        cmd = response['message']['content'].strip()
        print(f"[*] Отримано команду: {cmd}")

        # Визначаємо, чи GUI
        if any(cmd.startswith(g) for g in ['kitty', 'alacritty', 'xfce4-terminal', 'gnome-terminal', 'thunar', 'firefox']):
            run_gui(cmd)
        else:
            run_cli(cmd)
    except Exception as e:
        update_status(f"❌ Помилка моделі: {str(e)[:40]}")
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_agent(" ".join(sys.argv[1:]))
    else:
        print("Вейдер активний. Приклад: agent.py 'відкрий термінал з fastfetch'")
