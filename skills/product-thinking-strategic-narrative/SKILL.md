---
name: product-thinking-strategic-narrative
description: Evaluasi ide produk, sederhanakan user journey dan UX, serta susun narasi pitch berbasis kebutuhan pengguna dengan JTBD, desirability-viability-feasibility, dan SCQA.
---

# Product Thinking, UX Clarity, & Strategic Narrative Architect

## Sasaran

Uji apakah solusi menjawab masalah pengguna, dapat dieksekusi, dan memiliki jalan menuju keberlanjutan. Ubah analisis tersebut menjadi pengalaman serta cerita yang mudah dipahami pengguna biasa, juri, dan pengambil keputusan.

## 1. Product thinking dan kelayakan

### Desirability

- Mulai dari user friction atau unmet need yang memiliki dasar, bukan dari teknologi yang ingin dipamerkan.
- Tuliskan JTBD: **“Ketika [situasi], pengguna ingin [kebutuhan], sehingga mereka bisa [tujuan].”**
- Bedakan pengguna, pemilik proses, pembeli, dan stakeholder jika mereka berbeda orang. Jelaskan pekerjaan serta hambatan masing-masing tanpa mencampur kebutuhan mereka.
- Tandai mana kebutuhan hasil observasi, mana hipotesis, dan apa yang perlu divalidasi.

### Viability

- Jelaskan siapa yang memperoleh nilai dan siapa yang membayar. Pertimbangkan B2B, B2C, atau B2B2C; model pendapatan dapat berupa langganan/SaaS, komisi, freemium, atau model lain yang sesuai.
- Untuk alat internal, jelaskan pemilik anggaran dan nilai operasionalnya. Jangan memaksakan model komersial atau menyatakan prototipe sudah menjadi SaaS.
- Tentukan North Star Metric beserta definisi operasionalnya: apa yang dihitung, satuan, cakupan, serta cara pengukuran. Tandai sebagai usulan bila belum diukur.
- Jangan mengarang harga, CAC, LTV, pendapatan, atau bukti permintaan pasar.

### Feasibility

Kelompokkan cakupan produk menjadi:

| Prioritas | Kriteria |
| --- | --- |
| Must-Have | Pekerjaan inti pengguna dapat selesai; menjadi batas MVP |
| Should-Have | Diferensiasi atau peningkatan penting setelah alur inti terbukti |
| Could-Have | Pengembangan masa depan atau scaling yang belum dibutuhkan untuk membuktikan nilai inti |

Pisahkan prioritas dari status implementasi: tersedia, sebagian tersedia, atau rencana. Nyatakan dependensi dan keterbatasan yang memengaruhi kelayakan.

## 2. UX clarity dan pengurangan kompleksitas

- **The 3-Step Rule:** jelaskan journey dalam tiga sampai empat langkah utama. Gabungkan sublangkah menjadi fase yang masuk akal tanpa menyembunyikan persetujuan analis, validasi, atau kebutuhan bukti.
- **Cognitive load:** jelaskan input → hasil → tindakan pengguna. Untuk AI agentic, LLM pipeline, dan otomasi kompleks, gunakan analogi konkret bila membantu; jangan membiarkan analogi mengaburkan mekanisme atau batas AI.
- **Output dan value:** tonjolkan apa yang dapat dilakukan pengguna setelah menerima hasil. Detail teknis dimasukkan ketika diperlukan untuk menjelaskan inovasi, feasibility, batasan, atau pertanyaan juri.
- **Friction audit:** cari titik pengguna bingung, ragu, menunggu, atau berhenti. Contoh: istilah form ambigu, registrasi berlebih, keluaran AI lambat, error tanpa pemulihan, dan hasil tanpa sumber.
- Untuk setiap friction penting, pasangkan mitigasi konkret. Bedakan mitigasi yang sudah berjalan dari usulan; masukkan yang relevan ke deck tanpa menambah slide fitur yang tidak diperlukan.

Format audit yang disarankan:

| Langkah pengguna | Friction dan dasar observasi/hipotesis | Dampak terhadap pekerjaan | Mitigasi | Status dan cara validasi |
| --- | --- | --- | --- | --- |

## 3. Strategic narrative dengan SCQA

- **Situation:** bangun konteks yang dapat diverifikasi. Gunakan data makro atau tren industri jika tersedia dan relevan; konteks operasional yang teramati juga sah. Jangan mengarang statistik untuk membuka cerita.
- **Complication:** tunjukkan pemicu atau hambatan yang membuat pekerjaan pengguna sulit dan apa akibatnya.
- **Question:** rumuskan pertanyaan keputusan yang langsung muncul dari komplikasi.
- **Answer:** posisikan inovasi sebagai jawaban logis dengan mekanisme, bukti, dan batas yang jelas. Klaim “satu-satunya” atau “superior” memerlukan pembandingan yang mendukungnya.
- **Emotional resonance:** gunakan satu persona dan adegan konkret untuk membumikan masalah, lalu hubungkan dengan bukti agregat. Persona, kutipan ilustratif, dan skenario fiktif harus diberi label; jangan disajikan sebagai wawancara nyata.
- Pertahankan kesinambungan tokoh: pekerjaan awal → hambatan → penggunaan produk → hasil yang dapat ditunjukkan → keputusan yang tetap dipegang manusia.

## 4. Alur kerja dan keluaran

1. Pahami masalah dan bukti yang tersedia; tulis JTBD serta pihak yang terlibat.
2. Uji desirability, viability, dan feasibility. Catat celah bukti tanpa mengubah hipotesis menjadi fakta.
3. Tetapkan MVP, North Star Metric usulan/terukur, serta journey tiga sampai empat fase.
4. Audit friction pada journey dan tentukan mitigasi yang relevan.
5. Susun SCQA dan cerita persona yang menghubungkan masalah, mekanisme solusi, bukti, serta langkah validasi berikutnya.

Sesuaikan panjang output dengan permintaan. Untuk evaluasi produk, berikan keputusan dan alasannya, JTBD, penilaian kelayakan, cakupan MVP, journey, friction utama, dan validasi berikutnya. Jangan memaksakan semua bagian pada revisi kecil.

Untuk deck, gabungkan dengan `../business-innovation-case/SKILL.md`: gunakan action title dan format storyboard dari skill tersebut; gunakan skill ini untuk memeriksa kebutuhan pengguna serta kesinambungan cerita. Ikuti panduan visual dan kompetisi yang dirujuk `AGENTS.md`.

## Batas bukti untuk omniKPI

- Gunakan kode dan fixture terkini sebagai dasar fitur dan data demo. Pisahkan AI dari otomasi deterministik.
- Jangan mengklaim dampak waktu kerja, akurasi, atau hasil industri jika belum diukur. Rancang cara validasinya sebagai langkah berikutnya.
- Perbandingan sebelum/sesudah dapat memakai langkah kerja atau artefak yang benar-benar dapat dihitung; jangan mengubahnya menjadi persentase efisiensi waktu tanpa pengukuran.
- Persona Rani dan contoh lain tetap diberi label ilustratif jika bukan pengguna yang diwawancarai. Data sintetis dan asumsi harus tetap terlihat sebagai data sintetis dan asumsi.
