import hashlib
from pathlib import Path
import re
import subprocess
import sys


def extrair_segredos_historicos() -> dict[str, str]:
    segredos = {}
    
    # 1. Tenta extrair de ce6c3b0:docker-compose.yml
    try:
        res_compose = subprocess.run(
            ["git", "show", "ce6c3b0:docker-compose.yml"],
            capture_output=True,
            text=True,
            check=True
        )
        for linha in res_compose.stdout.splitlines():
            m = re.search(r"^\s*-\s*(HDW_API_KEY|OVPN_TOKEN)\s*=\s*(.+)$", linha) or \
                re.search(r"^\s*(HDW_API_KEY|OVPN_TOKEN)\s*:\s*(.+)$", linha)
            if m:
                var = m.group(1).strip()
                val = m.group(2).strip().strip("'\"")
                segredos[var] = val
    except Exception:
        pass

    # 2. Se faltar algum, complementa/confere com ce6c3b0:hdc_hdw_bridge.py
    if len(segredos) < 2:
        try:
            res_bridge = subprocess.run(
                ["git", "show", "ce6c3b0:hdc_hdw_bridge.py"],
                capture_output=True,
                text=True,
                check=True
            )
            for linha in res_bridge.stdout.splitlines():
                m_hdw = re.search(r'os\.getenv\("HDW_API_KEY",\s*["\']([^"\']+)["\']\)', linha)
                if m_hdw and "HDW_API_KEY" not in segredos:
                    segredos["HDW_API_KEY"] = m_hdw.group(1).strip()
                m_ovpn = re.search(r'os\.getenv\("OVPN_TOKEN",\s*["\']([^"\']+)["\']\)', linha)
                if m_ovpn and "OVPN_TOKEN" not in segredos:
                    segredos["OVPN_TOKEN"] = m_ovpn.group(1).strip()
        except Exception:
            pass

    if "HDW_API_KEY" not in segredos or "OVPN_TOKEN" not in segredos:
        raise RuntimeError("Não foi possível extrair todas as credenciais históricas do commit ce6c3b0")

    return segredos


def main():
    segredos = extrair_segredos_historicos()
    
    raiz_projeto = Path(__file__).resolve().parent.parent
    caminho_saida = raiz_projeto / "segredos_revogados.sha256"
    
    linhas = []
    for var in ["HDW_API_KEY", "OVPN_TOKEN"]:
        val = segredos[var]
        hash_val = hashlib.sha256(val.encode("utf-8")).hexdigest()
        tam_val = len(val)
        linhas.append(f"{hash_val} {tam_val} {var}")
        
    caminho_saida.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    sys.stdout.write("2 hashes gravados\n")


if __name__ == "__main__":
    main()
