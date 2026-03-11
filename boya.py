import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Boya Fabrikası Pro v26", layout="wide")

# --- BAĞLANTI AYARLARI ---
url = "https://docs.google.com/spreadsheets/d/1XhEwmzpS7-Y5ndJ_zG4ZHqHpYo7UIX6HpSGBIiowfZo/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# Sayı Formatlama
def format_gram(deger):
    yuvarlanmis = round(deger, 2)
    return f"{int(yuvarlanmis)}" if yuvarlanmis % 1 == 0 else f"{yuvarlanmis:,.2f}".replace(".00", "")

# Veri Çekme Fonksiyonu
def get_all_data(worksheet):
    try:
        df = conn.read(spreadsheet=url, worksheet=worksheet, ttl=0)
        return df.dropna(how="all").reset_index(drop=True)
    except:
        return pd.DataFrame()

# --- YAN PANEL ---
with st.sidebar:
    st.title("🛡️ Fabrika Yönetimi")
    admin_modu = st.checkbox("Admin Panelini Aç")
    if admin_modu:
        sifre = st.text_input("Şifre", type="password")
        if sifre != "1111":
            st.stop()
    st.success("Bulut Sistemi Hazır ✅")

# --- ANA EKRAN (KULLANICI) ---
if not admin_modu:
    st.title("🎨 Reçete Hesaplama")
    
    df_k = get_all_data("Kartelalar")
    df_r = get_all_data("Renkler")
    df_t = get_all_data("Türler")
    df_m = get_all_data("Miktarlar")

    if df_k.empty:
        st.info("Henüz veri bulunamadı. Lütfen Admin panelinden veri ekleyin.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            secilen_k = st.selectbox("1. KARTELA", ["Seçiniz..."] + df_k["ad"].unique().tolist())
        with c2:
            r_list = df_r[df_r["kartela_ad"] == secilen_k]["renk_ad"].unique().tolist() if secilen_k != "Seçiniz..." else []
            secilen_r = st.selectbox("2. RENK", ["Seçiniz..."] + r_list)
        with c3:
            t_list = df_t[(df_t["kartela_ad"] == secilen_k) & (df_t["renk_ad"] == secilen_r)]["tur_ad"].unique().tolist() if secilen_r != "Seçiniz..." else []
            secilen_t = st.selectbox("3. TÜR", ["Seçiniz..."] + t_list)
        with c4:
            m_vals = df_m["kg_degeri"].unique().tolist() if not df_m.empty else []
            secilen_m = st.selectbox("4. MİKTAR", ["Seçiniz..."] + [f"{x} KG" for x in m_vals])

        if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
            if "Seçiniz" not in [secilen_k, secilen_r, secilen_t, secilen_m]:
                h_kg = float(secilen_m.replace(" KG", ""))
                df_f = get_all_data("Formüller")
                full_key = f"{secilen_k} | {secilen_r} | {secilen_t}"
                reçete = df_f[df_f["tur_ad"].str.strip() == full_key] if not df_f.empty else pd.DataFrame()
                
                if not reçete.empty:
                    st.success(f"### {full_key} - {secilen_m} Reçetesi")
                    res = []
                    for _, row in reçete.iterrows():
                        g_aj = float(str(row["gramAJ"]).replace(",", "."))
                        b_mik = float(str(row["baz_miktar"]).replace(",", "."))
                        mikt = (g_aj / b_mik) * (h_kg * 1000)
                        res.append({"Bileşen": row["bilesen"], "Gram": format_gram(mikt)})
                    st.table(pd.DataFrame(res))
                else:
                    st.error("Formül bulunamadı!")

else:
    # --- ADMİN PANELİ ---
    st.title("🛠️ Veri Yönetim Merkezi")
    sekme1, sekme2 = st.tabs(["📁 Veri Ekle", "🧪 Formül Ekle"])

    with sekme1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Kartela Ekle")
            yeni_k = st.text_input("Kartela Adı")
            if st.button("Kartelayı Kaydet"):
                df = get_all_data("Kartelalar")
                df_yeni = pd.concat([df, pd.DataFrame([{"ad": yeni_k}])], ignore_index=True)
                conn.update(spreadsheet=url, worksheet="Kartelalar", data=df_yeni)
                st.toast("Kaydedildi!")

        with col2:
            st.subheader("Renk Ekle")
            df_k = get_all_data("Kartelalar")
            k_sec = st.selectbox("Kartela Seçin", df_k["ad"].unique().tolist() if not df_k.empty else [])
            yeni_r = st.text_input("Renk Adı")
            if st.button("Rengi Kaydet"):
                df = get_all_data("Renkler")
                df_yeni = pd.concat([df, pd.DataFrame([{"kartela_ad": k_sec, "renk_ad": yeni_r}])], ignore_index=True)
                conn.update(spreadsheet=url, worksheet="Renkler", data=df_yeni)
                st.toast("Kaydedildi!")

    with sekme2:
        st.subheader("Formül Girişi")
        f_k = st.selectbox("Kartela ", df_k["ad"].unique().tolist() if not df_k.empty else [])
        df_r = get_all_data("Renkler")
        f_r = st.selectbox("Renk ", df_r[df_r["kartela_ad"] == f_k]["renk_ad"].tolist() if not df_r.empty else [])
        f_t = st.text_input("Tür (Mat, İpek Mat vb.)")
        
        c_a, c_b, c_c = st.columns(3)
        with c_a: bils = st.text_input("Bileşen")
        with c_b: gra = st.number_input("Gramaj (1 KG için)", format="%.2f")
        with c_c: baz = st.number_input("Baz KG", value=1.0)

        if st.button("Formül Satırını Ekle"):
            full_t = f"{f_k} | {f_r} | {f_t}"
            df = get_all_data("Formüller")
            yeni_satir = pd.DataFrame([{"tur_ad": full_t, "bilesen": bils, "gramAJ": gra, "baz_miktar": baz}])
            df_yeni = pd.concat([df, yeni_satir], ignore_index=True)
            conn.update(spreadsheet=url, worksheet="Formüller", data=df_yeni)
            # Türler tablosuna da otomatik ekleyelim ki listede çıksın
            df_turler = get_all_data("Türler")
            if full_t not in df_turler["tur_ad"].tolist():
                tur_ekle = pd.DataFrame([{"kartela_ad": f_k, "renk_ad": f_r, "tur_ad": f_t}])
                conn.update(spreadsheet=url, worksheet="Türler", data=pd.concat([df_turler, tur_ekle]))
            st.success("Formül ve Tür kaydedildi!")
