import streamlit as st
import sqlite3
import pandas as pd
import shutil
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v16", layout="wide")

# Veritabanı Bağlantısı
def get_db():
    conn = sqlite3.connect('boya_otomasyon_ana.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# Tabloları İlk Kez Oluştur (Eksiksiz Şema)
cursor.execute("CREATE TABLE IF NOT EXISTS kartelalar (id INTEGER PRIMARY KEY, ad TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS renkler (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS boya_turleri (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT, tur_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS formuller (id INTEGER PRIMARY KEY, tur_id INTEGER, bilesen TEXT, gramAJ REAL, baz_miktar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS miktar_ayarlari (id INTEGER PRIMARY KEY, kg_degeri REAL UNIQUE)")
conn.commit()

# --- CSS: Masaüstü Görünümü Sıkıştırma ---
st.markdown("""
    <style>
    .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: -10px; }
    .stButton>button { width: 100%; font-weight: bold; border-radius: 5px; }
    div[data-testid="stExpander"] { background-color: #f8f9fa; border: 1px solid #ddd; }
    </style>
    """, unsafe_allow_html=True)

# --- YAN PANEL (ADMİN) ---
with st.sidebar:
    st.title("🛡️ Güvenlik")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Erişim Reddedildi")
            st.stop()
    st.markdown("---")
    st.info("Sistem Durumu: Çevrimiçi ✅")

# --- ANA EKRAN ---
if not admin_modu:
    st.title("🎨 Boya Fabrikası Reçete Sistemi")
    
    # Seçim Alanları (Yan Yana 4 Kolon)
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        cursor.execute("SELECT ad FROM kartelalar")
        k_list = [r[0] for r in cursor.fetchall()]
        secilen_k = st.selectbox("1. KARTELA SEÇ", ["Seçiniz..."] + k_list)

    with c2:
        r_list = []
        if secilen_k != "Seçiniz...":
            cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (secilen_k,))
            r_list = [r[0] for r in cursor.fetchall()]
        secilen_r = st.selectbox("2. RENK SEÇ", ["Seçiniz..."] + r_list)

    with c3:
        t_list = []
        if secilen_r != "Seçiniz...":
            cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
            t_list = [r[0] for r in cursor.fetchall()]
        secilen_t = st.selectbox("3. BOYA TÜRÜ SEÇ", ["Seçiniz..."] + t_list)

    with c4:
        cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
        m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
        secilen_m = st.selectbox("4. ÜRETİLECEK MİKTAR", ["Seçiniz..."] + m_list)

    if st.button("🚀 REÇETEYİ HESAPLA", type="primary"):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            bilesenler = cursor.fetchall()
            
            st.markdown(f"### 📋 Üretim Reçetesi: {secilen_r}")
            reçete_df = []
            for b, g, baz in bilesenler:
                hesap = (g / baz) * (h_kg * 1000)
                reçete_df.append({"Bileşen": b, "Gereken Miktar (Gram)": f"{hesap:,.2f}"})
            
            st.table(pd.DataFrame(reçete_df))
        else:
            st.error("Lütfen tüm alanları seçin!")

else:
    # --- ADMİN PANELİ (MASAÜSTÜNDEKİ TÜM ÖZELLİKLER) ---
    st.title("🛠️ Fabrika Yönetim Merkezi")
    
    # 1. BÖLÜM: Hiyerarşik Ekleme
    with st.expander("📂 1. Kartela / Renk / Tür Yönetimi", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Kartela")
            yeni_k = st.text_input("Yeni Kartela Adı", key="ak")
            if st.button("Kartela Ekle"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yeni_k,))
                conn.commit(); st.rerun()
        
        with col2:
            st.subheader("Renk")
            cursor.execute("SELECT ad FROM kartelalar")
            k_sec = st.selectbox("Hangi Kartelaya?", [r[0] for r in cursor.fetchall()], key="aks")
            yeni_r = st.text_input("Yeni Renk Adı", key="ar")
            if st.button("Renk Ekle"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (k_sec, yeni_r))
                conn.commit(); st.rerun()

        with col3:
            st.subheader("Boya Türü")
            cursor.execute("SELECT DISTINCT renk_ad FROM renkler")
            r_sec = st.selectbox("Hangi Renge?", [r[0] for r in cursor.fetchall()], key="ars")
            yeni_t = st.text_input("Yeni Boya Türü", key="at")
            if st.button("Tür Ekle"):
                # Masaüstündeki "Kartela | Renk | Tür" birleştirme mantığı
                cursor.execute("SELECT kartela_ad FROM renkler WHERE renk_ad=?", (r_sec,))
                k_ait = cursor.fetchone()[0]
                full_t = f"{k_ait} | {r_sec} | {yeni_t}"
                cursor.execute("INSERT INTO boya_turleri (kartela_ad, renk_ad, tur_ad) VALUES (?, ?, ?)", (k_ait, r_sec, full_t))
                conn.commit(); st.rerun()

    # 2. BÖLÜM: Miktar Ayarları
    with st.expander("⚖️ 2. Üretim Miktarlarını Yönet"):
        mc1, mc2 = st.columns(2)
        with mc1:
            y_gr = st.number_input("Eklenecek Miktar (Gram Cinsinden)", min_value=0, step=100)
            if st.button("Kilogram Olarak Listeye İşle"):
                cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (y_gr/1000,))
                conn.commit(); st.rerun()
        with mc2:
            st.write("Mevcut Miktarlar")
            cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
            st.write([f"{r[0]} KG" for r in cursor.fetchall()])
            if st.button("Tüm Miktarları Temizle"):
                cursor.execute("DELETE FROM miktar_ayarlari")
                conn.commit(); st.rerun()

    # 3. BÖLÜM: Formül Girişi (Masaüstü Düzeni)
    with st.expander("🧪 3. Reçete Formülleri Düzenle", expanded=True):
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        secili_tur = st.selectbox("Formülü Düzenlenecek Türü Seçin", ["Seçiniz..."] + [r[0] for r in cursor.fetchall()])
        baz_secimi = st.selectbox("Baz Miktar (Gram)", [100, 500, 1000, 5000], index=2)
        
        if secili_tur != "Seçiniz...":
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secili_tur,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ FROM formuller WHERE tur_id=?", (t_id,))
            mevcutlar = cursor.fetchall()
            
            st.markdown("#### Bileşen Giriş Tablosu")
            yeni_formül_verisi = []
            for i in range(10):
                rc1, rc2, rc3 = st.columns([0.5, 3, 2])
                with rc1: st.write(f"\n{i+1}")
                b_esk = mevcutlar[i][0] if i < len(mevcutlar) else f"Bileşen {i+1}"
                g_esk = mevcutlar[i][1] if i < len(mevcutlar) else 0.0
                with rc2: b_yeni = st.text_input("Bileşen Adı", value=b_esk, key=f"wb_{i}", label_visibility="collapsed")
                with rc3: g_yeni = st.number_input("Gram", value=float(g_esk), key=f"wg_{i}", label_visibility="collapsed")
                yeni_formül_verisi.append((b_yeni, g_yeni))
            
            if st.button("💾 FORMÜLÜ VERİTABANINA KAYDET", type="primary"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in yeni_formül_verisi:
                    if g > 0:
                        cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz_secimi))
                conn.commit()
                st.success("Formül Başarıyla Güncellendi!")

    # 4. BÖLÜM: Yedekleme
    with st.expander("💾 4. Veritabanı Yedekleme & Geri Yükleme"):
        if st.download_button("📂 Mevcut Veritabanını İndir", data=open('boya_otomasyon_ana.db', 'rb'), file_name="boya_yedek.db"):
            st.write("Yedek Hazırlandı.")
