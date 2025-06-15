# topsis.py

import numpy as np

def normalize(decision_matrix):
    """
    Normalisasi matriks keputusan menggunakan rumus dari Persamaan (1) di PDF.
    rij = xij / sqrt(sum(xij^2 for i=1 to m))
    """
    # np.linalg.norm(matrix, axis=0) adalah cara cepat untuk menghitung
    # akar dari jumlah kuadrat untuk setiap kolom (kriteria).
    norm = np.linalg.norm(decision_matrix, axis=0)
    # Menghindari pembagian dengan nol jika ada kolom yang semua nilainya nol
    norm[norm == 0] = 1
    return decision_matrix / norm

def apply_weights(normalized_matrix, weights):
    """
    Mengalikan matriks ternormalisasi dengan bobot preferensi (Persamaan 2).
    yij = wi * rij
    """
    return normalized_matrix * weights

def find_ideal_solutions(weighted_matrix, criteria_types):
    """
    Menentukan solusi ideal positif (A+) dan negatif (A-) (Persamaan 3 & 4).
    Tipe kriteria: 'benefit' (maksimalkan) atau 'cost' (minimalkan).
    """
    ideal_positive = np.zeros(weighted_matrix.shape[1])
    ideal_negative = np.zeros(weighted_matrix.shape[1])
    
    for j in range(weighted_matrix.shape[1]):
        column = weighted_matrix[:, j]
        if criteria_types[j] == 'benefit':
            ideal_positive[j] = np.max(column)
            ideal_negative[j] = np.min(column)
        elif criteria_types[j] == 'cost':
            ideal_positive[j] = np.min(column)
            ideal_negative[j] = np.max(column)
            
    return ideal_positive, ideal_negative

def calculate_distances(weighted_matrix, ideal_positive, ideal_negative):
    """
    Menghitung jarak Euclidean setiap alternatif ke solusi ideal.
    - Jarak ke solusi ideal positif (D+) - Persamaan (5)
    - Jarak ke solusi ideal negatif (D-) - Persamaan (6)
    """
    # axis=1 berarti kita menjumlahkan secara horizontal (per baris/alternatif)
    dist_positive = np.linalg.norm(weighted_matrix - ideal_positive, axis=1)
    dist_negative = np.linalg.norm(weighted_matrix - ideal_negative, axis=1)
    
    return dist_positive, dist_negative

def calculate_preference_score(dist_positive, dist_negative):
    """
    Menghitung nilai preferensi (V) untuk setiap alternatif (Persamaan 7).
    V = D- / (D- + D+)
    """
    # Menghindari pembagian dengan nol jika D- + D+ = 0
    denominator = dist_positive + dist_negative
    denominator[denominator == 0] = 1e-6 # nilai kecil untuk menghindari error
    
    return dist_negative / denominator

def run_topsis(decision_matrix, weights, criteria_types):
    """
    Fungsi utama untuk menjalankan seluruh alur TOPSIS dari awal hingga akhir.
    Mengembalikan skor preferensi untuk setiap alternatif.
    """
    # Langkah 1: Normalisasi Matriks Keputusan
    normalized_matrix = normalize(decision_matrix)
    
    # Langkah 2: Membuat Matriks Keputusan Ternormalisasi Terbobot
    weighted_matrix = apply_weights(normalized_matrix, weights)
    
    # Langkah 3: Menentukan Solusi Ideal Positif dan Negatif
    ideal_positive, ideal_negative = find_ideal_solutions(weighted_matrix, criteria_types)
    
    # Langkah 4: Menghitung Jarak ke Solusi Ideal
    dist_positive, dist_negative = calculate_distances(weighted_matrix, ideal_positive, ideal_negative)
    
    # Langkah 5: Menghitung Nilai Preferensi
    scores = calculate_preference_score(dist_positive, dist_negative)
    
    return scores, normalized_matrix, weighted_matrix