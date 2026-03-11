import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v22.1", layout="wide")

def get_db():
    conn = sqlite3.connect('boya_otomasyon_ana.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# Tabloları oluştur
cursor.execute("CREATE TABLE IF NOT EXISTS kartelalar (id INTEGER PRIMARY KEY, ad TEXT UNIQUE)")
cursor.execute("CREATE TABLE IF NOT EXISTS renkler (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS boya_turleri (id INTEGER PRIMARY KEY, kartela_ad TEXT, renk_ad TEXT, tur_ad TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS formuller (id INTEGER PRIMARY KEY, tur_id INTEGER, bilesen TEXT, gramAJ REAL, baz_miktar REAL)")
cursor.execute("CREATE TABLE IF NOT EXISTS miktar_ayarlari (id INTEGER PRIMARY KEY, kg_degeri REAL UNIQUE)")
conn.commit()

def format_gram(deger):
    yuvarlanmis = round(deger, 2)
    return f"{int(yuvarlanmis)}" if yuvarlanmis % 1 == 0 else f"{yuvarlanmis:,.2f}".replace(".00", "")

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Yönetim")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Erişim Bekleniyor...")
            st.stop()

# --- ANA EKRAN (KULLANICI) ---
if not admin_modu:
    st.title("🎨 Reçete Hesaplama")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        cursor.execute("SELECT ad FROM kartelalar")
        k_list = [r[0] for r in cursor.fetchall()]
        secilen_k = st.selectbox("1. KARTELA", ["Seçiniz..."] + k_list)
    with c2:
        r_list = []
        if secilen_k != "Seçiniz...":
            cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (secilen_k,))
            r_list = [r[0] for r in cursor.fetchall()]
        secilen_r = st.selectbox("2. RENK", ["Seçiniz..."] + r_list)
    with c3: # HATALI KISIM DÜZELTİLDİ
        t_list = []
        if secilen_r != "Seçiniz...":
            cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
            t_list = [r[0] for r in cursor.fetchall()]
        secilen_t = st.selectbox("3. TÜR", ["Seçiniz..."] + t_list)
    with c4:
        cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
        m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
        secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + m_list)

    if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            res = cursor.fetchone()
            if res:
                t_id = res[0]
                cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
                bilesenler = cursor.fetchall()
                if bilesenler:
                    tür_adi = secilen_t.split('|')[-1].strip()
                    # İSTEDİĞİN SADE BAŞLIK DÜZENİ
                    st.success(f"### {secilen_k} {secilen_r} {tür_adi} {secilen_m}")
                    res_df = [{"Bileşen Adı": b, "Miktar (Gram)": format_gram((g / baz) * (h_kg * 1000))} for b, g, baz in bilesenler]
                    st.table(pd.DataFrame(res_df))
                else: st.warning("Formül girilmemiş.")
        else: st.error("Eksik seçim yaptınız.")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Fabrika Yönetimi")
    tab_ekle, tab_formul, tab_miktar = st.tabs(["➕ Veri Yönetimi", "🧪 Formül Girişi", "⚖️ Miktar Ayarı"])

    with tab_ekle:
        # 1. KARTELA
        st.subheader("1. Adım: Kartela")
        col_k1, col_k2 = st.columns([3, 1])
        with col_k1: yk = st.text_input("Yeni Kartela Adı")
        with col_k2: 
            if st.button("Kartela Ekle"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (yk,))
                conn.commit(); st.rerun()
        
        cursor.execute("SELECT ad FROM kartelalar")
        k_options = [r[0] for r in cursor.fetchall()]
        sil_k = st.selectbox("Sililecek Kartela", ["Seç..."] + k_options)
        if st.button("Kartelayı Sil"):
            cursor.execute("DELETE FROM kartelalar WHERE ad=?", (sil_k,))
            conn.commit(); st.rerun()

        st.divider()
        # 2. RENK
        st.subheader("2. Adım: Renk")
        sel_k_for_r = st.selectbox("Kartela Seç", k_options)
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1: yr = st.text_input("Yeni Renk Adı")
        with col_r2:
            if st.button("Renk Ekle"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (sel_k_for_r, yr))
                conn.commit(); st.rerun()
        
        cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (sel_k_for_r,))
        r_options = [r[0] for r in cursor.fetchall()]
        sil_r = st.selectbox("Silinecek Renk", ["Seç..."] + r_options)
        if st.button("Rengi Sil"):
            cursor.execute("DELETE FROM renkler WHERE renk_ad=? AND kartela_ad=?", (sil_r, sel_k_for_r))
            conn.commit(); st.rerun()

        st.divider()
        # 3. TÜR
        st.subheader("3. Adım: Tür")
        sel_r_for_t = st.selectbox("Renk Seç", r_options)
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1: yt = st.text_input("Yeni Tür (Mat vb.)")
        with col_t2:
            if st.button("Tür Ekle"):
                full_t = f"{sel_k_for_r} | {sel_r_for_t} | {yt}"
                cursor.execute("INSERT INTO boya_turleri (kartela_ad, renk_ad, tur_ad) VALUES (?, ?, ?)", (sel_k_for_r, sel_r_for_t, full_t))
                conn.commit(); st.rerun()

    with tab_formul:
        st.subheader("🧪 Formül Girişi")
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        t_list_f = [r[0] for r in cursor.fetchall()]
        edit_t = st.selectbox("Tür Seç", ["Seçiniz..."] + t_list_f)
        baz_val = st.selectbox("Baz Miktar", [100, 500, 1000, 5000], index=2)
        if edit_t != "Seçiniz...":
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (edit_t,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ FROM formuller WHERE tur_id=?", (t_id,))
            mevcutlar = cursor.fetchall()
            f_rows = []
            for i in range(10):
                c_b, c_g = st.columns([3, 1])
                b_val = mevcutlar[i][0] if i < len(mevcutlar) else f"Bileşen {i+1}"
                g_val = mevcutlar[i][1] if i < len(mevcutlar) else 0.0
                with c_b: b_in = st.text_input(f"Ad {i}", b_val, key=f"b_{i}", label_visibility="collapsed")
                with c_g: g_in = st.number_input(f"Gr {i}", float(g_val), key=f"g_{i}", label_visibility="collapsed")
                f_rows.append((b_in, g_in))
            if st.button("KAYDET"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in f_rows:
                    if g > 0: cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz_val))
                conn.commit(); st.success("Kaydedildi!")

    with tab_miktar:
        st.subheader("⚖️ Miktar")
        y_gram = st.number_input("Gramaj", step=100)
        if st.button("Ekle"):
            cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (y_gram/1000,))
            conn.commit(); st.rerun()
