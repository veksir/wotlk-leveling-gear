"""Ejecuta todas las pruebas en orden y resume el resultado.

Uso:  python tests/run_all.py            (todas)
      python tests/run_all.py bis ux     (solo las indicadas)
Construye antes la página con  python scripts/build_page.py  (el workflow de CI ya lo hace)."""
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ALL = ["reference_ids", "reference_sets", "sockets", "spec_weights", "smoke", "features", "gems", "heirlooms", "leveling",
       "fresh80", "optimizer", "bis", "extras", "ux"]


def main():
    names = sys.argv[1:] or ALL
    failed = []
    for name in names:
        t0 = time.time()
        r = subprocess.run([sys.executable, str(HERE / f"{name}.py")], capture_output=True, text=True)
        ok = r.returncode == 0
        last = (r.stdout.strip().splitlines() or [""])[-1] if ok else (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ["?"])[-1]
        print(f"{'OK  ' if ok else 'FAIL'} {name:<15} {time.time() - t0:5.1f}s  {last[:110]}")
        if not ok:
            failed.append(name)
    print(f"\n{len(names) - len(failed)}/{len(names)} pruebas correctas" + (f"; fallan: {', '.join(failed)}" if failed else ""))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
