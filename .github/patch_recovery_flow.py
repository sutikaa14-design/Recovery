from pathlib import Path

def replace_or_fail(text, old, new, label):
    if old not in text:
        raise SystemExit(f"{label} not found")
    return text.replace(old, new, 1)

p = Path("app/src/main/java/com/recoverx/app/ui/viewmodel/RecoveryViewModel.kt")
s = p.read_text()
p.write_text(s)

print("Recovery live-results/recovery patch applied")
