import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v21", layout="wide")

# CSS: Tasarım
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    div[data-testid="stExpander"] { background-color: white; border: 1px solid #dfe3e6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_db():
    conn = sqlite3.connect('boya_otomasyon_ana.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# Tablolar
cursor.execute("CREATE TABLE IF NOT EXISTS kartelalar (id INTEGER PRIMARY KEY, ad TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS renkler (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS boya_turleri (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT, tur_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS formuller (id INTEGER PRIMARY KEY, tur_id INTEGER, bilesen TEXT, gramAJ REAL, baz_miktar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS miktar_ayarlari (id INTEGER PRIMARY KEY, kg_degeri REAL UNIQUE)")
conn.commit()

# Sayı Formatlama (Tam sayı ise sıfırsız, küsuratlıysa 2 basamak)
def format_gram(deger):
    yuvarlanmis = round(deger, 2)
    if yuvarlanmis % 1 == 0:
        return f"{int(yuvarlanmis)}"
    else:
        return f"{yuvarlanmis:,.2f}".replace(".00", "")

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Yönetim")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Şifre Gerekli")
            st.stop()
    st.divider()
    st.info("Sistem Hazır Bebeğim ✅")

# --- ANA EKRAN ---
if not admin_modu:
    st.title("🎨 Reçete Hesaplama")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cursor.execute("SELECT ad FROM kartelalar")
        k_list = [r[0] for r in cursor.fetchall()]
        secilen_k = st.selectbox("1. KARTELA", ["Seçiniz..."] + k_list)
    with col2:
        r_list = []
        if secilen_k != "Seçiniz...":
            cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (secilen_k,))
            r_list = [r[0] for r in cursor.fetchall()]
        secilen_r = st.selectbox("2. RENK", ["Seçiniz..."] + r_list)
    with col3:
        t_list = []
        if secilen_r != "Seçiniz...":
            cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
            t_list = [r[0] for r in cursor.fetchall()]
        secilen_t = st.selectbox("3. TÜR", ["Seçiniz..."] + t_list)
    with col4:
        cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
        m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
        secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + m_list)

    if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            bilesenler = cursor.fetchall()
            
            if bilesenler:
                # --- TAM İSTEDİĞİN SADE BAŞLIK DÜZENİ ---
                # "Kartela Renk Tür Miktar" (Aralarda sadece birer boşluk var)
                tür_adi = secilen_t.split('|')[-1].strip()
                baslik = f"{secilen_k} {secilen_r} {tür_adi} {secilen_m}"
                
                st.success(f"### {baslik}")
                
                res_data = []
                for b, g, baz in bilesenler:
                    o_gr = (g / baz) * (h_kg * 1000)
                    res_data.append({"Bileşen Adı": b, "Miktar (Gram)": format_gram(o_gr)})
                st.table(pd.DataFrame(res_data))
            else:
                st.warning("Formül Bulunamadı.")
        else:
            st.error("Lütfen seçimleri tamamlayın!")

else:
    # --- ADMİN PANELİ (Ekleme/Silme ve Formüller) ---
    st.title("🛠️ Fabrika Yönetimi")
    t1, t2 = st.tabs(["➕ Veri Ekle / Sil", "🧪 Formüller"])

    with t1:
        # Kartela Ekle/Sil
        st.subheader("📂 Kartela")
        c1, c2 = st.columns([3, 1])
        with c1: yk = st.text_input("Yeni Kartela")
        with c2: 
            if st.button("Ekle", key="k_ekle"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yk,))
                conn.commit(); st.rerun()
        
        cursor.execute("SELECT ad FROM kartelalar")
        k_listesi = [r[0] for r in cursor.fetchall()]
        sil_k = st.selectbox("Silinecek Kartela", ["Seç..."] + k_listesi)
        if st.button("Kartelayı Sil"):
            cursor.execute("DELETE FROM kartelalar WHERE ad=?", (sil_k,))
            cursor.execute("DELETE FROM renkler WHERE kartela_ad=?", (sil_k,))
            cursor.execute("DELETE FROM boya_turleri WHERE kartela_ad=?", (sil_k,))
            conn.commit(); st.rerun()

        st.divider()
        # Renk Ekle/Sil
        st.subheader("🎨 Renk")
        k_sec_r = st.selectbox("Hangi Kartela?", k_listesi, key="k_r_admin")
        c3, c4 = st.columns([3, 1])
        with c3: yr = st.text_input("Yeni Renk")
        with c4:
            if st.button("Ekle", key="r_ekle"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (k_sec_r, yr))
                conn.commit(); st.rerun()
        
        cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (k_sec_r,))
        r_sil_list = [r[0] for r in cursor.fetchall()]
        sil_r = st.selectbox("Silinecek Renk", ["Seç..."] + r_sil_list)
        if st.button("Rengi Sil"):
            cursor.execute("DELETE FROM renkler WHERE renk_ad=? AND kartela_ad=?", (sil_r, k_sec_r))
            cursor.execute("DELETE FROM boya_turleri WHERE renk_ad=? AND kartela_ad=?", (sil_r, k_sec_r))
            conn.commit(); st.rerun()

    with t2:
        # Formül Düzenleme
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        edit_t = st.selectbox("Tür Seç", ["Seçiniz..."] + [r[0] for r in cursor.fetchall()])
        baz = st.selectbox("Baz Miktar", [100, 500, 1000, 5000], index=2)
        if edit_t != "Seçiniz...":
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (edit_t,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ FROM formuller WHERE tur_id=?", (t_id,))
            mevcutlar = cursor.fetchall()
            f_rows = []
            for i in range(10):
                rc1, rc2 = st.columns([3, 1])
                b_e = mevcutlar[i][0] if i < len(mevcutlar) else f"Bileşen {i+1}"
                g_e = mevcutlar[i][1] if i < len(mevcutlar) else 0.0
                b_y = st.text_input(f"B{i}", b_e, key=f"wb_{i}", label_visibility="collapsed")
                g_y = st.number_input(f"G{i}", float(g_e), key=f"wg_{i}", label_visibility="collapsed")
                f_rows.append((b_y, g_y))
            if st.button("KAYDET"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in f_rows:
                    if g > 0: cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz))
                conn.commit(); st.success("Kaydedildi!")
