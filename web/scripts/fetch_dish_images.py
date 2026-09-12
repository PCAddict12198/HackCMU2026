#!/usr/bin/env python3
"""Download one freely-licensed photo per core dish from Wikimedia Commons.

Images live in web/public/dishes/<id>.jpg. Mapping is by filename, so the
frozen dish schema does not change. Resume-safe: skipped if the jpg exists.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "dishes"
SOURCES = OUT / "sources.json"
UA = "TasteSpaceHackCMU/1.0 (educational demo; https://github.com/PCAddict12198/HackCMU2026)"
API = "https://commons.wikimedia.org/w/api.php"

OK_LIC = (
    "cc0",
    "public domain",
    "pd",
    "cc by 2.0",
    "cc by 2.5",
    "cc by 3.0",
    "cc by 4.0",
    "cc by-sa 2.0",
    "cc by-sa 2.5",
    "cc by-sa 3.0",
    "cc by-sa 4.0",
)
BAD = re.compile(
    r"grout|diagram|map of|logo|icon|svg|poster|chart|nutrition|label|"
    r"dinosaur|construction|blank being|floor plan|qr code|screenshot|"
    r"person\.|portrait of|infographic",
    re.I,
)

# Extra search phrases after the dish display name. Keep them food-specific.
QUERIES: dict[str, list[str]] = {
    "tonkotsu_ramen": ["tonkotsu ramen bowl", "tonkotsu ramen"],
    "shoyu_ramen": ["shoyu ramen bowl", "ramen soy broth"],
    "miso_soup": ["miso soup bowl tofu"],
    "chicken_katsu": ["chicken katsu tonkatsu cutlet"],
    "teriyaki_salmon": ["teriyaki salmon glazed"],
    "okonomiyaki": ["okonomiyaki savory pancake"],
    "matcha_ice_cream": ["matcha ice cream green tea"],
    "mapo_tofu": ["mapo tofu sichuan"],
    "kung_pao_chicken": ["kung pao chicken stir fry"],
    "char_siu": ["char siu roast pork chinese"],
    "hot_and_sour_soup": ["hot and sour soup chinese bowl"],
    "dan_dan_noodles": ["dan dan noodles sichuan"],
    "peking_duck": ["peking duck sliced"],
    "egg_tart": ["portuguese egg tart pastel de nata", "hong kong egg tart"],
    "kimchi_jjigae": ["kimchi jjigae stew"],
    "bibimbap": ["bibimbap stone bowl"],
    "bulgogi": ["bulgogi grilled beef"],
    "tteokbokki": ["tteokbokki rice cakes"],
    "korean_fried_chicken": ["korean fried chicken yangnyeom"],
    "japchae": ["japchae glass noodles"],
    "hotteok": ["hotteok korean pancake"],
    "tom_yum_goong": ["tom yum goong shrimp soup"],
    "green_curry": ["thai green curry chicken"],
    "pad_thai": ["pad thai noodles"],
    "som_tam": ["som tam papaya salad"],
    "larb": ["larb minced meat salad thai"],
    "massaman_curry": ["massaman curry thai"],
    "mango_sticky_rice": ["mango sticky rice thai"],
    "pho_bo": ["pho bo beef noodle soup vietnam"],
    "bun_cha": ["bun cha hanoi grilled pork"],
    "banh_mi": ["banh mi sandwich vietnam"],
    "goi_cuon": ["goi cuon summer rolls"],
    "bun_bo_hue": ["bun bo hue spicy noodle"],
    "ca_kho_to": ["ca kho to caramelized fish"],
    "che_ba_mau": ["che ba mau three color dessert"],
    "chana_masala": ["chana masala chickpea curry"],
    "butter_chicken": ["butter chicken murgh makhani"],
    "palak_paneer": ["palak paneer spinach"],
    "lamb_rogan_josh": ["rogan josh lamb kashmiri"],
    "masala_dosa": ["masala dosa south indian"],
    "chicken_biryani": ["chicken biryani hyderabadi"],
    "gulab_jamun": ["gulab jamun dessert"],
    "tabbouleh": ["tabbouleh parsley salad"],
    "hummus": ["hummus chickpea dip bowl"],
    "falafel": ["falafel fried chickpea"],
    "shawarma": ["shawarma wrap meat"],
    "fattoush": ["fattoush salad pita"],
    "mujaddara": ["mujaddara lentils rice"],
    "baklava": ["baklava pastry pistachio"],
    "spaghetti_carbonara": ["spaghetti carbonara pasta"],
    "cacio_e_pepe": ["cacio e pepe pecorino"],
    "margherita_pizza": ["pizza margherita"],
    "mushroom_risotto": ["mushroom risotto"],
    "osso_buco": ["osso buco veal shank"],
    "minestrone": ["minestrone vegetable soup"],
    "tiramisu": ["tiramisu dessert"],
    "french_onion_soup": ["french onion soup gruyere"],
    "beef_bourguignon": ["boeuf bourguignon beef stew"],
    "coq_au_vin": ["coq au vin chicken wine"],
    "ratatouille": ["ratatouille provençal vegetables"],
    "bouillabaisse": ["bouillabaisse fish stew"],
    "croque_monsieur": ["croque monsieur sandwich"],
    "creme_brulee": ["creme brulee custard"],
    "tacos_al_pastor": ["tacos al pastor pineapple"],
    "aguachile": ["aguachile shrimp lime"],
    "mole_poblano": ["mole poblano chicken"],
    "pozole_rojo": ["pozole rojo pork hominy"],
    "chiles_rellenos": ["chiles rellenos stuffed pepper"],
    "cochinita_pibil": ["cochinita pibil pork"],
    "tres_leches": ["tres leches cake"],
}

NAMES = {
    "tonkotsu_ramen": "Tonkotsu Ramen",
    "shoyu_ramen": "Shoyu Ramen",
    "miso_soup": "Miso Soup",
    "chicken_katsu": "Chicken Katsu",
    "teriyaki_salmon": "Teriyaki Salmon",
    "okonomiyaki": "Okonomiyaki",
    "matcha_ice_cream": "Matcha Ice Cream",
    "mapo_tofu": "Mapo Tofu",
    "kung_pao_chicken": "Kung Pao Chicken",
    "char_siu": "Char Siu",
    "hot_and_sour_soup": "Hot And Sour Soup",
    "dan_dan_noodles": "Dan Dan Noodles",
    "peking_duck": "Peking Duck",
    "egg_tart": "Egg Tart",
    "kimchi_jjigae": "Kimchi Jjigae",
    "bibimbap": "Bibimbap",
    "bulgogi": "Bulgogi",
    "tteokbokki": "Tteokbokki",
    "korean_fried_chicken": "Korean Fried Chicken",
    "japchae": "Japchae",
    "hotteok": "Hotteok",
    "tom_yum_goong": "Tom Yum Goong",
    "green_curry": "Green Curry",
    "pad_thai": "Pad Thai",
    "som_tam": "Som Tam",
    "larb": "Larb",
    "massaman_curry": "Massaman Curry",
    "mango_sticky_rice": "Mango Sticky Rice",
    "pho_bo": "Pho Bo",
    "bun_cha": "Bun Cha",
    "banh_mi": "Banh Mi",
    "goi_cuon": "Goi Cuon",
    "bun_bo_hue": "Bun Bo Hue",
    "ca_kho_to": "Ca Kho To",
    "che_ba_mau": "Che Ba Mau",
    "chana_masala": "Chana Masala",
    "butter_chicken": "Butter Chicken",
    "palak_paneer": "Palak Paneer",
    "lamb_rogan_josh": "Lamb Rogan Josh",
    "masala_dosa": "Masala Dosa",
    "chicken_biryani": "Chicken Biryani",
    "gulab_jamun": "Gulab Jamun",
    "tabbouleh": "Tabbouleh",
    "hummus": "Hummus",
    "falafel": "Falafel",
    "shawarma": "Shawarma",
    "fattoush": "Fattoush",
    "mujaddara": "Mujaddara",
    "baklava": "Baklava",
    "spaghetti_carbonara": "Spaghetti Carbonara",
    "cacio_e_pepe": "Cacio E Pepe",
    "margherita_pizza": "Margherita Pizza",
    "mushroom_risotto": "Mushroom Risotto",
    "osso_buco": "Osso Buco",
    "minestrone": "Minestrone",
    "tiramisu": "Tiramisu",
    "french_onion_soup": "French Onion Soup",
    "beef_bourguignon": "Beef Bourguignon",
    "coq_au_vin": "Coq Au Vin",
    "ratatouille": "Ratatouille",
    "bouillabaisse": "Bouillabaisse",
    "croque_monsieur": "Croque Monsieur",
    "creme_brulee": "Creme Brulee",
    "tacos_al_pastor": "Tacos Al Pastor",
    "aguachile": "Aguachile",
    "mole_poblano": "Mole Poblano",
    "pozole_rojo": "Pozole Rojo",
    "chiles_rellenos": "Chiles Rellenos",
    "cochinita_pibil": "Cochinita Pibil",
    "tres_leches": "Tres Leches",
}

# Prefer a known Commons file when search ranking is noisy.
OVERRIDES: dict[str, str] = {
    "egg_tart": "File:Hong Kong Sweet Dynasty egg tarts.jpg",
    "char_siu": "File:Char siu.jpg",
    "pho_bo": "File:Beef noodle soup (Phở bò) - Pho Hanoi Authentic 2024-12-01.jpg",
    "chicken_katsu": "File:Cheesy chicken katsu and rice - Betterday, Brighton 2024-01-19.jpg",
    "teriyaki_salmon": "File:Liat Portal for Foodie Disorder - Oven-baked teriyaki salmon with vegetables.jpg",
    "tom_yum_goong": "File:Shrimp Tom yum soup from a Thai restaurant in Delray Beach, Florida.jpg",
    "bun_cha": "File:Bun cha Hanoi.jpg",
    "hummus": "File:Homemade hummus and pita 03.jpg",
    "ratatouille": "File:Ratatouille 2.jpg",
    "pozole_rojo": "File:Pozole Rojo Mexicano.jpg",
    "shoyu_ramen": "File:Soy sauce ramen.jpg",
    "banh_mi": "File:Bánh mì.jpg",
    "french_onion_soup": "File:French onion soup.jpg",
    "coq_au_vin": "File:Coq au vin.jpg",
    "mole_poblano": "File:Mole poblano (1).JPG",
    "fattoush": "File:Fattoush.jpg",
    "osso_buco": "File:Ossobuco.jpg",
    "cochinita_pibil": "File:Cochinita pibil.jpg",
    "ca_kho_to": "File:Cá kho tộ.jpg",
    "che_ba_mau": "File:Chè ba màu.jpg",
}


def get(url: str) -> bytes:
    # system curl has macOS certs; python.org urllib often does not
    r = subprocess.run(
        ["curl", "-fsSL", "--max-time", "60", "-A", UA, url],
        check=True,
        capture_output=True,
    )
    return r.stdout


def api(params: dict) -> dict:
    q = urllib.parse.urlencode({**params, "format": "json"})
    return json.loads(get(f"{API}?{q}"))


def strip_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", s).strip()


def lic_ok(name: str) -> bool:
    n = (name or "").strip().lower().replace("—", "-")
    return any(n == k or n.startswith(k + " ") for k in OK_LIC)


def score(title: str, dish_name: str, query: str) -> int:
    t = title.lower()
    if BAD.search(t):
        return -100
    s = 0
    for w in re.findall(r"[a-z0-9]+", dish_name.lower()):
        if len(w) > 2 and w in t:
            s += 8
    for w in query.lower().split():
        if len(w) > 3 and w in t:
            s += 2
    return s


def page_info(title: str) -> dict | None:
    data = api(
        {
            "action": "query",
            "titles": title,
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|mime|size",
            "iiurlwidth": "900",
        }
    )
    pages = data.get("query", {}).get("pages", {})
    for p in pages.values():
        ii = (p.get("imageinfo") or [None])[0]
        if not ii:
            return None
        em = ii.get("extmetadata") or {}
        return {
            "title": p.get("title"),
            "thumb": ii.get("thumburl") or ii.get("url"),
            "page": em.get("LicenseUrl", {}).get("value")
            or f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(p.get('title', ''))}",
            "artist": strip_html(em.get("Artist", {}).get("value", "unknown")),
            "licence": em.get("LicenseShortName", {}).get("value", ""),
            "mime": ii.get("mime", ""),
        }
    return None


def search(query: str, limit: int = 5) -> list[str]:
    data = api(
        {
            "action": "query",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",
            "gsrlimit": str(limit),
        }
    )
    pages = data.get("query", {}).get("pages", {})
    ranked = sorted(pages.values(), key=lambda p: p.get("index", 99))
    return [p["title"] for p in ranked if p.get("title")]


def pick(dish_id: str) -> dict | None:
    name = NAMES[dish_id]
    if dish_id in OVERRIDES:
        info = page_info(OVERRIDES[dish_id])
        if info and lic_ok(info["licence"]) and info.get("thumb"):
            info["rank"] = 0
            info["dish"] = name
            return info
        time.sleep(0.8)
    best = None
    best_s = -1
    for q in QUERIES[dish_id]:
        titles = search(q)
        time.sleep(1.1)
        for i, title in enumerate(titles):
            if BAD.search(title):
                continue
            info = page_info(title)
            time.sleep(0.35)
            if not info or not info.get("thumb"):
                continue
            if not lic_ok(info["licence"]):
                continue
            if not str(info.get("mime", "")).startswith("image/"):
                continue
            sc = score(title, name, q) - i
            if sc > best_s:
                best_s = sc
                best = {**info, "rank": i, "dish": name, "query": q}
        if best_s >= 10:
            break
    return best


def download(url: str, dest: Path) -> None:
    dest.write_bytes(get(url))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    sources = json.loads(SOURCES.read_text()) if SOURCES.exists() else {}
    missing = []
    for dish_id in NAMES:
        dest = OUT / f"{dish_id}.jpg"
        if dest.exists() and dest.stat().st_size > 2000:
            print(f"have {dish_id}")
            continue
        print(f"fetch {dish_id} ...", flush=True)
        try:
            hit = pick(dish_id)
        except Exception as e:
            print(f"  ERR {e}")
            missing.append(dish_id)
            time.sleep(0.4)
            continue
        if not hit:
            print("  none")
            missing.append(dish_id)
            continue
        try:
            download(hit["thumb"], dest)
        except Exception as e:
            print(f"  dl ERR {e}")
            missing.append(dish_id)
            continue
        sources[dish_id] = {
            "dish": hit["dish"],
            "title": hit["title"],
            "page": f"https://commons.wikimedia.org/wiki/{urllib.parse.quote(hit['title'])}",
            "artist": hit["artist"][:160],
            "licence": hit["licence"],
        }
        SOURCES.write_text(json.dumps(sources, indent=2, ensure_ascii=False) + "\n")
        print(f"  ok {hit['title']} ({hit['licence']})")
        time.sleep(0.6)
    print("done", len(list(OUT.glob('*.jpg'))), "jpgs; missing", missing)


if __name__ == "__main__":
    main()
