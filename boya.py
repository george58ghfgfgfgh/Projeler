import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import urllib.parse

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v25", layout="wide")

# --- BAĞLANTI AYARLARI ---
# Senin paylaştığın ana link
url = "https://docs.google.com/spreadsheets/d/1XhEwmzpS7-Y5ndJ_zG4ZHqHpYo7UIX6HpSGBIiowfZo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Sayı Formatlama Fonksiyonu
def format_gram(deger):
    yuvarlanmis = round(deger, 2)
    return f"{int(yuvarlanmis)}" if yuvarlanmis % 1 == 0 else f"{yuvarlanmis:,.2f}".replace(".00", "")

# Veri Çekme Fonksiyonu (Hata Korumalı)
def get_all_data(worksheet):
    try:
        # Taze veri çekmek için ttl=0 kullanıyoruz
        df = conn.read(spreadsheet=url, worksheet=worksheet, ttl=0)
        df = df.dropna(how="all") # Boş satırları temizle
        df.columns = df.columns.str.strip() # Sütun isimlerindeki boşlukları temizle
        return df
    except Exception as e:
        return pd.DataFrame() # Hata olursa boş tablo dön

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Fabrika Yönetimi")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.warning("Şifre Yanlış Bebeğim!")
            st.stop()
    st.success("Bulut Bağlantısı Aktif ✅")

# --- ANA EKRAN (KULLANICI) ---
if not admin_modu:
    st.title("🎨 Reçete Hesaplama")
    
    df_k = get_all_data("Kartelalar")
    df_r = get_all_data("Renkler")
    df_t = get_all_data("Türler")
    df_m = get_all_data("Miktarlar")

    if df_k.empty:
        st.info("Henüz veri eklenmemiş. Lütfen Admin panelinden veri girin.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            secilen_k = st.selectbox("1. KARTELA", ["Seçiniz..."] + df_k["ad"].unique().tolist())
        with c2:
            r_list = df_r[df_r["kartela_ad"] == secilen_k]["renk_ad"].unique().tolist() if secilen_k != "Seçiniz..." else []
            secilen_r = st.selectbox("2. RENK", ["Seçiniz..."] + r_list)
        with c3:
            # Tür aramayı daha güvenli yapıyoruz
            t_list = df_t[(df_t["kartela_ad"] == secilen_k) & (df_t["renk_ad"] == secilen_r)]["tur_ad"].unique().tolist() if secilen_r != "Seçiniz..." else []
            # Ekranda sadece türün ismini göster (Örn: Mat)
            t_display = [t.split('|')[-1].strip() if '|' in str(t) else t for t in t_list]
            secilen_t_dis = st.selectbox("3. TÜR", ["Seçiniz..."] + t_display)
        with c4:
            m_vals = df_m["kg_degeri"].sort_values().unique().tolist() if not df_m.empty else []
            secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + [f"{x} KG" for x in m_vals])

        if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
            if "Seçiniz" not in [secilen_k, secilen_r, secilen_t_dis, secilen_m]:
                h_kg = float(secilen_m.replace(" KG", ""))
                df_f = get_all_data("Formüller")
                
                # Formül sayfasındaki anahtar: "Kartela | Renk | Tür"
                full_t = f"{secilen_k} | {secilen_r} | {secilen_t_dis}"
                reçete = df_f[df_f["tur_ad"].str.strip() == full_t] if not df_f.empty else pd.DataFrame()
                
                if not reçete.empty:
                    st.success(f"### {full_t} - {secilen_m} İçin Reçete")
                    res = []
                    for _, row in reçete.iterrows():
                        g_aj = float(str(row["gramAJ"]).replace(",", "."))
                        b_mik = float(str(row["baz_miktar"]).replace(",", "."))
                        mikt = (g_aj / b_mik) * (h_kg * 1000)
                        res.append({"Bileşen Adı": row["bilesen"], "Miktar (Gram)": format_gram(mikt)})
                    st.table(pd.DataFrame(res))
                else:
                    st.error(f"'{full_t}' için formül bulunamadı. Lütfen Admin panelinden formül ekleyin.")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Bulut Fabrika Yönetimi")
    t1, t2, t3 = st.tabs(["📊 Temel Veriler", "🧪 Formül Girişi", "⚖️ Miktarlar"])

    with t1:
        st.subheader("Kartela, Renk ve Tür Ekleme")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            yeni_k = st.text_input("Yeni Kartela Adı")
            if st.button("Kartelayı Buluta Kaydet"):
                yeni_df = pd.DataFrame([{"ad": yeni_k}])
                conn.create(spreadsheet=url, worksheet="Kartelalar", data=yeni_df, extend=True)
                st.toast("Kartela Kaydedildi!")

        with col2:
            df_k = get_all_data("Kartelalar")
            k_sec = st.selectbox("Kartela Seç", df_k["ad"].unique().tolist() if not df_k.empty else [])
            yeni_r = st.text_input("Yeni Renk Adı")
            if st.button("Rengi Buluta Kaydet"):
                yeni_df = pd.DataFrame([{"kartela_ad": k_sec, "renk_ad": yeni_r}])
                conn.create(spreadsheet=url, worksheet="Renkler", data=yeni_df, extend=True)
                st.toast("Renk Kaydedildi!")

        with col3:
            df_r = get_all_data("Renkler")
            r_sec = st.selectbox("Renk Seç", df_r[df_r["kartela_ad"] == k_sec]["renk_ad"].tolist() if not df_r.empty else [])
            yeni_t = st.text_input("Yeni Tür (Örn: Mat, Parlak)")
            if st.button("Tür Kaydet"):
                yeni_df = pd.DataFrame([{"kartela_ad": k_sec, "renk_ad": r_sec, "tur_ad": yeni_t}])
                conn.create(spreadsheet=url, worksheet="Türler", data=yeni_df, extend=True)
                st.toast("Tür Kaydedildi!")

    with t2:
        st.subheader("🧪 Yeni Formül Girişi")
        with st.form("formül_formu"):
            f_k = st.selectbox("Kartela", df_k["ad"].unique().tolist() if not df_k.empty else [])
            f_r = st.selectbox("Renk", df_r[df_r["kartela_ad"] == f_k]["renk_ad"].tolist() if not df_r.empty else [])
            f_t = st.text_input("Tür (Seçtiğiniz Türün Aynısını Yazın)")
            
            st.divider()
            f_bilesen = st.text_input("Bileşen (Örn: baz, a1, sarı)")
            f_gram = st.number_input("Gramaj", step=0.01, format="%.2f")
            f_baz = st.number_input("Baz Miktar (KG)", value=1.0)
            
            if st.form_submit_button("Formül Satırını Kaydet"):
                full_name = f"{f_k} | {f_r} | {f_t}"
                yeni_f = pd.DataFrame([{"tur_ad": full_name, "bilesen": f_bilesen, "gramAJ": f_gram, "baz_miktar": f_baz}])
                conn.create(spreadsheet=url, worksheet="Formüller", data=yeni_f, extend=True)
                st.success(f"{full_name} için {f_bilesen} eklendi!")

    with t3:
        st.subheader("⚖️ Miktar Ayarları")
        yeni_m = st.number_input("Yeni KG Seçeneği Ekle", step=1)
        if st.button("Miktarı Kaydet"):
            yeni_df = pd.DataFrame([{"kg_degeri": yeni_m}])
            conn.create(spreadsheet=url, worksheet="Miktarlar", data=yeni_df, extend=True)
            st.toast("Miktar Eklendi!")
