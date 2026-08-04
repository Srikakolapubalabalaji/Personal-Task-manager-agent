import re

def normalize_task_title(title: str) -> str:
    if not title:
        return ""
    
    # 1. Lowercase and collapse consecutive spaces first
    t = title.lower().strip()
    t = re.sub(r'\s+', ' ', t)

    # 2. Strip conversational prefixes
    prefixes = [
        "create a high-priority task to ",
        "create a low-priority task to ",
        "create a task to ",
        "create task to ",
        "create a task ",
        "create task ",
        "add a task to ",
        "add task to ",
        "add task ",
        "i need to ",
        "i have to ",
        "need to ",
        "have to "
    ]
    for p in prefixes:
        if t.startswith(p):
            t = t[len(p):].strip()
            break

    # 3. Strip effort, duration, and deadline annotations (handling hyphens, periods, colons, spaces)
    t = re.sub(r'\s*[.\-—–:]?\s*(it will take|takes|\d+\s*(hours?|hrs?|mins?|minutes?)).*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*by\s+(friday|tomorrow|today|monday|tuesday|wednesday|thursday|saturday|sunday).*$', '', t, flags=re.IGNORECASE)
    t = re.sub(r'\s*(make it\s+)?(high|medium|low)\s+priority.*$', '', t, flags=re.IGNORECASE)

    # 4. Remove all non-alphanumeric characters except spaces and collapse again
    t = re.sub(r'[^\w\s]', '', t)
    t = re.sub(r'\s+', ' ', t).strip()

    return t
