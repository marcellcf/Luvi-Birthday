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
            "Selamat anda sudah kepala 2",
            "smakin tua",
            "semoga kedepannya kmu bisa sukses terus, bahagia selalu,",
            "dan apa yang kamu lakukan semua dijadikan berhasil",
            "amin",
        ],
    },
    {
        "nama": "Adek",
        "nama_lengkap": "Adek",
        "tampilan": "adek",
        "pesan": [
            "Happy birthday ce luvi!!",
            "Semoga jadi cece yang baik dan nggak suka ngebully adeknya",
            "Stop jadi cece yang jahat ya ce. Adek udah cukup menderita",
            "Hehe bercanda... dikit",
            "Makasih udah jadi cece yang seru, semoga makin sehat dan makin bahagia",
            "Tahun ini jadi cece yang baik ya. Janji?",
        ],
    },
]

# Pesan dari 4 anak ayam yang menetas (1 telur lagi isinya batu, 1 telur emas = Baby Luvi)
PESAN_ANAK_AYAM = [
    "Selamat ulang tahun ke-20, Luvi! Aku anak ayam pertama yang ngucapin!",
    "Semoga makin bahagia, makin sehat, makin bersinar kayak telur emas.",
    "Kata induk ayam, kamu orangnya baik banget. Aku setuju. Ciap!",
    "Jangan lupa traktir ya. Biji jagung juga boleh kok. Ciap!",
]

# Kartu gacha, urut dari yang pertama keluar. Yang terakhir HARUS legendary
# (kartu itu yang jadi kunci gerbang kastil). rarity: common / rare / epic / legendary
KARTU_GACHA = [
    # 1. foto bertiga mirror selfie sebelum photobox
    {"rarity": "common", "foto": "foto/kartu1.jpeg",
     "judul": "Trio Pemanasan Photobox",
     "teks": "Belum masuk photobox, udah foto duluan di cermin. Namanya juga pemanasan. "
             "Efek kartu: kangen ketemuan +100."},
    # 2. foto masa kecil, tatapan "eits aku keren kan"
    {"rarity": "rare", "foto": "foto/kartu2.jpeg",
     "judul": "Mini Luvi - Edisi Sok Keren",
     "teks": "Tatapan 'eits, aku keren kan?' ternyata udah ada dari kecil. "
             "Fix, percaya diri itu bawaan lahir."},
    # 3. foto aib lagi nahan ketawa
    {"rarity": "epic", "foto": "foto/kartu3.jpeg",
     "judul": "Luvi - Mode Nahan Ketawa",
     "teks": "Foto langka hasil jepretan diam-diam. Ketawanya ditahan, tapi pipinya nggak bisa bohong. "
             "Kartu udah keluar, protes ditolak."},
    # 4. foto sekarang lagi jadi panitia (harus yang terakhir & legendary)
    {"rarity": "legendary", "foto": "foto/kartu4.jpeg",
     "judul": "Luvi Panitia - Edisi Legend",
     "teks": "Rundown di tangan, acara jalan, panitia lain tenang. "
             "Dapet rarity Legendary karena kerjanya emang legend."},
]

# 5. foto pas ketemuan, Luvi umur 20 lagi senyum hepi
FOTO_AKHIR = "foto/akhir.jpeg"
CAPTION_AKHIR = "Luvi Lettisia, resmi Level 20!"
TEKS_AKHIR = ("Foto paling baru, langsung dari hari ini. Umur nambah, senyum kiyowo-nya tetap. "
              "Level hepi: MAKSIMAL.")

SURAT = """Ce Luvi,

Happy birthday yang ke-20!

Makasih udah jadi cece yang seru, sabar, dan selalu bisa diandelin. Semoga di umur yang baru ini cece makin sehat, makin bahagia, dan semua yang lagi diperjuangin satu-satu kesampaian.

Tetap jadi Luvi yang kayak gini ya. Tapi versi yang nggak suka ngebully adek.

Hehe."""
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


PHOTO_EXTS = [".jpeg", ".jpg", ".png", ".webp"]


def find_photo(rel_path):
    """Cari foto: nama persis dulu, lalu nama sama dengan ekstensi lain.
    Dicari di folder yang ditulis (mis. foto/) dan juga di folder utama."""
    rel = Path(rel_path)
    names = [rel.name] + [rel.stem + e for e in PHOTO_EXTS if rel.stem + e != rel.name]
    for name in names:
        for folder in (APP_DIR / rel.parent, APP_DIR):
            p = folder / name
            if p.is_file():
                return p
    return None


def photo_uri(rel_path):
    if not rel_path:
        return None
    p = find_photo(rel_path)
    if p is None:
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
        "teksAkhir": TEKS_AKHIR,
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
.block-container{padding:6px 0 0 !important;max-width:1100px}
/* bikin area game setinggi layar (HP & laptop) */
.stApp iframe{border:none;height:calc(100vh - 12px) !important;height:calc(100dvh - 12px) !important;min-height:480px}
</style>
"""


def main():
    st.set_page_config(page_title=f"{NAMA}'s Birthday Quest", page_icon="🎂", layout="wide")
    st.markdown(PAGE_CSS, unsafe_allow_html=True)
    components.html(build_game_html(), height=640, scrolling=False)


if __name__ == "__main__":  # Streamlit menjalankan file ini sebagai __main__
    main()
