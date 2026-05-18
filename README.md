#!/usr/bin/env python3
import ollama, sys, subprocess, threading, os, time

STATUS_FILE = "/tmp/deathstar_ai_status"
MODEL = "phi3:mini"

def update_status(text):
    with open(STATUS_FILE, "w") as f:
        f.write(text)

def run_async(cmd):
    """Виконує команду в окремому потоці, оновлює статус"""
    def worker():
        update_status(f"⚡ {cmd[:60]}")
        try:
            # Запускаємо з обмеженням навантаження (nice 10) та в пісочниці
            proc = subprocess.Popen(
                f"nice -n 10 firejail --profile=/etc/firejail/untrusted.profile {cmd}",
                shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            out, _ = proc.communicate()
            # Якщо потрібно показати вивід — пишемо в лог, а не в термінал
            with open("/tmp/deathstar_ai_output.log", "ab") as log:
                log.write(out)
            update_status("🌑 Готовий")
        except Exception as e:
            update_status(f"❌ Помилка: {str(e)[:40]}")
    threading.Thread(target=worker, daemon=True).start()

def query_agent(prompt):
    update_status("🤔 Думаю...")
    system_msg = (
        "Ти агент Death Star OS. Твоя єдина відповідь — команда Linux, яку треба виконати. "
        "Не пояснюй, не коментуй. Якщо просять запустити термінал з програмою — використовуй 'kitty -e <команда>'. "
        "Мова відповіді — англійська або українська команда."
    )
    try:
        response = ollama.chat(model=MODEL, messages=[
            {'role': 'system', 'content': system_msg},
            {'role': 'user', 'content': prompt}
        ])
        cmd = response['message']['content'].strip()
        # Якщо відповідь містить пояснення, витягаємо лише команду
        if not cmd.startswith(('kitty', 'alacritty', 'xfce4-terminal', 'gnome-terminal',
                              'nmap', 'ping', 'curl', 'gobuster', 'ffuf', 'sqlmap',
                              'echo', 'ls', 'cat', 'mkdir', 'rm', 'cp', 'mv',
                              'hyprctl', 'systemctl', 'fastfetch', 'neofetch', 'export')):
            # Пробуємо знайти команду в першому рядку
            lines = cmd.split('\n')
            for l in lines:
                if l.startswith(('kitty', 'nmap', 'ping', 'curl', 'fastfetch')):
                    cmd = l
                    break
        print(f"[*] Виконую: {cmd}")
        run_async(cmd)
    except Exception as e:
        update_status(f"❌ Помилка моделі: {str(e)[:40]}")
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_agent(" ".join(sys.argv[1:]))
    else:
        print("Вейдер активний. Приклад: agent.py 'відкрий термінал з fastfetch'")
