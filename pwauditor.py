#!/usr/bin/env python3
"""
SECURE PASSWORD AUDITOR (SPA)
Pro Edition — Termux/Linux
Created by Sreerag
"""

import os, sys, time, math, re, string, secrets, getpass, hashlib, random
import requests
from datetime import datetime

# -----------------------------
# Optional clipboard support
# -----------------------------
CLIP_OK = False
try:
    import pyperclip
    CLIP_OK = True
except Exception:
    pass

# -----------------------------
# Hashing (passlib bcrypt)
# -----------------------------
try:
    from passlib.hash import bcrypt
    HAVE_PASSLIB = True
except Exception:
    HAVE_PASSLIB = False

# -----------------------------
# ANSI Colors
# -----------------------------
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
MAG    = "\033[95m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[90m"
WHITE = "\033[97m"
BLUE = "\033[94m"   # light blue
RESET  = "\033[0m"

# -----------------------------
# Clear / Paths / Logging
# -----------------------------
def clear():
    os.system("clear" if os.name == "posix" else "cls")

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "spa.log")
os.makedirs(LOG_DIR, exist_ok=True)

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_event(event: str):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{now()}] {event}\n")
    except Exception:
        pass

# -----------------------------
# Cinematic printing
# -----------------------------
def typewriter(text: str, delay: float = 0.02, newline=True):
    for ch in text:
        print(ch, end="", flush=True)
        time.sleep(delay)
    if newline: print()

def cinematic_block(lines, delay_line=0.05, delay_char=0.01):
    for line in lines:
        typewriter(line, delay_char)
        time.sleep(delay_line)

# -----------------------------
# Old Banner (used everywhere)
# -----------------------------
def old_banner():
    return f"""
{CYAN}{BOLD}
   ███████╗███████╗ ██████╗ ██╗   ██╗██████╗  
   ██╔════╝██╔════╝██╔═══██╗██║   ██║██╔══██╗ 
   █████╗  ███████╗██║   ██║██║   ██║██████╔╝ 
   ██╔══╝  ╚════██║██║   ██║██║   ██║██╔═══╝  
   ███████╗███████║╚██████╔╝╚██████╔╝██║      
   ╚══════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═╝      

 🔐 SECURE PASSWORD AUDITOR (SPA)
  - Created by Sreerag
{RESET}
"""

def show_banner():
    clear()
    cinematic_block(old_banner().splitlines(), delay_line=0.03, delay_char=0.001)
    print()

# -----------------------------
# Exit Banner (kept cinematic)
# -----------------------------
def exit_banner():
    clear()
    lines = [
        RED  + r"   ███████╗██╗  ██╗██╗████████╗" + RESET,
        RED  + r"   ██╔════╝██║  ██║██║╚══██╔══╝" + RESET,
        RED  + r"   ███████╗███████║██║   ██║   " + RESET,
        RED  + r"   ╚════██║██╔══██║██║   ██║   " + RESET,
        RED  + r"   ███████║██║  ██║██║   ██║   " + RESET,
        RED  + r"   ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝   " + RESET,
        CYAN + "====================================" + RESET,
        GREEN + "   🔐 Secure Password Auditor" + RESET,
        YELLOW + "   Shutting down... Goodbye!" + RESET,
        GREEN + "   Created by Sreerag" + RESET,
        CYAN + "====================================" + RESET,
    ]
    cinematic_block(lines, delay_line=0.08, delay_char=0.02)
    print(DIM + f"[✓] Session Closed — {now()}" + RESET)
    sys.exit(0)

# -----------------------------
# Password utils
# -----------------------------
COMMON_PASSWORDS = {"123456","password","123456789","qwerty","abc123","iloveyou","admin","welcome"}
KEYBOARD_SEQS = ["qwertyuiop","asdfghjkl","zxcvbnm","1234567890"]

def generate_password(length=16, use_upper=True, use_digits=True, use_symbols=True):
    alphabet = string.ascii_lowercase
    if use_upper:  alphabet += string.ascii_uppercase
    if use_digits: alphabet += string.digits
    if use_symbols: alphabet += "!@#$%&*()-_=+[]{}:;?/"
    return "".join(secrets.choice(alphabet) for _ in range(length))

def entropy_bits(pw: str) -> float:
    pool = 0
    if re.search(r'[a-z]', pw): pool += 26
    if re.search(r'[A-Z]', pw): pool += 26
    if re.search(r'\d', pw):    pool += 10
    if re.search(r'[!@#\$%&\*\(\)\-_=+\[\]\{\}:;\?\/]', pw): pool += 20
    if pool == 0: pool = len(set(pw))
    return len(pw) * math.log2(pool) if pool > 0 else 0.0

def audit_details(pw: str):
    length = len(pw)
    entropy = math.log2(len(set(pw)) ** length) if pw else 0

    checks = {
        "Has Uppercase": any(c.isupper() for c in pw),
        "Has Lowercase": any(c.islower() for c in pw),
        "Has Digit": any(c.isdigit() for c in pw),
        "Has Symbol": any(c in string.punctuation for c in pw),
        "Length ≥ 12": length >= 12,
    }

    # Each check worth 20 points (5 checks → max score 100)
    score = sum(checks.values()) * 20

    tips = []
    if not checks["Has Uppercase"]:
        tips.append("Add at least one uppercase letter")
    if not checks["Has Lowercase"]:
        tips.append("Add at least one lowercase letter")
    if not checks["Has Digit"]:
        tips.append("Include at least one number")
    if not checks["Has Symbol"]:
        tips.append("Use at least one special symbol")
    if not checks["Length ≥ 12"]:
        tips.append("Make the password at least 12 characters long")

    return {
        "entropy": entropy,
        "score": score,
        "checks": checks,
        "tips": tips,
    }

def bcrypt_hash(pw: str, rounds: int = 12) -> str:
    if not HAVE_PASSLIB:
        return RED + "Passlib not installed (pip install passlib bcrypt)" + RESET
    return bcrypt.using(rounds=rounds).hash(pw)

# -----------------------------
# Menu Actions with CINEMATIC
# -----------------------------
def action_generate():
    length_in = input(CYAN + "Enter length (default 16): " + RESET).strip()
    length = int(length_in) if length_in.isdigit() else 16
    pw = generate_password(length)
    det = audit_details(pw)
    lines = [
        GREEN + "Generated password:" + RESET + f" {pw}",
        CYAN + f"Entropy: {det['entropy']:.1f} bits" + RESET,
        CYAN + f"Score: {det['score']}/100" + RESET,
    ]
    if CLIP_OK:
        pyperclip.copy(pw)
        lines.append(GREEN + "[✓] Copied to clipboard" + RESET)
    cinematic_block(lines)
    log_event(f"GENERATE len={length} score={det['score']} entropy={det['entropy']:.1f}")
    input(YELLOW + "\nPress Enter..." + RESET)

def action_audit():
    pw = getpass.getpass(CYAN + "Enter password: " + RESET)
    det = audit_details(pw)

    # First summary block with colored headers + green results
    lines = [
        f"{BOLD}{RED}Password audit:{RESET}",
        f"{BOLD}{RED}Length:{RESET} {GREEN}{len(pw)}{RESET}",
        f"{BOLD}{RED}Entropy:{RESET} {GREEN}{det['entropy']:.1f} bits{RESET}",
    ]

    # Score with color depending on strength + progress bar
    score = det['score']
    score_color = GREEN if score >= 70 else (YELLOW if score >= 40 else RED)
    bar_len = 20
    filled = int(bar_len * score / 100)
    bar = GREEN + "█" * filled + RED + "█" * (bar_len - filled) + RESET
    lines.append(f"{BOLD}{RED}Score:{RESET} {bar} {score_color}{score}/100{RESET}\n")

    cinematic_block(lines)

    # Animated Checks
    check_lines = [f"{BOLD}{RED}Checks:{RESET}"]
    check_lines.append(RED + "─" * 30 + RESET)
    for k, v in det["checks"].items():
        mark = GREEN + "✔" + RESET if v else RED + "✘" + RESET
        check_lines.append(f" - {k:13} {mark}")
    cinematic_block(check_lines)

    # Animated Suggestions
    if det["tips"]:
        tip_lines = [f"{BOLD}{RED}Suggestions:{RESET}"]
        tip_lines.append(RED + "─" * 30 + RESET)
        for t in det["tips"]:
            tip_lines.append(" - " + GREEN + t + RESET)
        cinematic_block(tip_lines)
    else:
        cinematic_block([GREEN + "No suggestions! Your password looks strong ✅" + RESET])

    # Logging + pause
    log_event(f"AUDIT score={det['score']} entropy={det['entropy']:.1f}")
    input(YELLOW + "\nPress Enter..." + RESET)

def action_hash():
    if not HAVE_PASSLIB:
        cinematic_block([RED + "Passlib missing! pip install passlib bcrypt" + RESET])
        input(YELLOW + "\nPress Enter..." + RESET); return
    pw = getpass.getpass(CYAN + "Enter password: " + RESET)
    h = bcrypt_hash(pw)
    cinematic_block([GREEN + "Bcrypt hash:" + RESET, h])
    log_event("HASH generated")
    input(YELLOW + "\nPress Enter..." + RESET)

def action_view_logs():
    lines = [CYAN + "── Logs (latest 10) ──────────────" + RESET]
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            last = f.readlines()[-10:]
        lines.extend([DIM + l.strip() + RESET for l in last])
    else:
        lines.append(DIM + "No logs yet." + RESET)
    cinematic_block(lines)
    input(YELLOW + "\nPress Enter..." + RESET)

def action_breach_check():
    pw = getpass.getpass(CYAN + "Enter password to check breach: " + RESET)
    sha1_pw = hashlib.sha1(pw.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1_pw[:5], sha1_pw[5:]

    url = f"https://api.pwnedpasswords.com/range/{prefix}"
    try:
        res = requests.get(url)
        if res.status_code != 200:
            print(RED + "⚠️ Error reaching breach database." + RESET)
            return
    except Exception as e:
        print(RED + f"⚠️ Connection error: {e}" + RESET)
        return

    hashes = (line.split(":") for line in res.text.splitlines())
    count = next((int(count) for h, count in hashes if h == suffix), 0)

    if count:
        cinematic_block([
            f"{BOLD}{RED}Breach Check Result:{RESET}",
            RED + f"⚠️ Found {count} times in known breaches! ❌" + RESET,
            YELLOW + "You should change this password immediately." + RESET
        ])
    else:
        cinematic_block([
            f"{BOLD}{RED}Breach Check Result:{RESET}",
            GREEN + "✅ Not found in breach databases. Good sign!" + RESET
        ])

    log_event(f"BREACH_CHECK result={'found' if count else 'not found'}")
    input(YELLOW + "\nPress Enter..." + RESET)

def action_security_quiz():
    questions = [
        {"q": "Which password is strongest?",
         "options": ["123456", "qwerty", "sTr0ng!Pass99"], "a": 3},
        {"q": "How often should you change important passwords?",
         "options": ["Never", "Every few years", "At least once a year or if breached"], "a": 3},
        {"q": "What’s safer?",
         "options": ["Same password everywhere", "Unique password per site", "Write on sticky notes"], "a": 2}
    ]

    score = 0
    random.shuffle(questions)

    for i, q in enumerate(questions, 1):
        # Show question with cinematic effect
        cinematic_block([BOLD + f"\nQ{i}: {q['q']}" + RESET])
        
        # Show options
        option_lines = []
        for j, opt in enumerate(q["options"], 1):
            option_lines.append(f"  {j}) {opt}")
        cinematic_block(option_lines)

        ans = input(CYAN + "Your answer: " + RESET)
        
        # Feedback with cinematic effect
        if ans.strip() == str(q["a"]):
            cinematic_block([GREEN + "✔ Correct!" + RESET])
            score += 1
        else:
            cinematic_block([RED + f"✘ Wrong! Correct answer: {q['a']}) {q['options'][q['a']-1]}" + RESET])

    # Fancy summary block at the end
    summary_lines = [
        f"{BOLD}{RED}Quiz Summary:{RESET}",
        f"{CYAN}Total Questions:{RESET} {GREEN}{len(questions)}{RESET}",
        f"{CYAN}Correct Answers:{RESET} {GREEN}{score}{RESET}",
        f"{CYAN}Score:{RESET} {YELLOW}{score}/{len(questions)}{RESET}"
    ]

    if score == len(questions):
        summary_lines.append(GREEN + "🌟 Excellent! You're a security pro!" + RESET)
    elif score >= len(questions)//2:
        summary_lines.append(YELLOW + "👍 Good! But there’s room to improve." + RESET)
    else:
        summary_lines.append(RED + "⚠️ Needs improvement. Read more about security." + RESET)

    cinematic_block(summary_lines)

    # Log
    log_event(f"QUIZ score={score}/{len(questions)}")
    input(YELLOW + "\nPress Enter..." + RESET)

# -----------------------------
# Menu
# -----------------------------
def menu():
    while True:
        show_banner()
        print(f"""{YELLOW}
[1] Generate a Secure Password
[2] Audit a Password
[3] Hash a Password (bcrypt)
[4] View Logs
[5] Check Password Breach (HIBP)
[6] Security Awareness Quiz
[7] Exit
{RESET}""")
        choice = input(CYAN + "Choose (1-7): " + RESET).strip()
        if choice == "1": action_generate()
        elif choice == "2": action_audit()
        elif choice == "3": action_hash()
        elif choice == "4": action_view_logs()
        elif choice == "7": exit_banner()
        elif choice == "5": action_breach_check()
        elif choice == "6": action_security_quiz()
        else:
            cinematic_block([RED + "Invalid choice!" + RESET])
            time.sleep(1)
# -----------------------------
if __name__ == "__main__":
    try:
        show_banner()
        menu()
    except KeyboardInterrupt:
        exit_banner()
