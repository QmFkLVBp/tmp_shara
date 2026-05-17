#!/usr/bin/env python3
import ollama, sys, subprocess, threading, time

STATUS_FILE = "/tmp/deathstar_ai_status"

def update_status(text):
    with open(STATUS_FILE, "w") as f:
        f.write(text)

def run_cmd(cmd):
    """Виконує команду в пісочниці та повертає вивід"""
    update_status(f"⚡ {cmd[:60]}")
    try:
        output = subprocess.check_output(
            f"firejail --profile=/etc/firejail/untrusted.profile {cmd}",
            shell=True, stderr=subprocess.STDOUT
        ).decode()
        update_status("🌑 Готовий")
        return output
    except subprocess.CalledProcessError as e:
        update_status("❌ Помилка")
        return f"Помилка: {e.output.decode()}"

def query_agent(prompt):
    """Запит до LLM, витяг команди та виконання"""
    update_status("🤔 Думаю...")
    response = ollama.chat(model='phi3:mini', messages=[
        {'role': 'system', 'content': 'Ти агент Death Star OS. Відповідай ТІЛЬКИ командою Linux, яку треба виконати. Якщо не можеш - поясни коротко.'},
        {'role': 'user', 'content': prompt}
    ])
    reply = response['message']['content'].strip()
    
    # Якщо відповідь схожа на команду (починається з типових утиліт або містить /)
    if reply.startswith(('kitty', 'alacritty', 'xfce4-terminal', 'gnome-terminal',
                         'nmap', 'ping', 'curl', 'gobuster', 'ffuf', 'sqlmap',
                         'echo', 'ls', 'cat', 'mkdir', 'rm', 'cp', 'mv',
                         'hyprctl', 'systemctl', 'fastfetch', 'neofetch')) \
       or '/' in reply:
        print(f"[*] Виконую: {reply}")
        out = run_cmd(reply)
        print(out)
    else:
        # Якщо це не команда – просто показуємо відповідь
        print(reply)
        update_status("🌑 Готовий")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_agent(" ".join(sys.argv[1:]))
    else:
        print("Вейдер активний. Приклад: agent.py 'запусти термінал з fastfetch'")
