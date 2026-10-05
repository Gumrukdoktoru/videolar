---
message: "Sınav harç ücreti 3.275 TL — Hacettepe'ye havale ile adım adım nasıl yatırılır"
audience: GM / GMY sınav adayları
mode: autonomous
canvas: 1080x1920
fps: 30
duration: 73.5
---

Zaman çizgisini seslendirme (`assets/audio/seslendirme-cem-v4.mp3`) belirler; aşağıdaki
saniyeler kelime zaman damgalarından alındı. Temel görüntü tek bir video
(`assets/footage/ekran-kaydi-duzenlenmis.mp4`): metni değiştirilmiş, yeniden zamanlanmış,
alanlara takipli kamera ile yakınlaşan çekim. Vurgu kutularının konumları kare kare
`assets/track.js` dosyasından okunur (rules: `ai-tracking-box`, `multi-phase-camera`).

## Frame 1 — Açılış (0.0–4.5)
status: built · src: index.html#intro
rules: waterfall-entry, spring-pop-entrance, ambient-glow-bloom
Bulanık telefon üstünde "SINAV HARÇ ÜCRETİ NASIL YATIRILIR?" + kehribar "3.275 TL".

## Frame 2 — Havale ile yatırın (4.5–9.2)
status: built · src: index.html#ways
rules: spring-pop-entrance, asr-keyword-glow
"Herhangi bir banka" (5.3) · "Mobil uygulama" (6.3) · "Havale" (7.5) kartları.

## Frame 3 — Uygulamada (9.2–12.9)
status: built · src: index.html#cards
rules: ai-tracking-box, svg-path-draw
Kamera "PARA GÖNDER / Başka Hesaba" başlığına yaklaşır, spot ışığı + çerçeve çizilir.

## Frame 4–9 — Form alanları (12.9–50.2)
status: built · src: index.html#cards, #steps
rules: multi-phase-camera, ai-tracking-box, counting-dynamic-scale, stat-bars-and-fills
IBAN → Alıcı adı → Ödeme türü → Tarih (07.10.2026, karakter karakter) → Tutar
(0 → 3.275,00 TL sayaç, 33.4) → Açıklama (GM / GMY / TC + Ad Soyad / örnek).
Üstte 7 adımlı ilerleme çubuğu.

## Frame 10 — DEVAM (50.2–52.5)
status: built · src: index.html#cards
rules: cursor-click-ripple
DEVAM butonunda dokunma dalgası (51.4), beyaz flaş ile onay ekranına geçiş (52.5).

## Frame 11 — Onay ekranı (52.5–57.9)
status: built · src: index.html#cards
rules: ai-tracking-box, svg-path-draw, cursor-click-ripple
Tutar + Toplam Tutar satırları çift çerçeve, onay işareti (53.9), ONAYLA dokunma (57.2).

## Frame 12 — Ödemeden sonra (57.9–70.3)
status: built · src: index.html#tips
rules: waterfall-entry, spring-pop-entrance
Dekontu saklayın (58.3) · 1–2 gün içinde kontrol (60.3) · Geri dönerse müdahale (62.8) ·
Başvurular açılınca dekontu yükleyin (65.9).

## Frame 13 — Kapanış (70.3–73.5)
status: built · src: index.html#outro
rules: spring-pop-entrance
"Hayırlı olsun!" + "Sınav harç ücreti · 3.275 TL".
