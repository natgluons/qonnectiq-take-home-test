# Qonnectiq - AI Engineer Task / Take Home Test

## 1. Cara Kerja Sistem

- **Document Parsing**: PDF laporan dan DOCX glosarium dibaca dan diubah menjadi structured data JSON.
- **Information Retrieval**: Pertanyaan pengguna dicocokkan dengan informasi yang paling relevan menggunakan kombinasi pencarian berbasis keywords, konteks, dan metadata.
- **AI Answer Generation**: Informasi yang ditemukan digunakan sebagai dasar jawaban. Pertanyaan dengan jawaban numerik tertentu dapat dijawab langsung dari data untuk mengurangi risiko kesalahan AI.
- **Source Attribution**: Jawaban disertai referensi dokumen dan halaman yang digunakan.
- **Out-of-Scope Handling**: Pertanyaan yang tidak didukung dokumen ditolak secara konsisten.
- MVP-nya mendukung penambahan PDF baru juga dengan format serupa.

## 2. Stacks & Tools

| Stacks / Library | Functions |
| --- | --- |
| FastAPI | Backend dan REST API |
| HTML + JavaScript | Vanilla, simple interface only |
| PyMuPDF | Text extraction |
| python-docx | Extract glossary DOCX |
| JSON | Store data hasil parsing |
| BM25 | Rank informasi berdasarkan relevansi |
| OpenAI GPT-4o-mini | Model default untuk jawaban retrieval |
| OpenAI text-embedding-3-small | Semantic search tambahan (explorative) |
| OpenAI Python SDK | Integrasi model |
| Pydantic | Validasi input API melalui FastAPI |
| Uvicorn | Run server aplikasi |
| python-dotenv | Configuration dan API key |
| Pytest + HTTPX | Automatic testing |

Pendekatan retrieval menggabungkan structured field matching, BM25, bilingual keyword matching, serta filtering berdasarkan tanggal dan nomor laporan. Semantic reranking menggunakan embeddings juga disediakan sebagai opsi. Saya memutuskan untuk tidak digunakan framework AI tambahan seperti LangChain maupun vector database karena ukuran dataset masih kecil. Tujuannya menjaga sistem tetap ringan, sederhana, dan mudah dievaluasi.

## 4. Hasil Testing & Performance

Dataset pengujian terdiri atas 3 laporan PDF dan 1 dokumen glosarium, menghasilkan 330 record pencarian serta 196 entri istilah.

| Metrik | Hasil |
| --- | --- |
| Dokumen berhasil diproses | 4/4 (100%) |
| Top-1 Retrieval Accuracy | 9/9 (100%) |
| Recall@3 | 9/9 (100%) |
| Penolakan pertanyaan di luar konteks | 3/3 (100%) |
| Automated Tests | 17/17 berhasil |
| Waktu parsing 4 dokumen | ±0,28 detik |
| Median waktu retrieval | 3,72 ms |
| P95 waktu retrieval | 4,38 ms |

Pengujian menggunakan dataset sample dan pertanyaan berlabel yang terbatas. Waktu retrieval diukur secara lokal, belum mencakup waktu respons OpenAI atau komunikasi jaringan. (Hasil ini belum merepresentasikan akurasi pada data baru.)

### Contoh Hasil

- **Pertanyaan:** Dimana letak lokasi sumur?
  - **Jawaban:** Malaysia
- **Pertanyaan:** Berapa Total NPT sumur?
  - **Jawaban:** 1.5 hr
- **Pertanyaan:** Wireline run apa yang direncanakan?
  - **Jawaban:** WL Run #1: PEX-QAIT dan WL Run #2: MDT (QS-Saturn)

Ketiga jawaban tersebut berhasil diperoleh langsung dari dokumen yang relevan tanpa memerlukan generasi jawaban oleh LLM.

## 5. Insight dan Evaluasi

### Temuan utama

- **Structured retrieval efektif untuk data teknis.** Nilai seperti kedalaman, lokasi, biaya, dan durasi dapat diambil langsung sehingga tidak perlu bergantung sepenuhnya pada interpretasi LLM.
- **Metadata meningkatkan ketepatan konteks.** Informasi tanggal dan nomor laporan membantu membedakan data dari beberapa laporan sumur yang sama.
- **Pendekatan hybrid memberikan fleksibilitas.** BM25 digunakan sebagai metode utama yang ringan dan tidak membutuhkan API, sementara embeddings tersedia untuk pencarian berdasarkan kemiripan makna.
- **Arsitektur minimal sudah mencukupi kebutuhan awal.** Sistem tidak memerlukan database khusus atau infrastruktur kompleks untuk dataset berukuran kecil.

### Keterbatasan saat ini

- Parser dioptimalkan untuk format DGOS dan DDR yang diberikan.
- PDF berbasis gambar atau hasil scan belum didukung.
- Semantic reranking dan kualitas jawaban LLM belum dievaluasi secara langsung dengan API.
- Kecepatan respons chat end-to-end terhadap batas tiga menit belum diverifikasi.
- Evaluasi lanjutan menggunakan pertanyaan dan dokumen baru diperlukan untuk mengukur kemampuan generalisasi.

## 6. Kesimpulan

- MVP berhasil mengimplementasikan alur pemrosesan dokumen, pencarian informasi, dan penyediaan jawaban berbasis sumber.
- Seluruh 9 pertanyaan evaluasi retrieval berhasil menemukan sumber yang tepat pada peringkat pertama, dengan waktu pencarian median sekitar 3,72 milidetik pada pengujian lokal.
- Hasil ini menunjukkan bahwa pendekatan retrieval yang sederhana tetapi terstruktur dapat bekerja dengan baik pada dataset awal, tanpa memerlukan fine-tuning, vector database, atau arsitektur AI yang kompleks.

### Catatan Pilihan Penyimpanan

JSON tetap menjadi pilihan default karena paling sederhana, mudah diperiksa, dan sudah cukup untuk ukuran dataset MVP. SQLite juga disediakan sebagai pilihan opsional apabila hasil parsing ingin disimpan dalam database tanpa menambah layanan atau proses setup lain. Pada satu proses ingestion, pengguna dapat memilih output JSON atau SQLite sesuai kebutuhan.
