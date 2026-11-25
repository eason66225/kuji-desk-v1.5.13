# HANDOFF.md — 唯一溝通管道

> 開工前先讀 `AGENTS.md` 與本檔。
> **只能在檔案底部「紀錄」區追加**，不可刪改他人紀錄。看板區由製作A 維護。
> `source/HANDOFF.md` 是歷史檔，只讀不寫。

---

## 📋 任務看板（製作A 維護，反映最新狀態）

| 任務ID | 標題 | 負責 | 狀態 | 依賴 | 最後更新紀錄 |
|---|---|---|---|---|---|
| T-001 | 讀取並驗證 repo，回報架構 | 製作A | 完成 | — | H-002 |
| T-001b | Vercel / Firebase 用途確認（技術棧不符） | 人類 | 阻塞 | T-001 | H-002 |
| T-001c | 合併協作檔與既有 AGENTS.md，修正 source 殘字 | 製作A | 待審 | T-001 | H-003 |
| T-002 | 審查 native_ui.py 現有 Tk 介面，產出 design/tokens.md 與畫面規格 | 設計B | 待辦 | T-001c | H-003 |
| T-003 | 盤點介面文字與 DC 通知文案，改寫第一次使用教學 | 寫手C | 待辦 | T-001c | H-003 |
| T-004 | 更新過時測試契約，恢復可跑的回歸 | 製作A | 待辦（需人類同意跑測試） | T-001c | H-002 |

狀態：`待辦` / `進行中` / `待審` / `完成` / `阻塞`

---

## 🧾 紀錄格式（複製使用）

```markdown
### H-xxx ｜ YYYY-MM-DD HH:MM ｜ 寄件：[製作A|設計B|寫手C|人類] → 收件：[製作A|設計B|寫手C|人類]
- 類型：指派 / 狀態更新 / 交付 / 提問 / 回覆 / 阻塞 / 更正
- 任務：T-xxx
- 引用：H-xxx（回覆或更正時填）
- 內容：
  - …
- 改動檔案：
  - `path/to/file`
- 需要對方做什麼：
  - …
- 狀態：待辦 / 進行中 / 待審 / 完成 / 阻塞
```

規則提醒：
- 設計B、寫手C 的「收件」只能是 **製作A** 或 **人類**，不可互寄。
- ID 依序遞增，追加前先看最後一筆 ID。

---

## 📜 紀錄（只能往下追加）

### H-001 ｜ 2026-11-25 20:02 ｜ 寄件：人類 → 收件：製作A、設計B、寫手C
- 類型：指派
- 任務：T-001、T-002、T-003
- 內容：
  - 專案啟動。角色與規則見 `AGENTS.md`。
  - 製作A 先完成 T-001（讀取並驗證 repo，回報架構與設計），完成後才細化 T-002、T-003 的規格。
  - 設計B、寫手C 在 T-001 完成前，只需讀檔並確認理解規則，不需動工。
- 需要對方做什麼：
  - 製作A：開始 T-001，結果追加為 H-002。
  - 設計B、寫手C：各追加一筆「狀態更新」確認已讀規則。
- 狀態：完成

### H-002 ｜ 2026-11-25 20:20 ｜ 寄件：製作A → 收件：人類
- 類型：交付
- 任務：T-001
- 引用：H-001
- 內容：
  - Repo：eason66225/kuji-desk-v1.5.13，HEAD e5eac0a（2026-11-25 20:05，v1.5.34 來源）。
  - 性質：Windows 桌面工具（Python 3.13 + Tk + Playwright CDP + aiohttp），接管本人已登入的 Chrome 設定檔，監看新箱並接續網站排隊。不是網頁應用，沒有雲端後端。
  - 架構：desktop.py 入口 → manager.py（127.0.0.1:18766 認證本機 API、帳號與任務）→ native_ui.py（Tk 介面，UI 1.5.34 / 服務 1.5.30，屬刻意分離）→ notifications.py（獨立 Discord 程序）。web/、browser-box-scan/、*.bak 為保留的舊版。
  - 驗證結果：9 個主要 .py 語法檢查通過；SOURCE-SHA256.json 40 檔全部相符；根目錄 KujiDesk.exe 與 SHA256SUMS.txt 相符（v1.5.13 保存檔）；未發現 Webhook、金鑰或私鑰外洩；本機 API 限 127.0.0.1／localhost 的 Host 與 Origin。
  - 未執行：單元測試（既有規則寫明依使用者要求暫不跑，且部分測試契約已過時）。
  - 問題 1（重大）：技術棧與原協作檔的 Vercel + Firebase 不符，見 T-001b。
  - 問題 2（重大）：repo 已有根目錄 AGENTS.md、source/AGENTS.md、source/HANDOFF.md（Codex 過去擔任開發者的紀錄）。Codex 會自動讀 AGENTS.md，若不合併，它會以為自己仍是開發者。
  - 問題 3：source/AGENTS.md 第 42 行開頭有 PowerShell 換行殘字。
  - 問題 4：76 個測試函式存在，但部分反映舊瀏覽器架構，目前無法宣稱回歸通過。
  - 問題 5：五分頁入場、Cloudflare 實際觸發、他台電腦首次使用仍未驗證（AI_CONTEXT.md 已註明）。
- 改動檔案：
  - 無（本輪只讀，未改 repo）
- 需要對方做什麼：
  - 人類：決定 Vercel / Firebase 的用途（T-001b）。
  - 人類：同意後由製作A 執行 T-001c。
- 狀態：完成

### H-003 ｜ 2026-11-25 20:30 ｜ 寄件：製作A → 收件：人類、設計B、寫手C
- 類型：交付
- 任務：T-001c
- 引用：H-002
- 內容：
  - 人類已授權處理，執行 T-001c。
  - 根目錄 `AGENTS.md` 改寫為三方協作總則：原有 5 條專案維護規範**全數保留**於第 5 節，另補上角色、目錄所有權、Git 流程、溝通規則、Tk 設計與語氣規範。
  - 專案資訊欄填入實際技術棧（Python / Tk / Playwright CDP），`部署` 欄註明 Vercel / Firebase 未定，指向 T-001b。
  - 第 1 節加入對 Codex 的明確告知：其歷史開發角色已結束，本輪為設計B，不再修改 `source/`。
  - 設計B 的交付定義改為「Tk 介面規格文件」而非 HTML/CSS 成品，因介面是 Tkinter。
  - 修正 `source/AGENTS.md` 第 42 行開頭的 PowerShell 換行殘字（問題 3）；該行條文內容未改動。
  - 因 `source/AGENTS.md` 內容變更，已依既有規範重算 `SOURCE-SHA256.json`，40 檔全部重新核對相符。
  - 新增 `CLAUDE.md`、`GEMINI.md`、`KICKOFF.md`；`source/AGENTS.md`、`source/AI_CONTEXT.md`、`source/HANDOFF.md` 保留不動，作為技術與歷史參考。
  - 未改動任何 `.py`、未執行程式、未重啟服務、未操作瀏覽器或隊伍。`KujiDesk.exe` 與 `SHA256SUMS.txt` 未動。
- 改動檔案：
  - `AGENTS.md`（改寫，保留原內容於第 5 節）
  - `HANDOFF.md`（新增）
  - `CLAUDE.md`、`GEMINI.md`、`KICKOFF.md`（新增）
  - `source/AGENTS.md`（修正第 42 行殘字）
  - `SOURCE-SHA256.json`（重算 AGENTS.md 雜湊）
- 需要對方做什麼：
  - 人類：確認 T-001c，並回覆 T-001b 的 Vercel / Firebase 決定。
  - 設計B：可開始 T-002。先讀 `source/native_ui.py` 與 `source/AI_CONTEXT.md`，產出 `design/tokens.md`（配色／字級／間距／狀態）與 `design/screens/` 下的畫面規格。沿用既有深色 clam 主題，不得修改 `source/`。
  - 寫手C：可開始 T-003。盤點 `source/native_ui.py` 的介面字串與 `source/notifications.py` 的通知文案，產出 `content/ui-strings.md`；並就 `source/使用說明.md` 的第一次使用流程提出改寫版本放 `content/`，由製作A 整合。不得修改 `source/`。
- 狀態：待審
