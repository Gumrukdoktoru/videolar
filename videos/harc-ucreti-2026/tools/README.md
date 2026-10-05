# Ekran metni değiştirme + takipli kamera hattı

`assets/footage/ekran-kaydi-duzenlenmis.mp4` ve `assets/track.js` bu betiklerle üretildi
(Python 3, OpenCV, NumPy, SciPy). Kaynak: depo kökündeki
`WhatsApp Video 2026-10-05 at 14.08.41.mp4`, önce 30 fps sabit kare hızına çevrildi
(`ffmpeg -i <kaynak> -vf fps=30 -an -c:v ffv1 cfr30.mkv`).

Betiklerdeki mutlak çalışma klasörü yolları (scratchpad / `FONTDIR`) oturuma özeldir;
tekrar çalıştırmadan önce kendi klasörünüze göre düzenleyin.

| Adım | Betik | Ne yapar |
| --- | --- | --- |
| 1 | `fit_targets.py` + `textmodel.py` | Referans karelerde (form: kare 300, onay: kare 1500) eski metni Open Sans SemiBold/Bold ile piksel altı hassasiyette modeller → `targets.json` |
| 2 | `track.py` | Her kare için ekran içeriğinin SIFT + RANSAC homografisi (form ve onay ekranı ayrı) |
| 3 | `fixH.py` | Komşularından sapan homografileri enterpolasyonla onarır |
| 4 | `patch.py` + `run_patch.py` / `run_fix.py` | Her karede metin modelini yeniden oturtur (konum, ölçek, açı, hareket bulanıklığı), sadece değişen rakam hücrelerini yeni rakamla değiştirir, parmak gibi engelleri korur, codec dokusunu taklit eder |
| 5 | `build_footage.py` | Seslendirmeye göre yeniden zamanlama (kurgu listesi), alanları takip eden kamera zoom'u, intro/ipucu bulanıklığı, 1080x1920 çıktı ve vurgu kutuları için kare kare alan konumları (`assets/track.js`) |

Değişen metinler:

- Form: `03/11/2025` → `07/10/2026`, `2.500,00` → `3.275,00`
- Onay ekranı: `03.11.2025` → `07.10.2026`, Tutar ve Toplam Tutar `2.500,00 TL` → `3.275,00 TL`
