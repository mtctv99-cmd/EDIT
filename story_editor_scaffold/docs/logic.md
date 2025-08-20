# Hướng dẫn triển khai **logic** (kết nối Gemini CLI) cho Story Editor

> Mục tiêu: sau khi giao diện (UI scaffold) đã sẵn, ta **điền logic** để bấm **Run** là gọi **Gemini CLI** xử lý ảnh + prompt, trả về văn bản và **ghi thẳng vào ô Text** của từng hàng. Tài liệu này tập trung vào **cách nối dây** và **mẫu mã** – bạn có thể thay thế bằng bất kỳ CLI/model nào.

---

## 0) Tư duy tổng quát

1. **UI phát lệnh** (nút Run trong `MainWindow`) → gom **ngữ cảnh** + **prompt** + **ảnh** của hàng cần xử lý.
2. **Adapter lớp Core** gọi **CLI** (qua `subprocess`) theo **mẫu lệnh cấu hình** → nhận `stdout/stderr/mã thoát`.
3. **Parse kết quả** (text/json) → cập nhật **row.text_edit** tương ứng.
4. Nếu bật **Giữ ngữ cảnh** → đẩy (prompt, image(s), output) vào `ProjectManager.context_history` (giới hạn N).

---

## 1) Chuẩn bị CLI (placeholder an toàn)

**Gemini CLI** hiện có nhiều cách cài/biến thể. Để tránh phụ thuộc tên/tham số cụ thể, ta cấu hình một **mẫu lệnh** (command template) trong `API Manager` hoặc `settings.json`:

Ví dụ (Windows PowerShell):
```text
gemini_cmd_template: "gemini --model {model} --input-text '{prompt}' --input-image {image}"
gemini_model: "gemini-1.5-pro"
```

> **Bạn chỉnh `gemini_cmd_template` đúng với CLI bạn dùng.**  
> Chỉ cần giữ lại các placeholder: `{model}`, `{prompt}`, `{image}` (có thể mở rộng thêm `{output}`, `{extra}`).

### Lưu ý
- Nếu CLI đọc key từ **biến môi trường**, thêm vào `API Manager` key và **set env** trước khi chạy `subprocess`.  
- Nếu CLI nhận **file prompt** thay vì chuỗi, thay template bằng `{prompt_file}` (xem phần 4).

---

## 2) Thu gom dữ liệu từ UI

Ta cần **hàng hiện tại** (hoặc nhiều hàng) để gửi ảnh + prompt:

- `EditorScreen` chứa danh sách `RowWidget` (ảnh + text).  
- Mỗi `RowWidget` đã có:
  - `self._image_path`
  - `self.text_edit`

Bạn có thể bắt đầu **đơn giản**: xử lý **hàng đầu tiên có ảnh** hoặc **hàng đang focus**. Sau đó mở rộng thành **chạy theo batch**.

Mẫu lấy tất cả hàng có ảnh:
```python
def collect_rows_with_images(editor_screen):
    rows = []
    layout = editor_screen.vbox
    for i in range(layout.count()):
        w = layout.itemAt(i).widget()
        if hasattr(w, "_image_path") and w._image_path:
            rows.append(w)
    return rows
```

---

## 3) Lấy prompt & chế độ “Giữ ngữ cảnh”

- Prompt được chọn từ **Prompt Manager** (dropdown trên toolbar).  
- Lấy nội dung prompt theo **tên**:
```python
from story_editor.core.prompt_store import PromptStore

def get_prompt_by_name(name: str) -> str:
    for p in PromptStore.list_prompts():
        if p.get("name") == name:
            return p.get("text", "")
    return ""
```

- **Templating đơn giản** (optional): format prompt với biến `{row_index}`, `{image_name}`,…
```python
prompt = base_prompt.format(
    row_index=i,
    image_name=os.path.basename(row._image_path or ""),
)
```

- **Giữ ngữ cảnh**: nối các lượt trước vào prompt (nếu bạn muốn duy trì mạch lạc) – ví dụ:
```python
def build_prompt_with_context(base_prompt, pm, max_turns=6):
    parts = []
    # pm.context_history: list of dicts {"prompt":..., "response":..., "images":[...]}
    for turn in pm.context_history[-max_turns:]:
        parts.append(f"[Trước đó]\nPrompt:\n{turn['prompt']}\nKết quả:\n{turn['response']}\n")
    parts.append(f"[Hiện tại]\n{base_prompt}")
    return "\n\n".join(parts)
```

> Tùy mô hình/CLI, bạn có thể truyền ngữ cảnh dưới dạng **system prompt**, **history** hoặc **text thường**.

---

## 4) Adapter gọi CLI (Core)

Tạo file mới `story_editor/core/ai_client.py` để **gom mọi lệnh CLI** về một nơi.

**Mẫu `ai_client.py`:**
```python
# story_editor/core/ai_client.py
import os, shlex, subprocess, tempfile

class AIClient:
    @staticmethod
    def run_cmd_template(cmd_template: str, model: str, prompt: str, image: str, env: dict = None, prompt_file_mode=False):
        """
        Chạy lệnh CLI theo template. 
        - cmd_template: "gemini --model {model} --input-text {prompt} --input-image {image}"
        - Nếu CLI yêu cầu prompt từ file, đặt prompt_file_mode=True để ghi ra file tạm và dùng {prompt_file}.
        """
        tmp_prompt_file = None
        try:
            if prompt_file_mode:
                fd, path = tempfile.mkstemp(suffix=".txt")
                os.close(fd)
                with open(path, "w", encoding="utf-8") as f:
                    f.write(prompt)
                tmp_prompt_file = path
                cmd = cmd_template.format(model=model, prompt_file=shlex.quote(path), image=shlex.quote(image), prompt=shlex.quote(prompt))
            else:
                cmd = cmd_template.format(model=model, prompt=shlex.quote(prompt), image=shlex.quote(image))

            # Chuẩn bị env (để đưa API KEY cho CLI nếu cần)
            run_env = os.environ.copy()
            if env:
                run_env.update(env)

            # Thực thi
            proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=run_env)
            ok = (proc.returncode == 0)
            return ok, proc.stdout.strip(), proc.stderr.strip(), proc.returncode
        finally:
            if tmp_prompt_file and os.path.exists(tmp_prompt_file):
                try: os.remove(tmp_prompt_file)
                except: pass
```

> Bạn tùy biến `cmd_template` cho **Gemini CLI** bạn dùng. Nếu CLI bắt buộc nhiều ảnh, thêm `{images}` và join `" ".join(shlex.quote(p) for p in image_list)`.

---

## 5) “Điền logic” vào `MainWindow` (nút **Run**)

Trong `story_editor/main_window.py`, thay `_action_run_stub` bằng **hàm thật**:

```python
from .core.ai_client import AIClient
from .core.prompt_store import PromptStore
from .core.settings import Settings
import os

def _action_run(self):
    provider = self.combo_tool.currentText()
    keep_ctx = self.chk_context.isChecked()

    if provider != "Gemini":
        QMessageBox.information(self, "Run", "Hiện chỉ demo Gemini (CLI)")
        return

    # 1) Lấy prompt
    prompt_name = self.combo_prompt.currentText()
    base_prompt = ""
    for p in PromptStore.list_prompts():
        if p.get("name") == prompt_name:
            base_prompt = p.get("text","")
            break

    if not base_prompt or prompt_name == "(chưa có prompt)":
        QMessageBox.warning(self, "Prompt", "Chưa chọn prompt hợp lệ.")
        return

    # 2) Tham số CLI từ Settings (API Manager có thể đã lưu model, template)
    cfg = Settings.load_api_config()
    cmd_template = cfg.get("gemini_cmd_template", "gemini --model {model} --text {prompt} --image {image}")
    model = cfg.get("gemini_model", "gemini-1.5-pro")
    # Nếu CLI cần key trong ENV:
    env = {}
    api_key = cfg.get("gemini_api_key")
    if api_key:
        env["GEMINI_API_KEY"] = api_key

    # 3) Gom hàng cần xử lý
    rows = []
    L = self.editor_screen.vbox
    for i in range(L.count()):
        w = L.itemAt(i).widget()
        if getattr(w, "_image_path", None):
            rows.append(w)

    if not rows:
        QMessageBox.information(self, "Run", "Không có ảnh để xử lý.")
        return

    # 4) Chạy từng hàng
    for idx, row in enumerate(rows):
        prompt = base_prompt
        if keep_ctx:
            # ví dụ ghép ngữ cảnh đơn giản
            history = self.project_manager.context_history[-6:]
            for turn in history:
                prompt += f"\n\n[Trước đó] Prompt: {turn['prompt']}\nKết quả: {turn['response']}\n"
        prompt += f"\n\n[Ảnh hiện tại]: {os.path.basename(row._image_path)}"

        ok, out, err, code = AIClient.run_cmd_template(
            cmd_template=cmd_template,
            model=model, prompt=prompt, image=row._image_path,
            env=env,
            prompt_file_mode=False  # đổi True nếu CLI yêu cầu file prompt
        )

        # 5) Ghi kết quả
        if ok:
            row.text_edit.setPlainText(out)
            # Lưu context đơn giản
            self.project_manager.context_history.append({
                "prompt": prompt,
                "response": out,
                "images": [row._image_path],
            })
            # Cắt lịch sử
            self.project_manager.context_history = self.project_manager.context_history[-20:]
        else:
            row.text_edit.append(f"\n\n[ERROR CLI {code}]\n{err}")
```

Đừng quên thay **hook** trong toolbar:
```python
# trong _build_toolbar():
act_run = QAction("Run", self)
act_run.triggered.connect(self._action_run)   # <— thay _action_run_stub
tb.addAction(act_run)
```

> Đây là **luồng tối thiểu** để chạy: gom prompt → xây lệnh CLI → gọi → đổ kết quả.

---

## 6) Xây mẫu lệnh CLI (template) cho các trường hợp phổ biến

### 6.1. CLI nhận **prompt string** + **1 ảnh**
```text
gemini --model {model} --text {prompt} --image {image}
```

### 6.2. CLI nhận **prompt từ file** + **1 ảnh**
```text
gemini --model {model} --prompt-file {prompt_file} --image {image}
```
Trong code: `prompt_file_mode=True`.

### 6.3. Nhiều ảnh (nếu cần)
Thay `{image}` → `{images}` và chuyển list → chuỗi:
```python
images_arg = " ".join(shlex.quote(p) for p in image_list)
cmd = cmd_template.format(model=model, prompt=..., images=images_arg)
```

> **Quan trọng**: mỗi CLI thật sẽ có cờ riêng (`--model`, `-m`, `--text`, `--input`, `--image` …). Hãy chỉnh `gemini_cmd_template` cho khớp CLI bạn dùng.

---

## 7) Đồng bộ Save/Load Project (khuyến nghị)

Khi nhấn **Save**/ **Save As**:
- Duyệt toàn bộ `RowWidget` để update `ProjectManager.data = [(image_path, text), ...]` trước khi gọi `save_project()`.
- Khi **Load** → `editor_screen.load_from_manager()` sẽ vẽ lại mọi hàng.

Mẫu gom dữ liệu khi Save:
```python
def sync_ui_to_pm(self):
    data = []
    L = self.editor_screen.vbox
    for i in range(L.count()):
        w = L.itemAt(i).widget()
        if not hasattr(w, "_image_path"): continue
        text = w.text_edit.toPlainText()
        data.append((w._image_path, text))
    self.project_manager.data = data
```

Gọi `sync_ui_to_pm()` **trước** `self.project_manager.save_project(...)`.

---

## 8) Xử lý lỗi & retry

- Nếu `returncode != 0`: hiện lỗi ra text box và **log** vào console.
- Có thể `retry` 1–2 lần với `sleep`/`backoff` khi gặp `429/5xx` (tùy CLI).
- Đừng quên **escape** prompt ảnh hưởng shell (dùng `shlex.quote`).

---

## 9) Nâng cấp tiếp theo (gợi ý)

- Batch theo **vùng chọn** (chỉ xử lý các hàng đang chọn).
- **OCR cục bộ** (Tesseract) như một provider khác trong dropdown.
- Pipeline “ảnh → OCR → dịch → rewrite → SRT” (xâu chuỗi nhiều lượt Run, dùng **Giữ ngữ cảnh**).
- Ghi **log phiên** để phục hồi khi app crash.
- Cho phép **model per action** (chọn model riêng cho OCR/Rewrite).

---

## 10) Checklist tích hợp nhanh

- [ ] Thêm `story_editor/core/ai_client.py` (mã ở mục 4)
- [ ] Thay `_action_run_stub` → `_action_run` (mục 5)
- [ ] Bổ sung hàm `sync_ui_to_pm()` và gọi trước khi Save
- [ ] Nhập CLI template + model + API key trong **API Manager**
- [ ] Tạo vài prompt trong **Prompt Manager**
- [ ] Bật “Giữ ngữ cảnh” nếu cần
- [ ] Test với 1 ảnh → nhiều ảnh
- [ ] Xử lý lỗi & ghi log

---

**Kết luận:** Với cơ chế **command-template + adapter `AIClient`**, bạn có thể **đổi bất kỳ CLI** nào (Gemini/OpenAI/Local) chỉ bằng sửa template & env, còn UI/logic giữ nguyên. Điều này giúp dự án dễ mở rộng và bảo trì lâu dài.
