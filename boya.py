import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v20", layout="wide")

def get_db():
    # Veritabanı adı sabit: Bu dosya GitHub'a yüklenebilir
    conn = sqlite3.connect('boya_otomasyon_ana.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# Tabloları oluştur (Silme işlemleri için FOREIGN KEY desteği önemli)
cursor.execute("CREATE TABLE IF NOT EXISTS kartelalar (id INTEGER PRIMARY KEY, ad TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS renkler (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS boya_turleri (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT, tur_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS formuller (id INTEGER PRIMARY KEY, tur_id INTEGER, bilesen TEXT, gramAJ REAL, baz_miktar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS miktar_ayarlari (id INTEGER PRIMARY KEY, kg_degeri REAL UNIQUE)")
conn.commit()

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
                # İSTEDİĞİN SADE BAŞLIK: Fildişi (Mat) - 5 KG
                tür_temiz = secilen_t.split('|')[-1].strip()
                st.success(f"### {secilen_r} ({tür_temiz}) - {format_gram(h_kg)} KG")
                
                res_data = []
                for b, g, baz in bilesenler:
                    o_gr = (g / baz) * (h_kg * 1000)
                    res_data.append({"Bileşen Adı": b, "Miktar (Gram)": format_gram(o_gr)})
                st.table(pd.DataFrame(res_data))
            else:
                st.warning("Bu ürün için henüz formül girilmemiş.")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Fabrika Yönetimi")
    t1, t2, t3 = st.tabs(["➕ Veri Ekle / Sil", "🧪 Formüller", "💾 Veritabanı Aktar"])

    with t1:
        # KARTELA BÖLÜMÜ
        st.subheader("📁 Kartela Yönetimi")
        c1, c2 = st.columns([3, 1])
        with c1: yk = st.text_input("Yeni Kartela Adı")
        with c2: 
            if st.button("Ekle", key="k_ekle"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yk,))
                conn.commit(); st.rerun()
        
        cursor.execute("SELECT ad FROM kartelalar")
        ks_sil = st.selectbox("Silinecek Kartela", ["Seç..."] + [r[0] for r in cursor.fetchall()])
        if st.button("Kartelayı ve Bağlı Tüm Renkleri Sil"):
            cursor.execute("DELETE FROM kartelalar WHERE ad=?", (ks_sil,))
            cursor.execute("DELETE FROM renkler WHERE kartela_ad=?", (ks_sil,))
            cursor.execute("DELETE FROM boya_turleri WHERE kartela_ad=?", (ks_sil,))
            conn.commit(); st.rerun()

        st.divider()
        # RENK BÖLÜMÜ
        st.subheader("🎨 Renk Yönetimi")
        cursor.execute("SELECT ad FROM kartelalar")
        k_sec_r = st.selectbox("Kartela Seç (Renk İçin)", [r[0] for r in cursor.fetchall()], key="k_r")
        c3, c4 = st.columns([3, 1])
        with c3: yr = st.text_input("Yeni Renk Adı")
        with c4:
            if st.button("Ekle", key="r_ekle"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (k_sec_r, yr))
                conn.commit(); st.rerun()

        cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (k_sec_r,))
        rs_sil = st.selectbox("Silinecek Renk", ["Seç..."] + [r[0] for r in cursor.fetchall()])
        if st.button("Rengi ve Bağlı Türleri Sil"):
            cursor.execute("DELETE FROM renkler WHERE renk_ad=? AND kartela_ad=?", (rs_sil, k_sec_r))
            cursor.execute("DELETE FROM boya_turleri WHERE renk_ad=? AND kartela_ad=?", (rs_sil, k_sec_r))
            conn.commit(); st.rerun()

    with t2:
        # Formül düzenleme (v19.1 ile aynı mantık)
        st.subheader("🧪 Formül Girişi")
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        edit_t = st.selectbox("Tür Seç", ["Seçiniz..."] + [r[0] for r in cursor.fetchall()])
        if edit_t != "Seçiniz...":
            # (Formül giriş tablo kodları buraya gelecek...)
            st.info("Buradan formül girişlerini yapabilirsin.")

    with t3:
        st.subheader("📤 GitHub / Yedekleme")
        st.write("Veritabanını bilgisayarına indirip GitHub'a yükleyebilirsin.")
        with open("boya_otomasyon_ana.db", "rb") as f:
            st.download_button("Veritabanını İndir", f, file_name="boya_otomasyon_ana.db")
