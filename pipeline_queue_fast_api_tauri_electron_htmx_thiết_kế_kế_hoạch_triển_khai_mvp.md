# Pipeline Queue FastAPI + Tauri/Electron + htmx — Thiết kế & Kế hoạch triển khai (MVP)

> **Mục tiêu**: Xây dựng pipeline bán tự động từ link → tải video → đổi tốc độ → (cắt nếu dài) → STT (FunASR) → dịch (Gemini) → render video + phụ đề (VI) → báo cáo. Hỗ trợ **hàng chờ (queue)**, theo dõi **clipboard** bằng **Tauri/Electron**, UI nhẹ bằng **htmx**. Tập trung cho tiếng Trung → tiếng Việt.

---

## 1) Kiến trúc tổng thể

- **Desktop**: Tauri/Electron (watch clipboard → gửi link sang API), có Settings (API keys, thư mục lưu, tốc độ, giới hạn dung lượng…).
- **Backend**: FastAPI + Worker Queue (Redis RQ/Dramatiq/Arq – MVP dùng **RQ** cho đơn giản). DB: SQLite (MVP), có thể nâng lên Postgres.
- **Jobs**: mỗi link là 1 Job gồm nhiều **Task** tuần tự; có **retry**/**resume** theo bước.
- **Storage**: thư mục do user chọn `flim/`, mỗi tập đặt tên: `01 flim.mp4`, các part: `01 flim part1.mp4`…
- **Third-party tools**: `yt-dlp`, `ffmpeg`, `funasr` (tiếng Trung), Google Gemini API.
- **UI Web**: FastAPI + Jinja + **htmx** (poll/SSE tiến độ, xem log, tải output).

### Sơ đồ thành phần (Mermaid)
```mermaid
flowchart LR
  subgraph Desktop[Tauri/Electron]
    CB[Clipboard Watcher]\n(Settings)
  end
  subgraph API[FastAPI]
    J[Jobs API]\n(REST)
    Q[Queue RQ]\n(Redis)
    DB[(SQLite)]
    SSE[SSE/htmx endpoints]
  end
  subgraph Worker[Workers]
    DL[yt-dlp]
    FF[ffmpeg]
    CUT[Silence-aware Split]
    ASR[FunASR -> SRT]
    TR[Gemini Translate]
    RD[Render+Burn Sub]
    RP[Report]
  end

  CB -- POST /jobs --> J
  J -- enqueue --> Q
  Q --> DL --> FF --> CUT --> ASR --> TR --> RD --> RP --> DB
  SSE -- status/logs --> Desktop
```

---

## 2) Luồng xử lý (đã chỉnh sửa)

**Clipboard** → **/jobs** → **Tải** → **Đổi tốc độ** → **(Nếu >20p thì cắt theo khoảng lặng, mỗi ≤25p)** → **STT FunASR → SRT** → **Dịch Gemini (chunk ≤1500 ký tự, random API key, hậu kiểm & retry)** → **Render (giảm -30dB nền, scale 1080p, zoom 130%, burn-in SRT VI)** → **Báo cáo + DONE**.

---

## 3) Quy tắc đặt tên & thư mục

- **Thư mục gốc do người dùng chọn**: ví dụ `flim/`.
- **Tên tập**: `<ep> <show>.mp4` với `ep` là 2 chữ số: `01 flim.mp4`, `02 flim.mp4`…
- **Part sau cắt**: `01 flim part1.mp4`, `01 flim part2.mp4`…
- **Phụ đề**: trùng tên video + `.srt`: `01 flim part1.srt`.
- **Output cuối**: `01 flim end.mp4` hoặc `01 flim part1 end.mp4`.
- **Temp**: đặt ở `flim/.tmp/<jobId>/` (tự dọn sau DONE/FAILED).

---

## 4) Cấu trúc dự án (mono-repo đơn giản)

```
project/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                  # FastAPI bootstrap, routers, SSE
│  │  ├─ config.py                # load .env, settings
│  │  ├─ deps.py
│  │  ├─ models.py                # SQLAlchemy (Job, Task, Artifact)
│  │  ├─ schemas.py               # Pydantic
│  │  ├─ jobs_router.py           # POST /jobs, GET /jobs/{id}
│  │  ├─ sse_router.py            # /jobs/{id}/stream
│  │  ├─ views.py                 # htmx pages
│  │  ├─ queue.py                 # RQ setup, enqueue helpers
│  │  ├─ workers/
│  │  │  ├─ pipeline.py           # Orchestrator (state machine)
│  │  │  ├─ steps_download.py     # yt-dlp/ffmpeg HLS
│  │  │  ├─ steps_speed.py        # setpts/atempo
│  │  │  ├─ steps_cut.py          # silence-aware split
│  │  │  ├─ steps_asr.py          # FunASR→SRT
│  │  │  ├─ steps_translate.py    # Gemini chunking+QA
│  │  │  ├─ steps_render.py       # ffmpeg render + subtitles
│  │  │  └─ steps_report.py       # metrics, JSON report
│  │  ├─ services/
│  │  │  ├─ ffmpeg.py             # wrappers & probes
│  │  │  ├─ ytdlp.py
│  │  │  ├─ srt_utils.py          # split/merge, QA, regex
│  │  │  ├─ funasr_client.py
│  │  │  └─ gemini_client.py
│  │  ├─ templates/               # Jinja + htmx partials
│  │  └─ static/
│  ├─ worker.py                   # rq worker entry
│  └─ requirements.txt
├─ desktop/
│  ├─ tauri/ or electron/
│  │  ├─ src/
│  │  │  ├─ main.(ts|js)          # app, tray, clipboard watcher
│  │  │  └─ settings.(tsx|vue)
│  │  └─ package.json / tauri.conf.json
├─ scripts/
│  ├─ ffprobe.bat/.sh
│  ├─ dev_redis.bat/.sh
│  └─ run_worker.bat/.sh
├─ .env.example
├─ README.md
└─ CODEX_TODO.md                   # Dấu neo sinh mã tự động
```

---

## 5) Biến môi trường & cấu hình

```ini
# .env.example
APP_BASE_URL=http://127.0.0.1:8000
STORAGE_ROOT=D:/videos/flim
MAX_DOWNLOAD_SIZE_MB=2000           # từ chối quá giới hạn
FORBID_LIVESTREAM=true
FORBID_DRM=true
DEFAULT_SPEED=1.15                  # người dùng có thể override
SPLIT_THRESHOLD_MIN=20
MAX_PART_DURATION_MIN=25
REDIS_URL=redis://127.0.0.1:6379/0
DB_URL=sqlite:///./app.db
# Danh sách API key (phân tách bằng dấu phẩy)
GEMINI_API_KEYS=key1,key2,key3
# FunASR
FUNASR_MODEL=paraformer-zh
FUNASR_DEVICE=cpu
```

**Settings có thể override theo Job**: tốc độ video, thư mục lưu, giới hạn kích thước, cho phép/không cho phép cắt, v.v.

---

## 6) State machine Job & Task

**Job.states**: `PENDING → QUEUED → RUNNING → (PAUSED) → DONE | FAILED`  
**Task list (tuần tự)**: `download → speed → cut? → asr → translate → render → report`

Mỗi **Task**:
- input/output rõ ràng (file path, metadata)
- `retries: int`, `max_retries: 3` (riêng dịch: 3 vòng hậu kiểm)
- ghi **artifacts** (video part, srt, json report)
- cập nhật **progress** (% ước lượng theo bước)

---

## 7) API hợp đồng (FastAPI)

### 7.1 POST `/jobs`
**Body (JSON)**
```json
{
  "source_url": "https://...",
  "show_name": "flim",
  "episode": 1,
  "options": {
    "speed": 1.15,
    "storage_root": "D:/videos/flim",
    "allow_cut": true,
    "max_download_size_mb": 2000
  }
}
```
**Resp**
```json
{ "job_id": "J20250827-0001", "state": "QUEUED" }
```

### 7.2 GET `/jobs/{job_id}` → trạng thái + artifacts

### 7.3 GET `/jobs/{job_id}/stream` (SSE) → events: `state`, `progress`, `log`, `artifact`

### 7.4 GET `/artifacts/{id}` → tải file output

### 7.5 POST `/jobs/{job_id}/cancel` | `/retry` | `/pause` | `/resume`

> **UI htmx**: dùng `hx-get` + `hx-swap` để poll/stream, bảng Job list, chi tiết Job, nút tải.

---

## 8) Tích hợp công cụ & công thức chuẩn

### 8.1 Tải link
- **yt-dlp** cho YouTube/Bilibili… (từ chối livestream/DRM dựa trên metadata)
- **ffmpeg** cho HLS/M3U8 trực tiếp
- Đặt tên tệp theo quy tắc (episode + show name). Kiểm tra **kích thước** sau tải, nếu vượt `MAX_DOWNLOAD_SIZE_MB` → FAIL.

**Gợi ý lệnh**
```bash
yt-dlp -o "%(title)s.%(ext)s" --no-live-from-start --no-part --restrict-filenames <URL>
```

### 8.2 Đổi tốc độ (áp dụng trước khi cắt)
- Video: `setpts=PTS/<speed>`
- Audio: chuỗi `atempo` (mỗi filter hỗ trợ ~0.5–2.0). Ví dụ speed 1.15 → `atempo=1.15`.

**Gợi ý lệnh**
```bash
ffmpeg -i input.mp4 -vf "setpts=PTS/1.15" -af "atempo=1.15" -c:v libx264 -c:a aac -movflags +faststart output_speed.mp4
```

### 8.3 Cắt theo khoảng lặng (≤25 phút/part)
- Dùng `ffmpeg` để dò **khoảng lặng** (silencedetect) rồi chọn **điểm cắt gần nhất** trước khi vượt 25 phút.
- Nếu không tìm thấy khoảng lặng phù hợp → cắt cứng tại 25 phút.

**Quy trình**
1. Chạy `ffmpeg -af silencedetect=noise=-30dB:d=0.5 -f null -` để lấy log thời điểm im lặng.
2. Parse timestamps → chọn mốc ≤25:00 gần nhất (có buffer ±5s).
3. Dùng `-ss`/`-to` để tách part; lặp cho đến hết video.

**Gợi ý lệnh tách một đoạn**
```bash
ffmpeg -ss 00:00:00 -to 00:24:58 -i input_speed.mp4 -c copy part1.mp4
```

### 8.4 STT (FunASR → SRT)
- Model: `paraformer-zh` (tuỳ chọn), device CPU/GPU.
- Xuất **SRT** với timestamps. Chuẩn hoá văn bản: loại tạp âm, khoảng trắng, **dấu câu TQ → kiểu VI thân thiện**.

> Mẹo: nếu FunASR trả JSON/CTM, viết `srt_utils.py` để map thành cues 1–N, mỗi cue ≤ max ký tự (không cắt từ giữa).

### 8.5 Dịch (Gemini)
- **Danh sách API key** (ENV) → **random pick** cho mỗi chunk.
- **Chia nhỏ SRT** theo **khối  ≤1500 ký tự** *giữ nguyên cấu trúc cue* (gộp nhiều cue thành 1 batch nhưng không vượt 1500).
- **Prompt** theo phong cách **truyện chữ Việt (TruyenCV.vn)**, dịch sát nghĩa nhưng tự nhiên.
- **Hậu kiểm**:
  - Nếu còn **ký tự Hán** (`[\p{Script=Han}]`) → re-translate batch.
  - Nếu **số thứ tự/timestamps** lệch cấu trúc → re-translate.
  - Tối đa **3 lần retry**/batch.
- **Giữ nguyên định dạng SRT**.

**Prompt gợi ý (mẫu)**
```
Bạn là dịch giả phụ đề Trung→Việt. Hãy dịch sát nghĩa nhưng tự nhiên,
phong cách truyện chữ phổ biến ở Việt Nam (giọng văn gần gũi, chuẩn ngữ pháp),
trả về NGUYÊN VẸN theo định dạng SRT đầu vào (giữ số thứ tự và timestamps).
Không thêm/bớt câu từ.
```

### 8.6 Render “video kết thúc”
- **Âm lượng nền**: `-30dB` (volume filter)
- **Scale**: 1920×1080 (giữ tỷ lệ, letterbox nếu cần)
- **Zoom**: phóng 130% + căn giữa để loại bỏ viền đen (dùng `crop` hoặc `scale+zoompan`/`vf=scale,setsar,crop`).
- **Phụ đề**: burn-in SRT (libass). Có thể convert SRT→ASS để style viền/đổ bóng.

**Gợi ý lệnh mẫu**
```bash
ffmpeg -i input_part.mp4 -vf "scale=1920:-2, crop=1920:1080, subtitles='part_vi.srt'" \
  -af "volume=-30dB" -c:v libx264 -c:a aac -movflags +faststart output_end.mp4
```
> Tuỳ chất lượng nguồn, điều chỉnh chuỗi filter để tránh méo hình. Nếu phụ đề không hiển thị, kiểm tra build ffmpeg (libass).

### 8.7 Báo cáo
- JSON + hiển thị UI: thời lượng gốc/đã đổi tốc độ, số part, số câu SRT, tỷ lệ nhận dạng (nếu có), thời gian tiêu tốn theo bước.

---

## 9) Thuật toán chia/gộp SRT để dịch

**Chia (chunk ≤1500 ký tự)**
1. Duyệt cue theo thứ tự, cộng dồn `len(text)+margin`.
2. Nếu sắp vượt ngưỡng → kết sổ chunk hiện tại, mở chunk mới.
3. Không tách giữa một cue.

**Gộp**
- Gắn kết quả dịch theo **cùng chỉ mục cue**.
- Bảo toàn `index` & `timestamp`.

**Hậu kiểm**
- Regex Han: `r"[\u3400-\u9FFF\uF900-\uFAFF]"`.
- Kiểm đếm số cue trước/sau.
- Validate timestamps: `HH:MM:SS,ms --> HH:MM:SS,ms`.

---

## 10) Chính sách chặn Job

- Từ chối nếu: livestream/DRM phát hiện qua metadata, hoặc vượt `MAX_DOWNLOAD_SIZE_MB`.
- Từ chối link không hỗ trợ.
- Log lý do trong Job → state `FAILED`.

---

## 11) Desktop App (Tauri/Electron)

### 11.1 Clipboard Watcher
- Theo dõi **clipboard** (văn bản). Khi phát hiện **URL mới** (regex), debounce 1–2s.
- Gửi `POST /jobs` với cấu hình mặc định từ **Settings**.
- Tray icon hiển thị số Job đang chạy, thông báo khi DONE/FAILED.

**Pseudocode**
```ts
const last = new Set<string>();
setInterval(async () => {
  const text = await readClipboard();
  if (isURL(text) && !last.has(text)) {
    last.add(text);
    await fetch(API + "/jobs", { method: "POST", body: JSON.stringify(payload(text))});
  }
}, 1500);
```

### 11.2 Settings
- API Base URL, thư mục lưu, tốc độ mặc định, ngưỡng cắt, danh sách Gemini Keys, bật/tắt tự gửi clipboard.

---

## 12) UI htmx (MVP)

- `/` — Job list (bảng), nút "New Job" (form URL, episode, show name)
- `/jobs/{id}` — chi tiết: tiến độ theo bước, log (auto-refresh via `hx-get`/SSE), link tải artifacts.
- Partial templates: `job_row.html`, `job_detail.html`, `artifact_btn.html`.

**Snippet ý tưởng**
```html
<div hx-get="/jobs/{{id}}/panel" hx-trigger="load, every 2s" hx-swap="outerHTML"></div>
```

---

## 13) Logging, tiến độ & SSE

- Mỗi Task push log theo cấp: INFO/WARN/ERROR.
- **Progress** theo % trọng số: download 20, speed 10, cut 10, asr 25, translate 20, render 10, report 5 (tinh chỉnh sau).
- **SSE** phát log/tiến độ real-time; htmx có thể dùng `hx-ext="sse"`.

---

## 14) Chi tiết triển khai các bước (pseudo)

### 14.1 `steps_download.py`
- Quyết định công cụ: nếu URL chứa HLS/M3U8 → ffmpeg; else yt-dlp.
- Validate MIME/size/DRM.

### 14.2 `steps_speed.py`
- Probe duration (ffprobe) → tính duration mới.

### 14.3 `steps_cut.py`
- Chạy silencedetect → chọn điểm cắt đẹp.
- Xuất danh sách parts + mapping tên file.

### 14.4 `steps_asr.py`
- Với mỗi part → chạy FunASR → SRT. Chuẩn hoá dấu câu, xóa filler như "嗯", "啊" nếu model trả về.

### 14.5 `steps_translate.py`
- Chunk SRT → gọi Gemini với prompt mẫu.
- QA → nếu fail, random key khác + retry ≤3.

### 14.6 `steps_render.py`
- Áp volume, scale 1080p, crop/zoom 130%, burn subtitle (SRT VI). Output `* end.mp4`.

### 14.7 `steps_report.py`
- Tổng hợp số liệu, ghi JSON + render bảng trong UI.

---

## 15) Mẫu schema DB (SQLAlchemy)

- **Job**: id, source_url, show_name, episode, state, created_at, updated_at, options(JSON), error_msg
- **Task**: id, job_id, name, state, try_count, logs(text), started_at, finished_at
- **Artifact**: id, job_id, type(video/srt/report), path, size

---

## 16) Kiểm thử & QA

- **Unit**: srt split/merge, han regex, timestamp parser, silence picker.
- **Integration**: sample link ngắn, link dài >20p, HLS, từ chối livestream/DRM.
- **E2E**: từ clipboard → DONE, kiểm tra file tên, style phụ đề.

---

## 17) Lộ trình triển khai

- **MVP (v0.1)**: Queue RQ, tải → speed → cut → asr → translate → render, UI htmx đơn giản, desktop watcher.
- **v0.2**: GPU cho FunASR, parallel parts, Postgres, account multi-user, preset style phụ đề, retry thông minh theo lỗi.
- **v0.3**: Dashboard thống kê, batch import, profile tối ưu ffmpeg theo phần cứng.

---

## 18) Dấu neo sinh mã (để Codex/AI tạo mã tự động)

> Đặt trong `CODEX_TODO.md` hoặc comment trong file tương ứng.

```md
- [ ] <!-- CODEX: backend/init --> Tạo FastAPI skeleton + RQ + SQLite models & migrations
- [ ] <!-- CODEX: api/jobs --> Sinh router /jobs (POST/GET), /stream (SSE), /artifacts
- [ ] <!-- CODEX: workers/pipeline --> Sinh orchestrator + state machine
- [ ] <!-- CODEX: steps/download --> Tạo bước tải (yt-dlp/HLS) + validate size/DRM
- [ ] <!-- CODEX: steps/speed --> Bước đổi tốc độ (setpts/atempo) + ffprobe
- [ ] <!-- CODEX: steps/cut --> Bước cắt theo khoảng lặng (silencedetect) + tách part
- [ ] <!-- CODEX: steps/asr --> Tích hợp FunASR → SRT + chuẩn hoá văn bản
- [ ] <!-- CODEX: steps/translate --> Tích hợp Gemini (keys pool, chunk 1500, QA, retry)
- [ ] <!-- CODEX: steps/render --> ffmpeg render (volume -30dB, scale 1080p, zoom 130%, burn subtitle)
- [ ] <!-- CODEX: steps/report --> Tổng hợp báo cáo JSON + UI
- [ ] <!-- CODEX: desktop/clipboard --> App Tauri/Electron watcher + Settings
- [ ] <!-- CODEX: ui/htmx --> Trang list jobs + job detail + SSE/polling
- [ ] <!-- CODEX: packaging --> Scripts run dev, worker, redis
```

---

## 19) Ghi chú triển khai thực tế

- Kiểm tra build `ffmpeg` có `libass` để burn SRT, hoặc chuyển SRT → ASS bằng `ffmpeg -i in.srt out.ass` và dùng `ass=` filter.
- Khi zoom 130% cần tính crop theo tỷ lệ video nguồn để tránh méo.
- FunASR/ASR có thể trả thời gian lệch nhỏ → cân nhắc snap mốc thời gian về bội số 10–20ms để sạch SRT.
- Gemini: đặt `safetySettings` để tránh cắt nội dung; set `temperature` thấp 0.2–0.4 để giữ sát nghĩa.
- Đảm bảo Unicode Normalization (NFC) trước khi ghi SRT tiếng Việt.

---

## 20) Phụ lục: Regex & helpers

- **URL**: `https?://[^\s]+`
- **Han**: `[\u3400-\u9FFF\uF900-\uFAFF]`
- **Timestamp SRT**: `\d{2}:\d{2}:\d{2},\d{3}`

**Pseudocode chọn mốc cắt**
```py
silences = parse_silencedetect(log)
cutpoints = []
next_limit = 25*60
for s in silences:
    if s.time <= next_limit - 2:   # buffer 2s
        candidate = s.time
    else:
        cutpoints.append(candidate if candidate else next_limit)
        next_limit += 25*60
```

---

*Tài liệu này là đặc tả chi tiết cho MVP. Có thể đẩy thẳng vào Cursor/Codex để sinh scaffold và từng bước triển khai.*

