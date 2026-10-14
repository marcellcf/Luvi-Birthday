"""
LUVI'S BIRTHDAY QUEST
=====================
Game pixel 8-bit buat ulang tahun Luvi, jalan di dalam Streamlit.

Alur game:
  Desa -> Kandang Ayam (pecahin telur, dapet koin + Baby Luvi)
       -> Toko Gacha (koin jadi kartu foto, terakhir dapet Kartu Legendary)
       -> Kastil Kue (lawan Kue Raksasa, tiup lilinnya)
       -> Ending (foto, surat, credits)

Cara jalanin:
    pip install streamlit
    streamlit run app.py

Semua yang bisa kamu ganti ada di bagian KONFIGURASI di bawah.
Game-nya sendiri ada di file game.html (nggak perlu diubah).
"""

import base64
import io
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

# ==================================================================
#  KONFIGURASI
# ==================================================================
NAMA = "Luvi"
NAMA_LENGKAP = "Luvi Lettisia"
UMUR = 20
PENGIRIM = "Adek"   # muncul di tanda tangan surat & credits

# NPC di desa. "tampilan" pilih "jessica" atau "adek" (bentuk karakternya).
NPC = [
    {
        "nama": "Jessica",
        "nama_lengkap": "Jessica Margaretha Olivia",
        "tampilan": "jessica",
        "pesan": [
            "Happy birthday luvi",
            "Panjang umur sehat selalu",
            "Sukses terus",
            "Msh eksperimen kan",
        ],
    },
    {
        "nama": "Adek",
        "nama_lengkap": "Adek",
        "tampilan": "adek",
        "pesan": [
            "Happy birthday ce luvi!!",
            "Panjang umur sehat selalu",
            "Makin sukses terus ya ce",
            "Traktirannya jangan lupa hehe",
        ],
    },
]

# Pesan dari 4 anak ayam yang menetas (1 telur lagi isinya batu, 1 telur emas = Baby Luvi)
PESAN_ANAK_AYAM = [
    "Selamat ulang tahun ke-20, Luvi! Aku anak ayam pertama yang ngucapin!",
    "Semoga makin bahagia, makin sehat, makin bersinar kayak telur emas.",
    "Kata induk ayam, kamu orangnya baik banget. Aku setuju. Ciap!",
    "Jangan lupa traktir ya. Biji jagung juga boleh kok.",
]

# Kartu gacha, urut dari yang pertama keluar. Yang terakhir HARUS legendary
# (kartu itu yang jadi kunci gerbang kastil). rarity: common / rare / epic / legendary
KARTU_GACHA = [
    {"rarity": "common", "foto": "foto/kartu1.jpg",
     "judul": "Luvi - Mode Panitia",
     "teks": "Rundown di tangan, senyum di muka. Sibuk tapi tetap santai."},
    {"rarity": "rare", "foto": "foto/kartu2.jpg",
     "judul": "Luvi - Kobid ARTMAX",
     "teks": "Koordinator yang paling bisa diandelin. Jaket merahnya bikin auto keliatan bos."},
    {"rarity": "epic", "foto": "foto/kartu3.jpg",
     "judul": "Luvi - Senyum Andalan",
     "teks": "Efek kartu: semua orang di sekitarnya ikut senyum. +100 mood."},
    {"rarity": "legendary", "foto": "foto/kartu4.jpg",
     "judul": "Luvi Lettisia - Edisi 20 Tahun",
     "teks": "Kartu paling langka di dunia. Cuma ada satu, dan hari ini dia ulang tahun."},
]

FOTO_AKHIR = "foto/akhir.jpg"
CAPTION_AKHIR = "Luvi Lettisia, Level 20"

SURAT = """Ce Luvi,

Happy birthday yang ke-20!

Makasih udah jadi cece yang seru, sabar, dan selalu bisa diandelin. Semoga di umur yang baru ini cece makin sehat, makin bahagia, dan semua yang lagi diperjuangin satu-satu kesampaian.

Tetap jadi Luvi yang kayak gini ya.

Traktirannya jangan lupa. Hehe."""
# ==================================================================


APP_DIR = Path(__file__).parent


@st.cache_data(show_spinner=False)
def _encode_photo(path_str: str, mtime: float) -> str:
    from PIL import Image, ImageOps  # Pillow sudah ikut terpasang bareng Streamlit

    img = ImageOps.exif_transpose(Image.open(path_str))
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[-1])
        img = bg
    else:
        img = img.convert("RGB")
    img.thumbnail((900, 900))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=84)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def photo_uri(rel_path):
    if not rel_path:
        return None
    p = APP_DIR / rel_path
    if not p.is_file():
        return None
    try:
        return _encode_photo(str(p), p.stat().st_mtime)
    except Exception:
        return None


def build_data() -> dict:
    return {
        "nama": NAMA,
        "namaLengkap": NAMA_LENGKAP,
        "umur": int(UMUR),
        "pengirim": PENGIRIM,
        "npc": [
            {"nama": n["nama"], "namaLengkap": n.get("nama_lengkap", n["nama"]),
             "tampilan": n.get("tampilan", ""), "pesan": list(n.get("pesan", []))}
            for n in NPC
        ],
        "telur": list(PESAN_ANAK_AYAM) or ["Ciap!"],
        "kartu": [
            {"rarity": k.get("rarity", "common"), "judul": k.get("judul", ""),
             "teks": k.get("teks", ""), "foto": photo_uri(k.get("foto"))}
            for k in KARTU_GACHA
        ],
        "fotoAkhir": photo_uri(FOTO_AKHIR),
        "captionAkhir": CAPTION_AKHIR,
        "surat": SURAT.strip(),
    }


def build_game_html() -> str:
    template = (APP_DIR / "game.html").read_text(encoding="utf-8")
    data_json = json.dumps(build_data(), ensure_ascii=False).replace("</", "<\\/")
    return template.replace("/*__DATA__*/null", data_json, 1)


PAGE_CSS = """
<style>
.stApp{background:#1a1230}
header[data-testid="stHeader"]{background:transparent;height:0}
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"]{visibility:hidden}
.block-container{padding-top:1rem;padding-bottom:0;max-width:980px}
iframe{border:none}
</style>
"""


def main():
    st.set_page_config(page_title=f"{NAMA}'s Birthday Quest", page_icon="🎂", layout="wide")
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    components.html(build_game_html(), height=640, scrolling=False)


if __name__ == "__main__":  # Streamlit menjalankan file ini sebagai __main__
    main()
