#!/usr/bin/env python3
import ollama, sys, subprocess, datetime

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT).decode()
    except subprocess.CalledProcessError as e:
        return f"Error: {e.output.decode()}"

def screenshot():
    path = "/tmp/deathstar_screen.png"
    subprocess.run(f"grim {path}", shell=True)
    text = run_cmd(f"tesseract {path} stdout")
    return text

def ask(prompt):
    try:
        response = ollama.chat(model='phi3:mini', messages=[
            {'role': 'system', 'content': 'Ти агент Death Star OS для пентесту. Якщо просять виконати дію, поверни ТІЛЬКИ команду Linux, яку треба виконати.'},
            {'role': 'user', 'content': prompt}
        ])
        reply = response['message']['content']
        # Якщо відповідь схожа на команду — виконуємо в пісочниці
        if reply.strip().startswith(('nmap', 'ping', 'curl', 'gobuster', 'ffuf', 'sqlmap')):
            print(f"[*] Виконую команду: {reply.strip()}")
            output = run_cmd(f"firejail --profile=/etc/firejail/untrusted.profile {reply.strip()}")
            print(output)
        else:
            print(reply)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ask(" ".join(sys.argv[1:]))
    else:
        print("Вейдер активний. Команда: agent.py 'проскануй 127.0.0.1'")
