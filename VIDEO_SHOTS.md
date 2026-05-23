# DAMAY — Video Shot Lists

Two cuts. The 90s vertical is what gets posted; the 3min landscape is what judges watch on a laptop. Both reference the same screen recordings — capture once, edit twice.

---

## Screen captures to record before any editing

Record each at 1080p min, 60fps where possible. All file names assumed under `docs/raw/`.

| File                              | What                                                                                          | Length |
|-----------------------------------|-----------------------------------------------------------------------------------------------|--------|
| `hero.mov`                        | Hero page idle, mouse off-screen                                                              | 5s     |
| `dashboard-list.mov`              | `/dashboard` showing the seeded **Kapitbahay Kalsada 7** plus 3 past completed rounds         | 6s     |
| `round-detail.mov`                | `/rounds/[id]` for Kapitbahay Kalsada 7, all 6 members visible                                | 8s     |
| `whatsapp-phone.mov`              | Phone screen recording: Twilio sandbox thread, typing `PAY`, send                             | 10s    |
| `timeline-tick.mov`               | Dashboard timeline ticking live from pending → confirmed (Supabase Realtime)                  | 8s     |
| `stellar-expert-tx.mov`           | Stellar Expert tx detail with typed `("pal","contrib")` event payload visible                 | 8s     |
| `reputation-marites.mov`          | `/reputation/[marites]` — score + history, scroll, hover the `-25` default event              | 10s    |
| `qr-final.mov`                    | Repo URL + QR full-screen, slight zoom-in                                                     | 4s     |
| `groupchat-broll.mov`             | Consent-cleared real group chat with paluwagan reminders (or staged reenactment)              | 6s     |
| `gcash-receipt-broll.mov`         | GCash screenshot scrolling — receipts piling up                                               | 4s     |

Audio: record VO clean in one sitting against a soft surface; -16 LUFS target.

---

## A. 90-second vertical (TikTok / IG Reels / YouTube Shorts)

**Target:** stop the scroll in the first 3 seconds; deliver the stat and the unlock by 0:15; pay it off by 1:20.

**Aspect:** 9:16, 1080×1920. **Music bed:** lo-fi Filipino acoustic (e.g. Ben&Ben instrumental loop), -22 LUFS under VO.

| #  | In    | Out   | Action / Composition                                                                                          | VO line (verbatim)                                                              | Source                          |
|----|-------|-------|---------------------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|----------------------------------|
| 1  | 0:00  | 0:03  | Big white text on black: **`₱100,000,000,000`** counting up fast; slams to **`/year`**                        | "One hundred billion pesos. A year."                                            | text animation                   |
| 2  | 0:03  | 0:07  | Cut to `groupchat-broll.mov`, phone in vertical frame, finger scrolling                                       | "This is where Filipinos actually save. Paluwagan. Group chat. GCash receipts." | `groupchat-broll.mov`            |
| 3  | 0:07  | 0:11  | `gcash-receipt-broll.mov` scrolling                                                                            | "Eighteen million of us. Zero of it on financial rails."                        | `gcash-receipt-broll.mov`        |
| 4  | 0:11  | 0:15  | Hard cut to black with red text: **`Organizer ghosts. Group dissolves. No record.`**                          | "One ghosted organizer and the whole thing breaks. No record. No recourse."     | text card                        |
| 5  | 0:15  | 0:20  | Logo reveal: **DAMAY** wordmark, Fraunces, warm cream on deep green                                            | "We built DAMAY."                                                                | logo animation                   |
| 6  | 0:20  | 0:27  | Vertical crop of `dashboard-list.mov`, focused on Kapitbahay Kalsada 7 card                                   | "Organizer creates a paluwagan in the dashboard. Six members, five hundred a week."   | `dashboard-list.mov`        |
| 7  | 0:27  | 0:35  | Vertical crop of `whatsapp-phone.mov` — `PAY` send                                                             | "Members never leave WhatsApp. Type PAY. That's the whole interaction."         | `whatsapp-phone.mov`             |
| 8  | 0:35  | 0:42  | `timeline-tick.mov`, vertical crop centered on the timeline row                                                | "Behind the scenes, every payment is a Stellar transaction. Live, on chain."    | `timeline-tick.mov`              |
| 9  | 0:42  | 0:50  | `stellar-expert-tx.mov`, vertical crop on event payload                                                        | "Anyone can read it. Anyone can verify it. Immutable."                          | `stellar-expert-tx.mov`          |
| 10 | 0:50  | 1:00  | `reputation-marites.mov` — score visible, history scrolling                                                    | "And every member builds a reputation. One missed payment? It's on the record. Recovered? Also on the record."    | `reputation-marites.mov`         |
| 11 | 1:00  | 1:10  | Split screen: WhatsApp on left, Stellar Expert on right, both vertical-cropped                                 | "Same group-chat UX. Cryptographic receipts underneath."                        | composite                        |
| 12 | 1:10  | 1:18  | Text card: **`v1.1 — Late-Night Lend`** / **`v1.2 — Real PHP rails`** / **`v2 — Mainnet`** stacked              | "Next: lending on top of your reputation. Real peso rails. Mainnet."            | text card                        |
| 13 | 1:18  | 1:25  | `qr-final.mov` — QR + `github.com/KpG782/damay`                                                                | "DAMAY. Bring it to your barangay."                                              | `qr-final.mov`                   |
| 14 | 1:25  | 1:30  | Hold on logo + URL, soft fade out                                                                              | (no VO; music tails)                                                             | logo                             |

**Captions:** burn-in Tagalog + English captions throughout. Reels without captions lose 40%+ retention.

**Cover frame:** the `₱100,000,000,000` slam in shot 1.

---

## B. 3-minute landscape (judges' recording)

**Target:** mirror `DEMO_SCRIPT.md` beat-for-beat but with cinematic intent. Single take where possible; cut only on hard beat transitions. **No music bed under voice during dashboard sections — let the product breathe.** Soft music only under hook + roadmap + ask.

**Aspect:** 16:9, 1920×1080. **Camera:** locked tripod for talking head; OBS for screen capture; phone-in-frame via mirror prop on desk (or Continuity Camera).

**Lower-thirds:** introduce once per major section. Font: Fraunces 28pt over a 70%-opacity dark-green bar, lower-left.

| #  | In    | Out   | Composition                                                                              | Action                                                                                                       | Audio                                            |
|----|-------|-------|------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------|--------------------------------------------------|
| 1  | 0:00  | 0:08  | Cold open: tight crop on `groupchat-broll.mov`, slight Ken Burns zoom-in                 | Group chat scrolls; "Maam, paki-transfer na po" reminders visible                                            | Music bed in (-22 LUFS); no VO yet               |
| 2  | 0:08  | 0:20  | Talking head, center frame, eye-line to camera                                            | Ken delivers the hook                                                                                        | VO: "Eighteen million Filipinos save through paluwagan…" |
| 3  | 0:20  | 0:30  | Full-screen stats slide; three bullets fade in one by one                                | Stats card animates                                                                                          | VO: "Paluwagan runs on three things…"            |
| 4  | 0:30  | 0:40  | Pivot to talking head, lower-third: **"Ken Patrick Garcia · DAMAY"**                     | Transition line into the demo                                                                                | VO: "When trust breaks, there's no record…"     |
| 5  | 0:40  | 0:55  | Screen capture full-screen: `dashboard-list.mov`                                          | Mouse hovers Kapitbahay Kalsada 7; clicks in                                                                 | VO: "Here is Kapitbahay Kalsada 7…"             |
| 6  | 0:55  | 1:00  | Continue screen capture: `round-detail.mov`                                               | All six members visible; cursor circles the contract ID chip                                                 | VO: "Six neighbors. Five hundred pesos. Six weeks."             |
| 7  | 1:00  | 1:10  | Picture-in-picture: dashboard left 60%, mirrored phone right 40%                          | Phone shows Twilio sandbox; Ken types `PAY`; tap send                                                        | VO: "Members never leave WhatsApp…"             |
| 8  | 1:10  | 1:20  | Full screen capture: `timeline-tick.mov`                                                  | Timeline row goes from `pending` to `confirmed`; subtle pulse animation                                      | VO: "Webhook hits API, idempotency catches dupes, worker queues Soroban tx." |
| 9  | 1:20  | 1:30  | Hold on dashboard; lower-third graphic: **"Stellar Testnet · Soroban event"**            | Cursor hovers the Stellar Expert link in the timeline row                                                    | VO: "Status flips confirmed when Horizon confirms. No refresh."          |
| 10 | 1:30  | 1:45  | Full screen: `stellar-expert-tx.mov`                                                      | Click into tx; event payload `("pal","contrib")` highlighted with cursor                                     | VO: "This is what judges should grep for…"      |
| 11 | 1:45  | 2:00  | Picture-in-picture: Stellar Expert left, talking head right (small)                       | Ken says the trust-layer line; eye contact with camera                                                       | VO: "Members see WhatsApp. Organizer sees a dashboard. The trust layer is here, on chain." |
| 12 | 2:00  | 2:15  | Full screen: `reputation-marites.mov`                                                     | Scroll Marites' history; pause on the `-25` default event                                                    | VO: "Here is Marites. Three rounds. One late payment…" |
| 13 | 2:15  | 2:30  | Continue capture; cursor clicks the default event → opens Stellar Expert                  | Tx detail loads; cursor circles the event payload                                                            | VO: "Her score follows her. Any future product can read it. Same trustline, different products." |
| 14 | 2:30  | 2:40  | Roadmap slide, three bullets fade in one by one                                            | Slide animates                                                                                               | VO: "Version 1.1 — Late-Night Lend…"            | 
| 15 | 2:40  | 2:50  | Talking head, lower-third: **"github.com/KpG782/damay"**                                  | Ken delivers the rails + mainnet line                                                                        | VO: "…real peso rails. Mainnet. White-label."   |
| 16 | 2:50  | 2:57  | `qr-final.mov` — full-screen QR + repo URL                                                | QR pulses once                                                                                               | VO: "Bring DAMAY to your barangay. Salamat po." |
| 17 | 2:57  | 3:00  | Hold on logo + URL; soft music tail; subtle fade to black                                 | End card                                                                                                     | Music tail only                                  |

**Props on desk:** phone (mirrored or in real shot), notebook with `kapitbahay-kalsada-7` written on the cover (subtle Filipino warmth detail), a halved pan de sal on a plate (visible blur in talking-head shots — communal/breakfast cue, not the focus).

**Recording order:** capture all screen recordings first (one continuous demo run), then record VO over them, then record talking-head shots (2, 4, 11, 15) as B-roll inserts. Edit final.

**Export specs:** H.264 MP4, CRF 18, 1920×1080 @ 30fps, AAC 320kbps stereo. Two deliverables: `damay-judges-3min.mp4` (main) and `damay-judges-3min-captioned.mp4` (burnt-in EN captions for accessibility submission).
