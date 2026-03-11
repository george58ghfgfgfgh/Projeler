import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v19", layout="wide")

# CSS: Tasarım
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .delete-btn>button { background-color: #ff4b4b; color: white; border: none; }
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

def format_gram(deger):
    if deger % 1 == 0: return f"{int(deger)}"
    else: return f"{deger:,.2f}"

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
                # İSTEDİĞİN SADE BAŞLIK: Sadece parantez içindekiler
                # Örn: (Fildişi) (Mat)
                st.success(f"### ({secilen_r}) ({secilen_t}) - {h_kg} KG")
                
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
    # --- ADMİN PANELİ ---
    st.title("🛠️ Fabrika Yönetimi")
    
    t1, t2, t3, t4 = st.tabs(["➕ Ekleme", "🧪 Formüller", "⚖️ Miktarlar", "🗑️ Veri Silme"])

    with t1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Kartela")
            yk = st.text_input("Yeni Kartela")
            if st.button("Kartela Ekle"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yk,))
                conn.commit(); st.rerun()
        with c2:
            st.subheader("Renk")
            cursor.execute("SELECT ad FROM kartelalar")
            ks = st.selectbox("Kartela Seç", [r[0] for r in cursor.fetchall()])
            yr = st.text_input("Yeni Renk")
            if st.button("Renk Ekle"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (ks, yr))
                conn.commit(); st.rerun()
        with c3:
            st.subheader("Tür")
            cursor.execute("SELECT DISTINCT renk_ad FROM renkler")
            rs = st.selectbox("Renk Seç", [r[0] for r in cursor.fetchall()])
            yt = st.text_input("Yeni Tür")
            if st.button("Tür Ekle"):
                cursor.execute("SELECT kartela_ad FROM renkler WHERE renk_ad=?", (rs,))
                k_ait = cursor.fetchone()[0]
                full_t = f"{k_ait} | {rs} | {yt}"
                cursor.execute("INSERT INTO boya_turleri (kartela_ad, renk_ad, tur_ad) VALUES (?, ?, ?)", (k_ait, rs, full_t))
                conn.commit(); st.rerun()

    with t2:
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        edit_t = st.selectbox("Formül Türü", ["Seçiniz..."] + [r[0] for r in cursor.fetchall()])
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
                with rc1: b_y = st.text_input(f"B{i+1}", b_e, key=f"wb_{i}", label_visibility="collapsed")
                with rc2: g_y = st.number_input(f"G{i+1}", float(g_e), key=f"wg_{i}", label_visibility="collapsed")
                f_rows.append((b_y, g_y))
            if st.button("FORMÜLÜ KAYDET"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in f_rows:
                    if g > 0: cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz))
                conn.commit(); st.success("Kaydedildi!")

    with t3:
        y_gr = st.number_input("Gramaj Ekle", step=100)
        if st.button("KG Olarak Kaydet"):
            cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (y_gr/1000,))
            conn.commit(); st.rerun()

    with t4:
        st.subheader("🗑️ Kayıtlı Verileri Sil")
        st.warning("Dikkat: Sildiğiniz veriyle bağlantılı tüm alt kayıtlar (formüller vb.) silinecektir.")
        
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            cursor.execute("SELECT ad FROM kartelalar")
            s_k_list = [r[0] for r in cursor.fetchall()]
            sil_k = st.selectbox("Kartela Sil", ["Seç..."] + s_k_list)
            if st.button("Kartelayı Sil", type="secondary"):
                cursor.execute("DELETE FROM kartelalar WHERE ad=?", (sil_k,))
                cursor.execute("DELETE FROM renkler WHERE kartela_ad=?", (sil_k,))
                cursor.execute("DELETE FROM boya_turleri WHERE kartela_ad=?", (sil_k,))
                conn.commit(); st.rerun()

        with col_s2:
            cursor.execute("SELECT renk_ad FROM renkler")
            s_r_list = [r[0] for r in cursor.fetchall()]
            sil_r = st.selectbox("Renk Sil", ["Seç..."] + s_r_list)
            if st.button("Rengi Sil"):
                cursor.execute("DELETE FROM renkler WHERE renk_ad=?", (sil_r,))
                cursor.execute("DELETE FROM boya_turleri WHERE renk_ad=?", (sil_r,))
                conn.commit(); st.rerun()

        with col_s3:
            cursor.execute("SELECT tur_ad FROM boya_turleri")
            s_t_list = [r[0] for r in cursor.fetchall()]
            sil_t = st.selectbox("Tür Sil", ["Seç..."] + s_t_list)
            if st.button("Türü Sil"):
                cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (sil_t,))
                t_id_sil = cursor.fetchone()[0]
                cursor.execute("DELETE FROM boya_turleri WHERE id=?", (t_id_sil,))
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id_sil,))
                conn.commit(); st.rerun()
