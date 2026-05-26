#!/usr/bin/env python3
import sys, os, subprocess, threading, time, re, datetime
from llama_cpp import Llama

STATUS_FILE = "/tmp/deathstar_ai_status"
MODEL_PATH = os.path.expanduser("~/deathstar-agent/tinyllama.gguf")
VAULT_PATH = os.path.expanduser("~/obsidian-vault")
MEMORY_FILE = os.path.join(VAULT_PATH, "AGENTS.md")

# Завантажуємо модель
print("[*] Завантажую модель...", file=sys.stderr)
llm = Llama(model_path=MODEL_PATH, n_gpu_layers=20, n_ctx=1024, verbose=False)

def update_status(text):
    with open(STATUS_FILE, "w") as f:
        f.write(text)

def read_memory():
    """Читає AGENTS.md та останні нотатки з vault"""
    memory_context = ""
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory_context = f.read()

    # Додаємо останні 5 змінених нотаток
    try:
        result = subprocess.run(
            f"find {VAULT_PATH}/memory -name '*.md' -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -5 | cut -d' ' -f2-",
            shell=True, capture_output=True, text=True
        )
        for note in result.stdout.strip().split('\n'):
            if note and os.path.exists(note):
                with open(note, "r") as f:
                    memory_context += f"\n\n---\n{f.read()[:500]}"
    except:
        pass

    return memory_context[:3000]  # Обмежуємо контекст

def write_to_memory(title, content, tags=None):
    """Створює нову нотатку в vault"""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    filename = f"{title.lower().replace(' ', '-')}.md"
    filepath = os.path.join(VAULT_PATH, "memory", filename)

    with open(filepath, "w") as f:
        f.write("---\n")
        f.write(f"title: {title}\n")
        f.write(f"created: {timestamp}\n")
        if tags:
            f.write(f"tags: {tags}\n")
        f.write("---\n\n")
        f.write(f"# {title}\n\n")
        f.write(content)

    # Оновлюємо індекс
    index_path = os.path.join(VAULT_PATH, "memory", "index.md")
    if os.path.exists(index_path):
        with open(index_path, "a") as f:
            f.write(f"\n- [[{title}]] ({timestamp})")

def extract_command(text):
    """Витягує команду з відповіді"""
    patterns = [
        r'(kitty\s+-e\s+.+)', r'(alacritty\s+-e\s+.+)',
        r'(nmap\s+.+)', r'(ping\s+.+)', r'(curl\s+.+)',
        r'(echo\s+.+)', r'(ls\s+.+)', r'(cat\s+.+)',
        r'(mkdir\s+.+)', r'(rm\s+.+)', r'(fastfetch.*)'
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            return match.group(1)
    return None

def query_agent(prompt):
    update_status("🤔 Думаю...")
    memory = read_memory()

    system_msg = (
        "Ти — агент Death Star OS. У тебе є доступ до Obsidian vault пам'яті.\n"
        f"Поточна пам'ять:\n{memory}\n\n"
        "Відповідай ТІЛЬКИ командою Linux без пояснень.\n"
        "Якщо просять термінал — 'kitty -e <програма>'.\n"
        "Якщо потрібно запам'ятати щось важливе — додай 'REMEMBER: <заголовок> | <зміст>'.\n"
        "Мова — англійська або українська команда."
    )

    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1,
        max_tokens=256
    )

    full_reply = output['choices'][0]['message']['content'].strip()

    # Перевіряємо, чи є команда "REMEMBER"
    if "REMEMBER:" in full_reply.upper():
        try:
            parts = full_reply.split("REMEMBER:", 1)[1].strip()
            if "|" in parts:
                title, content = parts.split("|", 1)
                write_to_memory(title.strip(), content.strip(), "agent-generated")
                update_status("📝 Запам'ятав")
        except:
            pass

    cmd = extract_command(full_reply)
    if cmd:
        print(f"[*] Виконую: {cmd}")
        if any(cmd.startswith(g) for g in ['kitty', 'alacritty', 'xfce4-terminal']):
            def worker():
                update_status(f"🖥️ {cmd[:50]}")
                env = os.environ.copy()
                subprocess.Popen(cmd, shell=True, env=env,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(1)
                update_status("🌑 Готовий")
            threading.Thread(target=worker, daemon=True).start()
        else:
            def worker():
                update_status(f"⚡ {cmd[:50]}")
                proc = subprocess.Popen(
                    f"nice -n 10 firejail --profile=/etc/firejail/untrusted.profile {cmd}",
                    shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
                )
                out, _ = proc.communicate()
                with open("/tmp/deathstar_ai_output.log", "ab") as log:
                    log.write(out)
                update_status("🌑 Готовий")
            threading.Thread(target=worker, daemon=True).start()
    else:
        print(full_reply)
        update_status("🌑 Готовий")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query_agent(" ".join(sys.argv[1:]))
    else:
        print("VaderAI активний. Приклад: vaderai 'проскануй 127.0.0.1 та запам'ятай результати'")
