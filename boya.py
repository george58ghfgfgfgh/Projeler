import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI (Genişliği Masaüstü Gibi Sınırla) ---
st.set_page_config(page_title="Boya Fabrikası", layout="wide")

# CSS ile Görünümü Masaüstüne Benzetelim
st.markdown("""
    <style>
    .stTextInput, .stNumberInput { margin-bottom: -15px; }
    .stButton>button { width: 100%; height: 3em; background-color: #27ae60; color: white; font-weight: bold; }
    .main { background-color: #f0f2f6; }
    </style>
    """, unsafe_allow_html=True)

def get_db():
    conn = sqlite3.connect('boya_bulut.db', check_same_thread=False)
    return conn

conn = get_db()
cursor = conn.cursor()

# --- ANA BAŞLIK ---
st.title("🖥️ Boya Fabrikası (Masaüstü Modu)")

# --- YAN PANEL (ADMİN) ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Şifre Gerekli")
            st.stop()

if not admin_modu:
    # --- KULLANICI EKRANI (Tkinter Benzeri Kompakt Düzen) ---
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

    with c3:
        t_list = []
        if secilen_r != "Seçiniz...":
            cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
            t_list = [r[0] for r in cursor.fetchall()]
        secilen_t = st.selectbox("3. TÜR", ["Seçiniz..."] + t_list)

    with c4:
        cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
        m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
        secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + m_list)

    if st.button("HESAPLA"):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            bilesenler = cursor.fetchall()
            
            st.markdown(f"### 📋 {secilen_r} - {secilen_t} Reçetesi")
            res_data = []
            for b, g, baz in bilesenler:
                o_gr = (g / baz) * (h_kg * 1000)
                res_data.append({"Bileşen": b, "Miktar (Gr)": f"{o_gr:.2f}"})
            st.table(pd.DataFrame(res_data))

else:
    # --- ADMİN PANELİ (MASAÜSTÜ GÖRÜNÜMÜ) ---
    st.subheader("🛠️ Formül Düzenleme Ekranı")
    
    # Hiyerarşi Seçimi
    col_a, col_b = st.columns(2)
    with col_a:
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        tum_turler = [r[0] for r in cursor.fetchall()]
        edit_t = st.selectbox("Düzenlenecek Boya Türünü Seçin", ["Seçiniz..."] + tum_turler)
    with col_b:
        baz_deger = st.selectbox("Baz Miktar (Gram)", [100, 500, 1000, 5000], index=2)

    if edit_t != "Seçiniz...":
        cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (edit_t,))
        t_id = cursor.fetchone()[0]
        cursor.execute("SELECT bilesen, gramAJ FROM formuller WHERE tur_id=?", (t_id,))
        mevcut_f = cursor.fetchall()

        st.markdown("---")
        # 10 Satırlık Yan Yana Düzen (Tkinter gibi)
        updated_rows = []
        for i in range(10):
            row_c1, row_c2, row_c3 = st.columns([0.5, 3, 2])
            with row_c1: st.write(f"\n\n**{i+1}.**")
            
            b_val = mevcut_f[i][0] if i < len(mevcut_f) else f"Bileşen {i+1}"
            g_val = mevcut_f[i][1] if i < len(mevcut_f) else 0.0
            
            with row_c2: b_in = st.text_input(f"Bileşen Adı", value=b_val, key=f"b_{i}", label_visibility="collapsed")
            with row_c3: g_in = st.number_input(f"Gramaj", value=float(g_val), key=f"g_{i}", label_visibility="collapsed")
            updated_rows.append((b_in, g_in))

        if st.button("FORMÜLÜ KAYDET"):
            cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
            for b, g in updated_rows:
                if g > 0:
                    cursor.execute("INSERT INTO formuller (id, tur_id, bilesen, gramAJ, baz_miktar) VALUES (NULL, ?,?,?,?)", (t_id, b, g, baz_deger))
            conn.commit()
            st.success("Başarıyla Kaydedildi! ✅")

    st.markdown("---")
    st.subheader("📊 Kartela & Miktar Yönetimi")
    c_k1, c_k2 = st.columns(2)
    with c_k1:
        y_k = st.text_input("Yeni Kartela Ekle")
        if st.button("Kartelayı Sisteme İşle"):
            cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (y_k,))
            conn.commit(); st.rerun()
    with c_k2:
        y_gr = st.number_input("Yeni Üretim Miktarı (Gram)", min_value=0)
        if st.button("Miktarı Kaydet"):
            cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (y_gr/1000,))
            conn.commit(); st.rerun()
