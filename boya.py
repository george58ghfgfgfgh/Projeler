import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Cloud v24", layout="wide")

# --- GOOGLE SHEETS BAĞLANTISI ---
# Senin paylaştığın tablo linkini buraya sabitliyoruz
url = "https://docs.google.com/spreadsheets/d/1XhEwmzpS7-Y5ndJ_zG4ZHqHpYo7UIX6HpSGBIiowfZo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Sayı Formatlama
def format_gram(deger):
    yuvarlanmis = round(deger, 2)
    return f"{int(yuvarlanmis)}" if yuvarlanmis % 1 == 0 else f"{yuvarlanmis:,.2f}".replace(".00", "")

# --- VERİ İŞLEMLERİ ---
def get_all_data(worksheet):
    return conn.read(spreadsheet=url, worksheet=worksheet).dropna(how="all")

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Bulut Yönetimi")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.stop()
    st.success("Google Sheets Bağlantısı Aktif ✅")

# --- ANA EKRAN (KULLANICI) ---
if not admin_modu:
    st.title("🎨 Reçete Hesaplama")
    
    # Verileri Buluttan Çek
    df_k = get_all_data("Kartelalar")
    df_r = get_all_data("Renkler")
    df_t = get_all_data("Türler")
    df_m = get_all_data("Miktarlar")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        secilen_k = st.selectbox("1. KARTELA", ["Seçiniz..."] + df_k["ad"].tolist())
    with c2:
        r_list = df_r[df_r["kartela_ad"] == secilen_k]["renk_ad"].tolist() if secilen_k != "Seçiniz..." else []
        secilen_r = st.selectbox("2. RENK", ["Seçiniz..."] + r_list)
    with c3:
        t_list = df_t[(df_t["kartela_ad"] == secilen_k) & (df_t["renk_ad"] == secilen_r)]["tur_ad"].tolist() if secilen_r != "Seçiniz..." else []
        t_display = [t.split('|')[-1].strip() for t in t_list]
        secilen_t_dis = st.selectbox("3. TÜR", ["Seçiniz..."] + t_display)
    with c4:
        m_vals = df_m["kg_degeri"].sort_values().tolist()
        secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + [f"{x} KG" for x in m_vals])

    if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
        if "Seçiniz" not in [secilen_k, secilen_r, secilen_t_dis, secilen_m]:
            h_kg = float(secilen_m.replace(" KG", ""))
            df_f = get_all_data("Formüller")
            full_t = f"{secilen_k} | {secilen_r} | {secilen_t_dis}"
            reçete = df_f[df_f["tur_ad"] == full_t]
            
            if not reçete.empty:
                st.success(f"### {secilen_k} {secilen_r} {secilen_t_dis} {secilen_m}")
                res = []
                for _, row in reçete.iterrows():
                    mikt = (row["gramAJ"] / row["baz_miktar"]) * (h_kg * 1000)
                    res.append({"Bileşen Adı": row["bilesen"], "Miktar (Gram)": format_gram(mikt)})
                st.table(pd.DataFrame(res))
            else:
                st.warning("Bu tür için formül bulunamadı.")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Bulut Fabrika Yönetimi")
    t1, t2 = st.tabs(["➕ Veri Ekle/Sil", "🧪 Formül Girişi"])

    with t1:
        st.subheader("Google Sheets Üzerinden Yönetim")
        st.info("Bebeğim, şu an en güvenli yol verileri doğrudan Google Sheets dosyan içinden eklemek veya silmektir. Sayfayı yenilediğinde uygulama yeni verileri otomatik çeker.")
        st.link_button("📂 Google Tabloyu Aç ve Düzenle", url)
        
        # Buraya basit ekleme butonları da eklenebilir ancak ilk aşamada 
        # doğrudan tabloyu kullanmak hataları sıfıra indirir.

    with t2:
        st.subheader("🧪 Formül Rehberi")
        st.write("Formüller sayfasındaki 'tur_ad' kısmına şu formatta yazmalısın:")
        st.code(f"Kartela Adı | Renk Adı | Tür Adı")
