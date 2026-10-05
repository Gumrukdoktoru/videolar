---
workflow: general-video
flow: automation
storyboard: no
message: "Sınav harç ücreti 3.275 TL — Hacettepe'ye havale ile adım adım nasıl yatırılır"
destination: instagram-reels
aspect: 1080x1920
language: tr
audience: Gümrük Müşavirliği / Gümrük Müşavir Yardımcılığı sınavına girecek adaylar
length: 73.5s
angle: tutorial
---

## Intent

14.08 tarihli ekran kaydı videosunun (banka uygulamasında Hacettepe Üniversitesi Döner
Sermaye İşletmesi'ne havale) güncellenmiş hali. Kullanıcının isteği: "konuşmasını yeni bir
konuşma ile değiştirmek istiyorum. elevenlabs 4'te Cemi kullanmak istiyorum ... tarih
kısmına 07.10.2026 yazalım ve ücret kısmına 3275 TL yazalım ... en önemlisi motion
effectlerde eklemeni istiyorum".

## Assets

- assets/audio/seslendirme-cem-v4.mp3 — yeni seslendirme (ElevenLabs eleven_v4, ses: Cem
  `D1xRw7f8ZHedI7xJgfvz`, 4 varyasyondan take 1, 72.2 sn). Videonun ana zaman çizgisi.
- assets/footage/ekran-kaydi-duzenlenmis.mp4 — orijinal 14.08 videosu; ekrandaki tarih
  (03/11/2025 → 07/10/2026, 03.11.2025 → 07.10.2026) ve tutar (2.500,00 → 3.275,00;
  Tutar + Toplam Tutar) kare kare takip edilerek değiştirildi, seslendirmeye göre yeniden
  zamanlandı. Orijinal ses kullanılmıyor.
- assets/track.json — her çıktı karesi için form/onay ekranı alanlarının konumları
  (vurgu kutuları alanları takip eder).

## Customizations

- Motion efektleri: alanlara kamera zoom'u, takip eden vurgu kutuları, değer kartları
  (07.10.2026, 3.275,00 TL sayaçlı), GM/GMY açıklama kartı, DEVAM/ONAYLA dokunma efekti,
  açılış başlığı, ipuçları kartları, kapanış.

## Notes

- Sınav tarihi seslendirmede belirtilmedi (2026 tarihi kullanıcıdan teyit edilmedi).
- IBAN numarası grafiklerde yeniden yazılmadı; seslendirme kılavuzdaki IBAN'ı işaret ediyor.
- TC ve isim ekranda örnek değer (11111111111 CAN YILMAZ).
