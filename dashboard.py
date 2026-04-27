# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta

# 1. Sayfa Ayarları
st.set_page_config(page_title="Stratejik KDS v3 | Tam Fonksiyonel", layout="wide")

# --- 2. VERİ VE MODEL (İptal Verileri Dahil) ---
@st.cache_data
def randevu_taleplerini_olustur():
    data = []
    hizmet_gruplari = {
        'Hizmet-A': {'kar': 250, 'sure': 30}, 'Hizmet-B': {'kar': 550, 'sure': 60},
        'Hizmet-C': {'kar': 1200, 'sure': 120}, 'Hizmet-D': {'kar': 2500, 'sure': 180}
    }
    baslangic_saati = datetime.strptime("09:00", "%H:%M")
    for i in range(1, 51):
        h_grubu = np.random.choice(list(hizmet_gruplari.keys()))
        talep_saati = (baslangic_saati + timedelta(minutes=int(np.random.randint(0, 480)))).strftime("%H:%M")
        
        # Geçmiş ve anlık risk verileri [cite: 11, 57]
        gecmis_iptal_orani = round(np.random.uniform(0, 0.4), 2) 
        anlik_no_show = round(np.random.uniform(0.05, 0.65), 2)
        
        data.append({
            'Talep_ID': f"REQ-{i:03d}",
            'Hizmet_Tipi': h_grubu,
            'Talep_Saati': talep_saati,
            'Birim_Kar': hizmet_gruplari[h_grubu]['kar'],
            'Sure_Dk': hizmet_gruplari[h_grubu]['sure'],
            'Sadakat_Puani': np.random.randint(1, 11),
            'Gecmis_Iptal_Orani': gecmis_iptal_orani,
            'No_Show_Riski': anlik_no_show,
            'Toplam_Risk': round((gecmis_iptal_orani + anlik_no_show) / 2, 2) # Hibrit risk tahmini [cite: 18]
        })
    return pd.DataFrame(data)

df = randevu_taleplerini_olustur()

# --- 3. SIDEBAR: YÖNETİM PANELİ ---
st.sidebar.header("🕹️ Yönetim Paneli")
piyasa_modu = st.sidebar.selectbox("Piyasa Durumu", ["Normal", "Bayram ⭐", "Durgunluk 🛡️", "Rakip Atağı ⚔️"])
personel_sayisi = st.sidebar.number_input("Personel Sayısı", 1, 50, 10)
mola_suresi = st.sidebar.slider("Mola Süresi (dk)", 15, 120, 30)

st.sidebar.subheader("📈 Kapasite Esnekliği")
overbooking_orani = st.sidebar.slider("Overbooking (Yedek Randevu) %", 0, 50, 10) / 100

st.sidebar.subheader("💰 Finansal Parametreler")
zam_orani = st.sidebar.slider("Zam (%)", 0, 100, 0) / 100
indirim_orani = st.sidebar.slider("İndirim (%)", 0, 100, 0) / 100
maliyet_artisi = st.sidebar.slider("Maliyet Artışı (%)", 0, 100, 20) / 100

# --- 4. HESAPLAMALAR ---
# Net Kar ve MCDM Kabul Skoru [cite: 8, 17, 55]
df['Net_Kar'] = df['Birim_Kar'] * (1 + zam_orani - indirim_orani - maliyet_artisi)
df['Kabul_Skoru'] = (df['Net_Kar']*0.4) + (df['Sadakat_Puani']*4) + ((1-df['Toplam_Risk'])*20)

# Kapasite Hesapları [cite: 26, 39]
toplam_is = df['Sure_Dk'].sum()
gercek_kapasite = personel_sayisi * 8 * 60
esnek_kapasite_sayisi = int(personel_sayisi * (1 + overbooking_orani))
doluluk = ((toplam_is + (personel_sayisi * mola_suresi)) / gercek_kapasite) * 100

# --- 5. ÇOKLU UYARI VE DENETLEME MOTORU ---
st.title("🚀 Gelişmiş Karar Destek Sistemi")
hatalar = []
oneriler = []

# A. Bayram Senaryosu
if piyasa_modu == "Bayram ⭐":
    if zam_orani < 0.30: hatalar.append("❌ **BAYRAM KRİZİ:** Fiyatları en az %30 artırmalısın!")
    if personel_sayisi < 15: hatalar.append("❌ **PERSONEL YETERSİZ:** Bayramda personel sayısını artır (Önerilen: 15+).")
    if indirim_orani > 0.10: hatalar.append("❌ **GEREKSİZ İNDİRİM:** Bayramda %10'dan fazla indirim yapma!")

# B. Durgunluk Senaryosu
elif piyasa_modu == "Durgunluk 🛡️":
    if indirim_orani < 0.15: oneriler.append("💡 **TEŞVİK GEREKLİ:** Durgunlukta %15-20 indirim yapmalısın.")
    if indirim_orani > 0.40: hatalar.append("⚠️ **ZARARINA SATIŞ:** %40 indirim maliyeti kurtarmaz!")
    if personel_sayisi > 8: oneriler.append("💡 **TASARRUF:** Personel sayısını 6-8 arasına çek.")

# C. Rakip Atağı
elif piyasa_modu == "Rakip Atağı ⚔️":
    if zam_orani > 0: hatalar.append("❌ **STRATEJİK HATA:** Rakip saldırırken zam yapma!")
    if indirim_orani < 0.20: oneriler.append("⚔️ **SAVUNMA HATTI:** En az %20 indirimle kaleyi koru.")

# D. Personel, Mola & Overbooking Dengesi
if personel_sayisi < 5 and mola_suresi > 60:
    hatalar.append("⚠️ **OPERASYONEL RİSK:** Az personelle uzun mola işleri aksatır!")
if doluluk > 95 and mola_suresi < 20:
    hatalar.append("😫 **PERSONEL İSYANI:** Molayı bu kadar kısmak personeli kaçırır!")

ortalama_risk = df['Toplam_Risk'].mean()
if ortalama_risk > 0.25 and overbooking_orani < 0.15:
    oneriler.append(f"💡 **OVERBOOKING FIRSATI:** İptal riski yüksek (%{ortalama_risk*100:.0f}). Overbooking'i artır.")

# E. Finansal Kontroller (Hiç yazmama veya aşırı indirim)
if zam_orani == 0 and indirim_orani == 0:
    oneriler.append("📝 **PASİF YÖNETİM:** Piyasa şartlarına göre bir aksiyon al.")
if indirim_orani > 0.50:
    hatalar.append("🛑 **İNDİRİMİN UCUNU KAÇIRDIN:** %50 indirim kârı yok eder!")

# --- 6. DİNAMİK KABUL MEKANİZMASI ---
st.subheader("🤖 AI Denetleme Raporu")
if hatalar:
    for h in hatalar: st.error(h)
if oneriler:
    for o in oneriler: st.info(o)

st.divider()
st.subheader("📋 Akıllı Randevu Çizelgesi")

# Yüksek Maliyet Filtresi [cite: 38, 42]
kriter_metni = "Normal Prosedür"
if maliyet_artisi > 0.60:
    kriter_metni = "⚠️ YÜKSEK MALİYET FİLTRESİ (Skor > 45)"
    st.warning(kriter_metni)

def karar_ver(row):
    if row['Net_Kar'] <= 0: return "❌ RED: Zarar"
    if maliyet_artisi > 0.60 and row['Kabul_Skoru'] < 45: return "🛑 RED: Düşük Verim"
    
    saat_grubu = df[df['Talep_Saati'] == row['Talep_Saati']].sort_values(by='Kabul_Skoru', ascending=False)
    sira = list(saat_grubu['Talep_ID']).index(row['Talep_ID']) + 1
    
    if sira <= personel_sayisi: return "✅ KABUL"
    elif sira <= esnek_kapasite_sayisi: return "⚠️ YEDEK (Overbook)"
    return "🔄 ERTELE"

df['Sistem_Karari'] = df.apply(karar_ver, axis=1)

st.dataframe(df[['Talep_Saati', 'Hizmet_Tipi', 'Toplam_Risk', 'Kabul_Skoru', 'Net_Kar', 'Sistem_Karari']].sort_values('Talep_Saati'), use_container_width=True)

# --- 7. ÖZET METRİKLER ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Kapasite Doluluk", f"%{doluluk:.1f}")
c2.metric("Beklenen Net Kâr", f"{df[df['Sistem_Karari'].str.contains('✅|⚠️')]['Net_Kar'].sum():,.0f} TL")
c3.metric("Yedek Kapasite", f"+{esnek_kapasite_sayisi - personel_sayisi}")
c4.metric("Ort. İptal Riski", f"%{ortalama_risk*100:.1f}")