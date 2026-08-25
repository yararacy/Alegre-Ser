#!/usr/bin/env python3
"""
Atualiza podser-data.json a partir do feed do canal @Alegre-Ser no YouTube.

- NUNCA remove episódios (o feed do YouTube só traz os ~15 mais recentes;
  os antigos que saem do feed continuam preservados no JSON).
- NUNCA sobrescreve o título de um episódio já existente (mantém o título
  "curado" à mão). Só adiciona episódios novos.
- Roda sem dependências externas (só a biblioteca padrão do Python).

Uso: python scripts/update_podser.py
"""
import json
import os
import re
import sys
import urllib.request

CHANNEL_ID = "UCfeX5B51SmVkInjhBHc3u-g"  # @Alegre-Ser
FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id=" + CHANNEL_ID
DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "podser-data.json")


def fetch_feed():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def unescape(text):
    return (text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'").replace("&apos;", "'"))


def clean_title(raw):
    """Remove o prefixo 'PodSer #NN' / 'Ep NN' e separadores iniciais."""
    t = re.sub(r"^\s*(?:pod\s*ser|ep)\s*#?\s*(?:escolhas)?\s*\d+\s*", "", raw, flags=re.I)
    t = re.sub(r"^[\s\-–—|:.]+", "", t)
    return t.strip()


def episode_number(raw):
    """Retorna o nº do episódio se o vídeo for um PodSer; senão None."""
    m = re.search(r"pod\s*ser\s*#?\s*(?:escolhas)?\s*(\d{1,2})", raw, flags=re.I)
    if not m:
        m = re.match(r"\s*ep\s*#?\s*(\d{1,2})\b", raw, flags=re.I)
    return int(m.group(1)) if m else None


def parse_feed(xml):
    found = {}
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        vid = re.search(r"<yt:videoId>([^<]+)</yt:videoId>", entry)
        title = re.search(r"<title>([^<]*)</title>", entry)
        if not vid or not title:
            continue
        raw = unescape(title.group(1))
        ep = episode_number(raw)
        if ep is None:
            continue  # ignora lives, saudações e outros vídeos que não são episódios
        found[ep] = {"ep": ep, "id": vid.group(1).strip(), "titulo": clean_title(raw)}
    return found


def main():
    with open(DATA_PATH, encoding="utf-8") as f:
        existing = json.load(f)
    by_ep = {int(e["ep"]): e for e in existing}

    try:
        feed_eps = parse_feed(fetch_feed())
    except Exception as exc:  # rede fora do ar / feed indisponível: não quebra o site
        print("Erro ao ler o feed do YouTube:", exc)
        return 0

    changed = False
    for ep, data in feed_eps.items():
        if ep not in by_ep:
            by_ep[ep] = data
            changed = True
            print("Novo episódio adicionado: EP", ep, "-", data["titulo"])
        elif not by_ep[ep].get("id") and data["id"]:
            by_ep[ep]["id"] = data["id"]
            changed = True
            print("ID preenchido para EP", ep)

    if changed:
        out = sorted(by_ep.values(), key=lambda e: -int(e["ep"]))
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("podser-data.json atualizado.")
    else:
        print("Nenhum episódio novo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
