# app.py

import streamlit as st
import pandas as pd
import numpy as np
import base64
import plotly.express as px
import plotly.graph_objects as go # FITUR BARU: Import untuk Grafik Radar
from topsis import run_topsis

# --- Konfigurasi Halaman ---
st.set_page_config(page_title="Rekomendasi Smartphone", layout="wide")

# --- Fungsi Bantuan ---
def get_image_as_base64(path):
    """Membaca file gambar dan mengubahnya menjadi base64."""
    try:
        with open(path, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError:
        return None

# --- Judul Aplikasi ---
st.title('📱 Sistem Pendukung Keputusan Pemilihan Smartphone')
st.write("Temukan smartphone terbaik menggunakan Metode TOPSIS.")

# --- Sidebar ---
with st.sidebar:
    # --- Profil Toko ---
    img_base64 = get_image_as_base64('assets/phone_logo.jpg')
    if img_base64:
        st.markdown(
            f"""
            <div style="text-align:center; padding: 1rem 0;">
                <img src="data:image/png;base64,{img_base64}" 
                     style="width: 120px; border-radius: 15px; margin-bottom: 10px;" />
                <p style="font-size: 24px; font-weight: bold;">📱 Cihuy Store</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.header("Konfigurasi Kriteria")
    # --- Data Kriteria ---
    criteria_data = {
        'Harga (juta Rp)': {'weight': 5, 'type': 'cost'},
        'Skor Kamera (1-100)': {'weight': 4, 'type': 'benefit'},
        'Baterai (mAh)': {'weight': 4, 'type': 'benefit'},
        'Berat (gram)': {'weight': 3, 'type': 'cost'},
        'Skor Performa': {'weight': 5, 'type': 'benefit'}
    }
    
    weights = []
    criteria_names = list(criteria_data.keys())
    
    for name in criteria_names:
        weight = st.slider(
            f"Bobot untuk {name}", 1, 5, 
            criteria_data[name]['weight'],
            help=f"Tipe: **{criteria_data[name]['type']}**"
        )
        weights.append(weight)

# --- Memuat Data ---
@st.cache_data
def load_data():
    """Memuat dan mempersiapkan data smartphone."""
    try:
        df = pd.read_csv('data_smartphone.csv')
        # FITUR BARU: Menambahkan kolom gambar placeholder untuk setiap hp
        # Ini akan digunakan untuk menampilkan gambar di kartu hasil
        df['Image URL'] = df['Alternatif'].apply(
            lambda x: f"https://placehold.co/500x500/EAEAEA/000000?text={x.replace(' ', '+')}&font=roboto"
        )
        return df
    except FileNotFoundError:
        return None

df_original = load_data()

if df_original is None:
    st.error("File 'data_smartphone.csv' tidak ditemukan. Pastikan file ada di folder yang sama.")
    st.stop()

# --- FITUR BARU: Filter Data ---
st.header("Filter Harga Smarthpone")
max_price = int(df_original['Harga (juta Rp)'].max())
min_price = int(df_original['Harga (juta Rp)'].min())

price_range = st.slider(
    "Filter berdasarkan rentang harga (juta Rp):",
    min_value=min_price,
    max_value=max_price,
    value=(min_price, max_price)
)

# Terapkan filter ke dataframe
df_filtered = df_original[
    (df_original['Harga (juta Rp)'] >= price_range[0]) &
    (df_original['Harga (juta Rp)'] <= price_range[1])
]

st.write(f"Menampilkan **{len(df_filtered)}** dari **{len(df_original)}** alternatif smartphone.")
st.dataframe(df_filtered.drop(columns=['Image URL']), use_container_width=True)


# --- Proses Perhitungan ---
st.header("Rekomendasi Smartphone")
if st.button('🚀 Hitung Rekomendasi Sekarang!', type="primary"):
    if df_filtered.empty:
        st.warning("Tidak ada data untuk dihitung. Sesuaikan filter Anda.")
    else:
        # Ekstrak data untuk perhitungan
        alternatives = df_filtered['Alternatif'].values
        image_urls = df_filtered['Image URL'].values
        decision_matrix = df_filtered[criteria_names].values
        criteria_types = [info['type'] for info in criteria_data.values()]

        with st.spinner('Sedang melakukan perhitungan TOPSIS...'):
            scores, normalized_matrix, weighted_matrix = run_topsis(decision_matrix, weights, criteria_types)
            
            df_result = pd.DataFrame({
                'Alternatif': alternatives,
                'Skor TOPSIS': scores,
                'Image URL': image_urls
            })
            df_result['Peringkat'] = df_result['Skor TOPSIS'].rank(ascending=False, method='min').astype(int)
            df_result = df_result.sort_values(by='Skor TOPSIS', ascending=False).reset_index(drop=True)

        st.success('✅ Perhitungan TOPSIS Selesai!')
        
        # --- MENAMPILKAN HASIL ---
        st.header('🏆 Hasil Peringkat Smartphone')
        
        # --- KARTU DETAIL UNTUK PERINGKAT TERATAS (SUDAH DIPERBAIKI) ---
        st.subheader("Peringkat Teratas")
        top_alternatives = df_result.head(3)
        cols = st.columns(3)
        
        # Pemetaan untuk medali dan gambar lokal
        medal_map = {
            1: {"emoji": "🥇", "image": "assets/phone1.jpg"},
            2: {"emoji": "🥈", "image": "assets/phone2.jpg"},
            3: {"emoji": "🥉", "image": "assets/phone3.jpg"}
        }
        
        for i, row in top_alternatives.iterrows():
            rank = i + 1
            with cols[i]:
                medal_info = medal_map.get(rank)
                st.markdown(f"<h3 style='text-align: center;'>{medal_info['emoji']} Peringkat {rank}</h3>", unsafe_allow_html=True)
                
                # Menggunakan gambar lokal sesuai peringkat
                try:
                    st.image(medal_info['image'], caption=row['Alternatif'])
                except FileNotFoundError:
                    st.error(f"Gambar {medal_info['image']} tidak ditemukan.")

                st.metric(label="Skor Preferensi", value=f"{row['Skor TOPSIS']:.4f}")
                
                with st.expander("Lihat Detail Spesifikasi"):
                    specs = df_original[df_original['Alternatif'] == row['Alternatif']].iloc[0]
                    st.write(f"**Harga**: Rp {specs['Harga (juta Rp)']} Juta")
                    st.write(f"**Kamera**: {specs['Skor Kamera (1-100)']}/100")
                    st.write(f"**Baterai**: {specs['Baterai (mAh)']} mAh")
                    st.write(f"**Berat**: {specs['Berat (gram)']} gram")
                    st.write(f"**Performa**: {specs['Skor Performa']}")

        st.divider()

        # --- Layout Baru untuk Visualisasi dan Tabel ---
        res_col1, res_col2 = st.columns([0.6, 0.4]) # Bagan lebih besar
        
        with res_col1:
            # --- Visualisasi Hasil dengan Bagan Batang ---
            st.subheader("Visualisasi Peringkat")
            top_10_df = df_result.head(10).sort_values(by='Skor TOPSIS', ascending=True)
            fig_bar = px.bar(
                top_10_df, x='Skor TOPSIS', y='Alternatif', orientation='h',
                title='Top 10 Smartphone Berdasarkan Skor', text='Skor TOPSIS'
            )
            fig_bar.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        with res_col2:
            # --- FITUR BARU: Grafik Radar ---
            st.subheader("Analisis Profil Juara")
            
            # Ambil data untuk smartphone peringkat 1
            top_phone_data = df_filtered[df_filtered['Alternatif'] == df_result.iloc[0]['Alternatif']].iloc[0]
            
            # Normalisasi nilai untuk grafik radar agar skalanya sama (0-1)
            # Ambil nilai min dan max dari keseluruhan data, bukan yg terfilter saja
            min_vals = df_original[criteria_names].min()
            max_vals = df_original[criteria_names].max()
            
            radar_values = []
            for i, name in enumerate(criteria_names):
                val = top_phone_data[name]
                if criteria_data[name]['type'] == 'cost':
                    # Untuk 'cost', nilai rendah lebih baik. Jadi kita balik skalanya.
                    normalized_val = 1 - ((val - min_vals[i]) / (max_vals[i] - min_vals[i]))
                else: # benefit
                    normalized_val = (val - min_vals[i]) / (max_vals[i] - min_vals[i])
                radar_values.append(normalized_val)
                
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=radar_values,
                theta=criteria_names,
                fill='toself',
                name=df_result.iloc[0]['Alternatif']
            ))
            fig_radar.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
                title=f"Profil Keunggulan: {df_result.iloc[0]['Alternatif']}",
                showlegend=False
            )
            st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        
        # --- Tabel Hasil Lengkap dan Detail Perhitungan ---
        st.subheader("Tabel Peringkat Lengkap")
        st.dataframe(df_result.drop(columns=['Image URL']), use_container_width=True)
        
        with st.expander("Lihat Detail Langkah Perhitungan Matematis"):
            st.subheader("Matriks Ternormalisasi")
            st.dataframe(pd.DataFrame(normalized_matrix, columns=criteria_names, index=alternatives))
            
            st.subheader("Matriks Ternormalisasi Terbobot")
            st.dataframe(pd.DataFrame(weighted_matrix, columns=criteria_names, index=alternatives))
