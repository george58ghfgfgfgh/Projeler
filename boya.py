import streamlit as st
import sqlite3
import pandas as pd

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v18.1", layout="wide")

# CSS: Tasarım
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stSelectbox, .stTextInput, .stNumberInput { margin-bottom: -10px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    div[data-testid="stExpander"] { background-color: white; border: 1px solid #dfe3e6; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- VERİTABANI FONKSİYONLARI ---
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

# --- AKILLI FORMAT FONKSİYONU ---
def format_gram(deger):
    # Eğer sayı tam sayıysa (kalan yoksa) .00 kısmını at, değilse 2 basamak göster
    if deger % 1 == 0:
        return f"{int(deger)}"
    else:
        return f"{deger:,.2f}"

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Sistem Yönetimi")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Yönetici Şifresi", type="password")
        if sifre != "1111":
            st.warning("Lütfen şifre giriniz.")
            st.stop()
    st.divider()
    st.info("Merhaba bebeğim, sistem her zamanki gibi emrinde. ✅")

# --- ANA EKRAN ---
if not admin_modu:
    st.title("🎨 Boya Reçete Hesaplama")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT ad FROM kartelalar")
        k_list = [r[0] for r in cursor.fetchall()]
        secilen_k = st.selectbox("1. KARTELA SEÇ", ["Seçiniz..."] + k_list)

    with col2:
        r_list = []
        if secilen_k != "Seçiniz...":
            cursor.execute("SELECT renk_ad FROM renkler WHERE kartela_ad=?", (secilen_k,))
            r_list = [r[0] for r in cursor.fetchall()]
        secilen_r = st.selectbox("2. RENK SEÇ", ["Seçiniz..."] + r_list)

    with col3:
        t_list = []
        if secilen_r != "Seçiniz...":
            cursor.execute("SELECT tur_ad FROM boya_turleri WHERE kartela_ad=? AND renk_ad=?", (secilen_k, secilen_r))
            t_list = [r[0] for r in cursor.fetchall()]
        secilen_t = st.selectbox("3. BOYA TÜRÜ SEÇ", ["Seçiniz..."] + t_list)

    with col4:
        cursor.execute("SELECT kg_degeri FROM miktar_ayarlari ORDER BY kg_degeri")
        m_list = [f"{r[0]} KG" for r in cursor.fetchall()]
        secilen_m = st.selectbox("4. ÜRETİM MİKTARI", ["Seçiniz..."] + m_list)

    st.write("")
    if st.button("🚀 REÇETEYİ HESAPLA", type="primary", use_container_width=True):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (secilen_t,))
            t_id = cursor.fetchone()[0]
            
            cursor.execute("SELECT bilesen, gramAJ, baz_miktar FROM formuller WHERE tur_id=?", (t_id,))
            bilesenler = cursor.fetchall()
            
            if bilesenler:
                st.success(f"### Reçete: {secilen_r} ({secilen_t}) - Toplam: {h_kg} KG")
                reçete_df = []
                for b, g, baz in bilesenler:
                    o_gr = (g / baz) * (h_kg * 1000)
                    # BURADA AKILLI FORMATI KULLANIYORUZ
                    reçete_df.append({"Bileşen Adı": b, "Miktar (Gram)": format_gram(o_gr)})
                st.table(pd.DataFrame(reçete_df))
            else:
                st.warning("Bu ürün için henüz bir formül girilmemiş.")
        else:
            st.error("Lütfen tüm alanları sırasıyla seçiniz!")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Fabrika Yönetim Paneli")
    
    with st.expander("📂 1. Kartela / Renk / Tür Kayıt", expanded=True):
        c_a, c_b, c_c = st.columns(3)
        with c_a:
            y_k = st.text_input("Yeni Kartela")
            if st.button("Kartelayı Kaydet"):
                cursor.execute("INSERT OR IGNORE INTO kartelalar (ad) VALUES (?)", (y_k,))
                conn.commit(); st.rerun()
        with c_b:
            cursor.execute("SELECT ad FROM kartelalar")
            ks_list = [r[0] for r in cursor.fetchall()]
            ks = st.selectbox("Kartela Seç", ks_list, key="ks")
            y_r = st.text_input("Yeni Renk")
            if st.button("Rengi Kaydet"):
                cursor.execute("INSERT INTO renkler (kartela_ad, renk_ad) VALUES (?, ?)", (ks, y_r))
                conn.commit(); st.rerun()
        with c_c:
            cursor.execute("SELECT DISTINCT renk_ad FROM renkler")
            rs_list = [r[0] for r in cursor.fetchall()]
            rs = st.selectbox("Renk Seç", rs_list, key="rs")
            y_t = st.text_input("Yeni Tür")
            if st.button("Türü Kaydet"):
                cursor.execute("SELECT kartela_ad FROM renkler WHERE renk_ad=?", (rs,))
                k_ait = cursor.fetchone()[0]
                full_t = f"{k_ait} | {rs} | {y_t}"
                cursor.execute("INSERT INTO boya_turleri (kartela_ad, renk_ad, tur_ad) VALUES (?, ?, ?)", (k_ait, rs, full_t))
                conn.commit(); st.rerun()

    with st.expander("⚖️ 2. Üretim Kilogramları"):
        y_gr = st.number_input("Gram Cinsinden Yazın", min_value=0, step=100)
        if st.button("KG Olarak Ekle"):
            cursor.execute("INSERT OR IGNORE INTO miktar_ayarlari (kg_degeri) VALUES (?)", (y_gr/1000,))
            conn.commit(); st.rerun()

    with st.expander("🧪 3. Reçete Formüllerini Yaz", expanded=True):
        cursor.execute("SELECT tur_ad FROM boya_turleri")
        t_sec = st.selectbox("Formül Girişi Yapılacak Tür", ["Seçiniz..."] + [r[0] for r in cursor.fetchall()])
        baz = st.selectbox("Baz Miktar (Gr)", [100, 500, 1000, 5000], index=2)
        
        if t_sec != "Seçiniz...":
            cursor.execute("SELECT id FROM boya_turleri WHERE tur_ad=?", (t_sec,))
            t_id = cursor.fetchone()[0]
            cursor.execute("SELECT bilesen, gramAJ FROM formuller WHERE tur_id=?", (t_id,))
            mevcutlar = cursor.fetchall()
            
            f_rows = []
            for i in range(10):
                rc1, rc2, rc3 = st.columns([0.5, 3, 2])
                with rc1: st.write(f"\n{i+1}")
                b_e = mevcutlar[i][0] if i < len(mevcutlar) else f"Bileşen {i+1}"
                g_e = mevcutlar[i][1] if i < len(mevcutlar) else 0.0
                with rc2: b_y = st.text_input("Ad", value=b_e, key=f"wb_{i}", label_visibility="collapsed")
                with rc3: g_y = st.number_input("Gr", value=float(g_e), key=f"wg_{i}", label_visibility="collapsed")
                f_rows.append((b_y, g_y))
            
            if st.button("💾 FORMÜLÜ KAYDET", type="primary"):
                cursor.execute("DELETE FROM formuller WHERE tur_id=?", (t_id,))
                for b, g in f_rows:
                    if g > 0:
                        cursor.execute("INSERT INTO formuller (tur_id, bilesen, gramAJ, baz_miktar) VALUES (?,?,?,?)", (t_id, b, g, baz))
                conn.commit(); st.success("Kaydedildi!")
