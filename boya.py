import streamlit as st
import sqlite3
import pandas as pd
import os

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Bulut v14", layout="centered")

# --- VERİTABANI BAĞLANTISI ---
def get_db():
    conn = sqlite3.connect('boya_bulut.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# Tabloları oluştur (Aynı mantık, Web uyumlu)
cursor.execute("CREATE TABLE IF NOT EXISTS kartelalar (id INTEGER PRIMARY KEY, ad TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS renkler (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS boya_turleri (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT, tur_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS formuller (id INTEGER PRIMARY KEY, tur_id INTEGER, bilesen TEXT, gramAJ REAL, baz_miktar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS miktar_ayarlari (id INTEGER PRIMARY KEY, kg_degeri REAL UNIQUE)")
conn.commit()

# --- ANA ARAYÜZ ---
st.title("🎨 Boya Fabrikası Otomasyonu")
st.markdown("---")

# Yan Menü (Admin Girişi için)
with st.sidebar:
    st.header("⚙ Yönetim")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Lütfen geçerli şifre girin.")
            st.stop()

if not admin_modu:
    # --- KULLANICI EKRANI ---
    col1, col2 = st.columns(2)
    
    with col1:
        cursor.execute("SELECT ad FROM kartelalar")
        k_list = [r[0] for r in cursor.fetchall()]
        secilen_k = st.selectbox("1. Kartela Seç", ["Seçiniz..."] + k_list)

    with col2:
        if secilen_k != "Seçiniz...":
            cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (secilen_k,))
            r_list = [r[0] for r in cursor.fetchall()]
            secilen_r = st.selectbox("2. Renk Seç", ["Seçiniz..."] + r_list)
        else:
            secilen_r = st.selectbox("2. Renk Seç", ["Önce Kartela Seçin"])

    cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
    t_list = [r[0] for r in cursor.fetchall()]
    secilen_t = st.selectbox("3. Boya Türü Seç", ["Seçiniz..."] + t_list)

    cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
    m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
    secilen_m = st.selectbox("4. Üretilecek Miktar", ["Seçiniz..."] + m_list)

    if st.button("REÇETEYİ HESAPLA", use_container_width=True, type="primary"):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            t_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            bilesenler = cursor.fetchall()
            
            st.success(f"### {secilen_r} - {secilen_t} Reçetesi ({h_kg} KG)")
            
            data = []
            for b, g, baz in bilesenler:
                o_gr = (g / baz) * (h_kg * 1000)
                data.append({"Bileşen": b, "Miktar (Gram)": round(o_gr, 2)})
            
            st.table(pd.DataFrame(data))
        else:
            st.error("Lütfen tüm seçimleri yapın!")

else:
    # --- ADMIN PANELİ (WEB) ---
    st.header("🛠 Admin Yönetim Paneli")
    
    tab1, tab2, tab3 = st.tabs(["Hiyerarşi & Miktar", "Formül Düzenle", "Veri Yedekleme"])
    
    with tab1:
        st.subheader("Kartela/Renk/Tür Ekle")
        yeni_k = st.text_input("Yeni Kartela Adı")
        if st.button("Kartela Ekle"):
            cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yeni_k,))
            conn.commit()
            st.rerun()

        st.subheader("Üretim Miktarı Ekle (Gram)")
        yeni_gr = st.number_input("Gram Cinsinden", min_value=0, step=100)
        if st.button("Miktarı KG Olarak Kaydet"):
            cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (yeni_gr/1000,))
            conn.commit()
            st.rerun()

    with tab2:
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        tum_turler = [r[0] for r in cursor.fetchall()]
        edit_t = st.selectbox("Düzenlenecek Boya Türü", ["Seçiniz..."] + tum_turler)
        
        if edit_t != "Seçiniz...":
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (edit_t,))
            t_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            mevcut_f = cursor.fetchall()
            
            baz_deger = st.selectbox("Baz Miktar (gr)", [100, 500, 1000, 5000], index=2)
            
            updated_rows = []
            for i in range(10):
                c1, c2 = st.columns([3, 1])
                b_val = mevcut_f[i][0] if i < len(mevcut_f) else f"Bileşen {i+1}"
                g_val = mevcut_f[i][1] if i < len(mevcut_f) else 0.0
                
                with c1: b_input = st.text_input(f"Ad {i+1}", value=b_val, key=f"b_{i}")
                with c2: g_input = st.number_input(f"Gram {i+1}", value=float(g_val), key=f"g_{i}")
                updated_rows.append((b_input, g_input))
            
            if st.button("Formülü Güncelle", type="primary"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in updated_rows:
                    if g > 0:
                        cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz_deger))
                conn.commit()
                st.success("Formül başarıyla kaydedildi!")

    with tab3:
        st.subheader("💾 Veritabanı İşlemleri")
        with open("boya_bulut.db", "rb") as f:
            st.download_button("Veritabanını Bilgisayarına İndir (Yedek)", f, file_name="boya_yedek.db")
        
        st.info("Web sitesini yayınladığınızda buradaki veriler bulutta saklanır.")