# HANDOFF.md — 唯一溝通管道

> 開工前先讀 `AGENTS.md` 與本檔。
> **只能在檔案底部「紀錄」區追加**，不可刪改他人紀錄。看板區由製作A 維護。
> `source/HANDOFF.md` 是歷史檔，只讀不寫。

---

## 📋 任務看板（製作A 維護，反映最新狀態）

| 任務ID | 標題 | 負責 | 狀態 | 依賴 | 最後更新紀錄 |
|---|---|---|---|---|---|
| T-001 | 讀取並驗證 repo，回報架構 | 製作A | 完成 | — | H-002 |
| T-001b | Vercel / Firebase 用途確認 → 決定不採用 | 人類 | 完成 | T-001 | H-005 |
| T-001c | 合併協作檔與既有 AGENTS.md，修正 source 殘字 | 製作A | 完成 | T-001 | H-005 |
| T-002 | 審查 native_ui.py 現有 Tk 介面，產出 design/tokens.md 與畫面規格 | 設計B | 待審 | T-001c | H-009 |
| T-003 | 盤點介面文字與 DC 通知文案 | 寫手C | 完成 | T-001c | H-013 |
| T-003b | 改寫第一次使用教學（使用說明.md） | 寫手C | 完成 | T-003 | H-013 |
| T-006 | 套用 ui-strings.md 的建議到 source/，統一命名 | 製作A | 待審 | T-003 | H-014 |
| T-007 | 套用 design/T-002 的按鈕對比度修正 | 製作A | 待審 | T-002 | H-015 |
| T-004 | 跑實際測試並診斷 | 製作A | 待審（診斷完成，修復待決定） | T-006 | H-016 |
| T-004b | 修復 test_entry_tabs 的 CDP 替身 | 製作A | 待審（已完成，6/6 通過） | T-004 | H-017 |
| T-004d | 處理 6 項「測試目的已失效」的測試 | 製作A | 待辦（需人類決定去留） | T-004b | H-017 |
| T-010 | 移除 load_home 與 login_store 死程式碼 | 製作A | 待審 | T-004b | H-018 |
| T-004c | 釐清 3 項行為差異是測試過時或程式回歸 | 製作A | 待辦（需人類確認預期行為） | T-004 | H-016 |
| T-009 | 複核並調整綠／紅按鈕文字色 | 設計B | 完成 | T-007 | H-022 |
| T-013 | 套用 T-009 的停用配色到 native_ui.py | 製作A | 待審 | T-009 | H-022 |
| T-014 | 將 GitHub 來源同步回 work\\kuji-manager | 製作A | 完成 | T-011 | H-023 |
| T-015 | 建置 v1.5.38 EXE | 設計B | 待辦（阻塞已排除） | T-017 | H-028 |
| T-017 | 修正版本號寫死三處的根因 | 製作A | 待審 | T-015 | H-028 |
| T-016 | 將本機較新的 AI_CONTEXT.md、CODEX_PROGRESS.md 反向同步到 GitHub | 設計B | 完成 | T-014 | H-027 |
| T-008 | 紀錄 ID 改用角色前綴避免撞號 | 人類 | 待辦 | — | H-010 |
| T-004 | 更新過時測試契約，恢復可跑的回歸 | 製作A | 待辦（需人類同意跑測試） | T-001c | H-002 |
| T-005 | 併入 Ponytail 程式精簡原則為 AGENTS.md 第 9 節 | 製作A | 完成 | T-001c | H-005 |

| T-011 | 併入 Codex 的 v1.5.35～37，確立 GitHub 為唯一來源 | 製作A | 待審 | T-010 | H-019 |
| T-012 | 設計B 角色放寬為可受指派開發 | 製作A | 完成 | — | H-019 |

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

### H-004 ｜ 2026-11-25 20:50 ｜ 寄件：製作A → 收件：人類、設計B、寫手C
- 類型：交付
- 任務：T-005
- 引用：H-003
- 內容：
  - 依人類要求，將 Ponytail（https://github.com/dietrichgebert/ponytail ，MIT）併入 `AGENTS.md` 第 9 節「程式精簡原則」，**非整份覆蓋**，原有第 1–8 節全部保留。原第 9 節版本紀錄改為第 10 節。
  - 第 9 節為依本專案情境改寫的中文版，不是原文複製；已在節首標示來源與 MIT 授權。
  - 預設強度設為 ultra，人類可改。
  - 明確寫入優先順序：**第 9 節低於第 5 節**。與「不中斷監看或隊伍、不自動付款、不處理驗證碼、不繞過網站限制」衝突時以第 5 節為準。
  - 處理兩項與既有規範的衝突：
    1. Ponytail 要求為新邏輯加測試，但第 5 節規定執行回歸前須問人類 → 第 9.5 節寫明「可以寫測試並 commit，不可自行跑整套 unittest」。
    2. 「不為了幾行程式新增依賴」補上本專案理由：要打包單檔 EXE，新依賴會增加體積與 PyInstaller 風險。
  - 第 9.9 節將精簡原則轉化到各角色：製作A 全面適用；設計B 為「不過度設計」但不得省略狀態呈現與無障礙；寫手C 為「不寫超出需求的文案」但不得刪減安全提醒與「由本人處理」語意。
  - 未改動 `source/**` 任何檔案，`SOURCE-SHA256.json` 無須重算。未執行程式、未操作瀏覽器或隊伍。
  - 註：Ponytail README 的效能數據為作者自行回報，非獨立驗證，未寫入本專案文件。
- 改動檔案：
  - `AGENTS.md`（新增第 9 節，版本紀錄改為第 10 節）
  - `HANDOFF.md`（本紀錄）
- 需要對方做什麼：
  - 人類：確認第 9 節內容與 ultra 強度；並回覆 T-001b 的 Vercel / Firebase 決定。
  - 設計B、寫手C：開工前重讀 `AGENTS.md`，注意新增的第 9 節與第 9.9 節對你的適用方式。
- 狀態：待審

### H-005 ｜ 2026-11-25 21:08 ｜ 寄件：製作A → 收件：人類、設計B、寫手C
- 類型：狀態更新
- 任務：T-001b、T-001c、T-005
- 引用：H-002、H-003、H-004
- 內容：
  - 人類決定：**不採用 Vercel 與 Firebase**。本專案維持純本機桌面應用，發布走 GitHub Release。T-001b 結案。
  - `AGENTS.md` 第 0 節部署欄已定案，移除「用途未定」字樣，不再指向 T-001b。
  - 人類核准 T-001c 與 T-005，兩者結案。
  - `dev` 已合併進 `main`，B 與 C 可直接從 `main` 讀取新規則。
- 改動檔案：
  - `AGENTS.md`（部署欄定案、版本紀錄追加一列）
  - `HANDOFF.md`（本紀錄、看板狀態更新）
- 需要對方做什麼：
  - 設計B：開始 T-002。讀 `source/native_ui.py` 與 `source/AI_CONTEXT.md`，產出 `design/tokens.md` 與 `design/screens/` 畫面規格。沿用既有深色 clam 主題，不修改 `source/`。
  - 寫手C：開始 T-003。盤點 `source/native_ui.py` 介面字串與 `source/notifications.py` 通知文案，產出 `content/ui-strings.md`，並提出 `source/使用說明.md` 的改寫版放 `content/`。不修改 `source/`。
- 狀態：完成

### H-006 ｜ 2026-11-25 22:30 ｜ 寄件：寫手C → 收件：製作A
- 類型：交付
- 任務：T-003
- 內容：
  - 盤點 `native_ui.py` 與 `notifications.py` 的 200 條中文介面字串，產出 24 條建議改寫與 3 點整體觀察。
  - 三大發現：核心元件名稱不統一（總控／控制台／背景服務／本機服務混用）；自動化邊界用詞易誤導（搶箱、自動操作、通過入場限制）；開發者視角殘留（套用修正、API 更新籤數）。
  - 未產出：`使用說明.md` 的改寫版本。
  - 執行方式：由人類授權，製作A 透過電腦操作在 Gemini App 交派並取回產出。寫手C 本身未存取 repo，材料由製作A 從原始碼抽出後提供。
- 改動檔案：
  - `content/ui-strings.md`（新增）
- 狀態：待審

### H-007 ｜ 2026-11-25 22:35 ｜ 寄件：製作A → 收件：人類、寫手C
- 類型：回覆
- 任務：T-003
- 引用：H-006
- 內容：
  - 已審查寫手C 的交付。整體品質可用，採納多數建議，但有**兩處誤判必須更正**：
    1. **`suto 1 ban kuji` 不是拼字錯誤。** 已核對 `README.md`、`source/README.md` 與 `native_ui.py:203`，這是專案既有的副標與標頭文字，屬刻意命名，不改。
    2. **標題列沒有「孤立的 v」。** 原始碼為 `'suto 1 ban kuji · 獨立視窗 v'+UI_VERSION`（native_ui.py:113），實際顯示為「獨立視窗 v1.5.34」。寫手C 只拿到抽出的字串、沒有上下文，因此誤判；此為製作A 提供材料的疏失，非寫手C 的問題。
  - 確認正確且優先採納：「每 3 分鐘自動以 API 更新全部籤數」必須改掉。依 `AGENTS.md` 第 5 節，查籤實際是 HTTP GET + HTML 解析，不得宣稱官方 JSON 庫存介面，這條是規範衝突而不只是文案問題。
  - 「搶箱」「自動操作」「通過入場限制」的收斂建議符合第 5 節對自動化邊界的要求，採納。
  - **暫不套用到 `source/`**：命名統一（總控／控制台 → 背景服務）牽涉 `使用說明.md`、`CHANGELOG.md` 與既有 HANDOFF 的既定用語，屬產品層級決定，須人類拍板。已開 T-006 追蹤。
  - 本輪未改動任何 `.py`，未重啟服務，未操作瀏覽器或隊伍。
- 改動檔案：
  - `content/ui-strings.md`（加入交付者與狀態標頭）
  - `HANDOFF.md`（本紀錄、看板更新）
- 需要對方做什麼：
  - 人類：決定是否採用「背景服務／主視窗／獨立 Chrome 視窗」的統一命名（T-006）。
  - 寫手C：執行 T-003b，改寫 `使用說明.md` 的第一次使用流程。
### H-008 ｜ 2026-11-25 21:49 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-002
- 引用：H-005
- 內容：
  - 從 main 開立 design/T-002，以 v1.5.34 Tk 介面為規格基線，盤點元件、版面與狀態。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 狀態：進行中

### H-009 ｜ 2026-11-25 21:52 ｜ 寄件：設計B → 收件：製作A
- 類型：交付
- 任務：T-002
- 引用：H-005、H-008
- 內容：
  - 以 UI v1.5.34 與相容服務 v1.5.30 做靜態盤點。規格涵蓋深色 clam 樣式、主視窗、三張帳號卡、紀錄與各對話框。
  - 沿用現有元件與色盤。提出綠／紅按鈕的高對比文字、鍵盤焦點、狀態空值及舊資料提示，另附最小視窗與 DPI 驗收情境。
  - 本輪只做原始碼與 Markdown 靜態核對。Windows 實際排版、DPI 與鍵盤走查待整合後驗證；未執行程式、未操作瀏覽器或隊伍。
- 改動檔案：
  - design/tokens.md
  - design/screens/dashboard.md
  - design/screens/logs.md
  - design/screens/dialogs.md
  - HANDOFF.md（追加 T-002 紀錄）
- 需要對方做什麼：
  - 製作A：審查 design/T-002 的 PR，確認是否採用標為提案的調整，尤其是輪詢失敗與紀錄讀檔失敗可用的狀態訊號。
  - 製作A：整合時安排佔位文字，優先確認驗證、隊伍影響與結果未明的提示語意。
- 狀態：待審

### H-010 ｜ 2026-11-25 22:45 ｜ 寄件：製作A → 收件：人類、設計B、寫手C
- 類型：更正
- 任務：T-002、T-003
- 引用：H-006、H-007、H-008、H-009
- 內容：
  - **紀錄 ID 撞號。** 設計B 於 `design/T-002` 分支追加的兩筆原本編為 H-006、H-007，與寫手C 交付時製作A 在 `main` 寫入的 H-006、H-007 重複。已將設計B 的兩筆改編為 **H-008、H-009**，內容未更動，其內部引用一併更新。
  - 原因：兩個分支各自從同一個 ID 往下編。`AGENTS.md` 第 6 節的「ID 依序遞增」在平行分支下不成立。
  - 預防措施（待人類確認）：改為帶角色前綴的 ID，例如 `HA-001`、`HB-001`、`HC-001`，各自獨立遞增，合併時不會相撞。開 T-008 追蹤。
  - 已將 `design/T-002` 合併進 `dev`，HANDOFF.md 的衝突以保留雙方全部紀錄的方式解決，沒有刪除任何一筆。
- 改動檔案：
  - `HANDOFF.md`（重新編號、合併看板）
- 需要對方做什麼：
  - 人類：確認是否改用角色前綴的紀錄 ID（T-008）。
- 狀態：完成

### H-011 ｜ 2026-11-25 23:55 ｜ 寄件：寫手C → 收件：製作A
- 類型：狀態更新
- 任務：T-003b
- 引用：H-007、H-010
- 內容：
  - 已確認 `C:\Users\eason\Desktop\kuji-desk\HANDOFF.md` 任務看板上的 T-003b，並核對 `source/使用說明.md`、`source/native_ui.py`、`source/AI_CONTEXT.md` 與 `content/ui-strings.md`。
  - 開始撰寫第一次使用教學改寫版至 `content/使用說明.md`。
- 改動檔案：
  - `HANDOFF.md`（追加本紀錄）
- 狀態：進行中

### H-012 ｜ 2026-11-25 23:56 ｜ 寄件：寫手C → 收件：製作A
- 類型：交付
- 任務：T-003b
- 引用：H-007、H-011
- 內容：
  - 依 `source/使用說明.md`、`source/native_ui.py`、`source/AI_CONTEXT.md` 與 `content/ui-strings.md`，完成第一次使用教學改寫提案 `content/使用說明.md`。
  - 改寫重點：補上「使用前先知道」邊界清單（登入、Cloudflare 驗證、抽籤／付款、退出隊伍皆由本人處理）；把第一次啟動與 Chrome 遠端偵錯／設定檔綁定拆為 5 步驟並補充常見狀況排除；以「你」稱呼使用者，保留目前 v1.5.34 實際按鈕與選項名稱以免操作對不上，同時註明每 3 分鐘自動更新實際為頁內 HTML 解析而非官方 JSON 庫存 API。
  - 誠實說明與風險提醒：本輪僅進行靜態檔案閱讀與文案撰寫，**跳過**實機操作、EXE 執行與任何程式／瀏覽器測試；**未驗證**改寫文字是否已與 T-006（若採用命名統一）對齊，整合至 `source/使用說明.md` 時需依 T-006 人類決議同步調整對應按鈕名稱（如「控制台／背景服務」、「API 更新」）。未修改 `source/**` 與 `design/**`，未執行任何 git 指令。
- 改動檔案：
  - `content/使用說明.md`（新增）
  - `HANDOFF.md`（追加 H-011、H-012）
- 需要對方做什麼：
  - 製作A：審查 `content/使用說明.md`，並在 T-006 定案後一併決定整合進 `source/使用說明.md` 的版本與時機（若需同步更新 `SOURCE-SHA256.json`，由製作A 處理）。
- 狀態：待審

### H-013 ｜ 2026-11-26 00:05 ｜ 寄件：製作A → 收件：人類、寫手C
- 類型：回覆
- 任務：T-003、T-003b
- 引用：H-012
- 內容：
  - 已審查 `content/使用說明.md`（整合進 repo 時更名為 `content/使用說明-改寫版.md`，避免與 `source/使用說明.md` 混淆）。**通過，無須修改。**
  - 逐項查核寫手C 新增的三個具體數字，全部與原始碼相符：
    1. 「連續 1 小時無箱自動停止」→ `manager.py:968-971`，`time.monotonic() - empty_since >= 3600`。
    2. 「Runtime 存於 %LOCALAPPDATA%/KujiDesk，可用 KUJI_RUNTIME 指定」→ `manager.py:27-29`、`desktop.py:13-15`。
    3. 「連線最長等候 60 秒」→ `manager.py:356`，`connect_over_cdp('chrome', timeout=60000)`。
  - 另核對五分頁機制、Cloudflare 兩項預設值（`cloudflare_enabled` true、`cloudflare_popup` false）均與 `AGENTS.md`、`AI_CONTEXT.md` 一致。
  - 與 H-007 的差異值得記錄：本輪寫手C 直接讀取 `source/` 原始檔，因此事實正確；上一輪（T-003）只拿到製作A 抽出的字串、缺乏上下文，才產生兩處誤判。**結論：給 C 檔案讀取權限確實改善了產出品質。**
  - 採納其保留現版按鈕名稱的判斷：在 T-006 命名方案定案前，教學若先改名詞會與實際介面對不上。
  - T-003、T-003b 結案。本輪未改動 `source/**`，未執行程式、未操作瀏覽器或隊伍。
- 改動檔案：
  - `content/使用說明-改寫版.md`（新增）
  - `HANDOFF.md`（本紀錄、看板更新）
- 需要對方做什麼：
  - 人類：T-006（命名統一）仍待決定；定案後製作A 才會把 ui-strings.md 與本教學一併整合進 `source/`，並重算 `SOURCE-SHA256.json`。
- 狀態：完成

### H-014 ｜ 2026-11-26 02:55 ｜ 寄件：製作A → 收件：人類、設計B、寫手C
- 類型：交付
- 任務：T-006
- 引用：H-007、H-013
- 內容：
  - 人類核准命名統一。已套用：常駐服務一律稱「**背景服務**」，受控 Chrome 稱「**獨立視窗**」，程式本體稱「**Kuji Desk／主視窗**」。
  - 改動統計：`manager.py` 26 處、`native_ui.py` 23 處、`notifications.py` 11 處。舊詞（總控／控制台／本機服務／專用視窗／搶箱／以 API）在 `source/**` 已全數歸零。
  - 一併採納 ui-strings.md 的語意修正：「每 3 分鐘自動以 API 更新全部籤數」改為「自動重新讀取全部籤數」；「搶箱與排隊執行紀錄」改為「監看與排隊執行紀錄」；「自動操作已暫停」改為「自動監看已暫停」；「通過入場限制」改為「網站開放進入…」；「輪到抽籤」改為「輪到你進入頁面」。
  - **未採納**（H-007 已查證為誤判）：`suto 1 ban kuji` 維持不動；標題列的 `v` 來自 `'…獨立視窗 v'+UI_VERSION`，非贅字。
  - **發現並處理一個會靜默失效的耦合**：`notifications.py` 的 `CLOUDFLARE_NOTICE` 會與 `manager.py:471` 設定的 `note` 做相等比對（`cloudflare_event_key`）。只改一邊會讓 Cloudflare 通知完全不發出。兩處已同步修改並驗證字串完全一致，兩邊各加上 `# shortcut:` 註記說明耦合關係與未來應抽成共用常數。
  - **升級後的已知影響**：舊的執行紀錄事件仍存著舊字串，`cloudflare_event_key` 的 `detected_at` 會退回 `'current'`，升級後若當下正處於 Cloudflare 驗證狀態，最多會重複發出一則通知。不影響功能。
  - 事前查核：確認全專案僅有三處中文字串被用於相等比對——網站自身的日文按鈕文字（`details.py:35`、`manager.py:1021`）與紀錄篩選的 `'全部紀錄'`（`native_ui.py:806`），皆未更動。
  - `source/使用說明.md` 已以寫手C 的 T-003b 改寫版整合並同步名詞；C 的原始提案保留於 `content/使用說明-改寫版.md`。舊版六個章節與全部警告事項均已涵蓋。
  - 依規範重算 `SOURCE-SHA256.json`，40 檔核對相符。四個 `.py`／`.md` 以 `py_compile` 驗證通過。
  - **製作A 自身疏失並已修正**：首次改寫時以 Python 文字模式寫檔，把四個檔案的 CRLF 全轉成 LF，造成 diff 虛增至 5700 行。已還原為 CRLF，實際改動為 147 增 95 刪。
  - **未執行**：單元測試（依 AGENTS.md 第 5 節須人類同意）、實機操作、EXE 重新打包。未重啟任何服務，未操作瀏覽器或隊伍。
- 改動檔案：
  - `source/manager.py`、`source/native_ui.py`、`source/notifications.py`、`source/使用說明.md`
  - `SOURCE-SHA256.json`（重算四個檔案的雜湊）
  - `HANDOFF.md`（本紀錄、看板更新）
- 需要對方做什麼：
  - 人類：此版尚未在 Windows 實機驗證。要套用請先等目前隊伍結束，再重新打包並「重新啟動服務」。
  - 人類：是否要製作A 執行 T-004（更新過時測試契約並跑回歸）？
  - 設計B：T-007 的對比度提案（綠／紅按鈕改深色文字）尚未套用，與本輪文案改動互不衝突。
- 狀態：待審

### H-015 ｜ 2026-11-26 05:15 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：交付
- 任務：T-007
- 引用：H-009、H-014
- 內容：
  - 採納設計B 的對比度提案。新增常數 `ON_ACCENT='#10151c'`，綠／紅底按鈕的文字由白字改為深色，對比從 3.25:1／3.82:1 提升到約 5.65:1／4.80:1，通過 WCAG AA 的 4.5:1。共 7 處。
  - **套用過程中發現並修正自己的兩個錯誤**：
    1. 首次替換時誤將「🔔 DC Webhook 設定」按鈕一併改掉。該鈕底色是深藍 `#2b3d52`，改成深字幾乎看不見。已還原為白字。設計B 的提案只針對綠／紅底，範圍是我自己擴大的。
    2. T-006 漏掉 `native_ui.py:551` 的狀態列字串「舊版服務正在執行…套用修正」。已補為「舊版背景服務正在執行，請按右上角「重新啟動服務」套用新版。」
  - **T-006 打破了一個測試**：`test_notifications.py:53` 斷言通知標題含「已通過入場限制」，而該標題已改為「✅ 可進入商品／籤箱頁」。斷言已同步更新。這是刻意改名造成的契約變更，不是程式缺陷。
  - 依規範重算 `SOURCE-SHA256.json`，40 檔核對相符；`py_compile` 通過。
  - **未執行**：單元測試、實機驗證、重新打包。未重啟服務，未操作瀏覽器或隊伍。顏色變更只能靠實機目視確認。
- 改動檔案：
  - `source/native_ui.py`、`source/test_notifications.py`、`SOURCE-SHA256.json`、`HANDOFF.md`
- 需要對方做什麼：
  - 人類：實機開啟後目視確認綠／紅按鈕的深色文字是否清楚。
  - 人類：是否同意執行 T-004（跑回歸測試）。上述測試斷言的修正顯示，現有測試確實與現版契約脫節，但在你同意前不會執行。
- 狀態：待審

### H-016 ｜ 2026-11-26 05:30 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：交付
- 任務：T-004、T-009
- 引用：H-015
- 內容：
  - 人類同意執行測試。**76 個測試全部跑過一遍，60 通過、16 有問題。**這是本專案近期第一次取得完整的測試基線。
  - 執行環境：Linux 容器（非 Windows 實機），Python 3.13，已安裝 aiohttp 3.14.5。未在使用者電腦上執行任何東西，未碰瀏覽器或隊伍。

  **分檔結果**

  | 檔案 | 通過／總數 | 狀況 |
  |---|---|---|
  | `test_notifications.py` | 8／8 | 全通過（含 T-006 改名後同步的斷言） |
  | `test_manager.py` | 43／53 | 3 失敗、7 錯誤 |
  | `test_entry_tabs.py` | 0／6 | 5 失敗、1 永久卡住 |
  | `test_service_runtime.py` | 4／5 | 1 錯誤 |
  | `test_login_store.py` | 1／4 | 3 錯誤 |

  **分成三類，處理方式不同**

  1. **環境限制，非缺陷（4 項）**：`test_login_store` 的 3 項需要 Windows 帳號加密（DPAPI），`test_service_runtime` 的 1 項需要 tkinter。這兩項在 Linux 容器內無法執行，必須在 Windows 實機跑。不應視為失敗。
  2. **測試契約過時（9 項）**：`test_entry_tabs` 全 6 項停留在舊架構——測試只 mock 了 `context.new_page()`，但 `manager.py:536` 起的 `new_entry_page()` 已改為透過 CDP `new_cdp_session` + `Runtime.evaluate` 的 `window.open` 開分頁。另 `test_manager` 有 4 項缺 playwright mock、1 項呼叫已不存在的 `Account.schedule_soldout_resume`。這些是程式演進、測試沒跟上，修 mock 即可。
     - `test_cancellation_closes_extras_and_keeps_original` 會**永久卡住**（`test_entry_tabs.py:32` 的 `await asyncio.Event().wait()` 等不到取消），直接 `unittest discover` 會整組掛住。這是目前沒人跑測試的實際原因之一。
  3. **行為差異，需人類確認（3 項）**：這三項**不能逕自改斷言讓它變綠**，因為無法單憑程式碼判斷是測試過時還是真的回歸：
     - `test_official_page_reload_retries_observation_without_submission`：期望 `phase=='waiting'`，實際 `'submitting'`。**安全關鍵部分仍正確**——同一測試前一行斷言重試次數為 2 已通過，代表官方頁重新載入後程式確實是重新觀察而非重送排隊。差異只在狀態標籤。
     - `test_login_only_reuses_window_when_control_resumes`：期望 HTTP 200，實際 400。
     - `test_gate_without_pid_adopts_product_after_entry`：期望採用 `sap_0000008550`，實際 `None`。
  - **未做**：沒有修改任何測試斷言去迎合現行行為。依 AGENTS.md 第 9.8 節，不把未驗證寫成已驗證，也不以「讓測試變綠」為目標。
  - 另依人類指示，綠／紅按鈕文字色的後續調整改由**設計B** 負責（T-009）。H-015 已套用的 `ON_ACCENT='#10151c'` 為暫行值，請設計B 複核或提出替代。實機目視仍須人類確認。
- 改動檔案：
  - `HANDOFF.md`（本紀錄、看板更新）。本輪未改動任何程式碼或測試檔。
- 需要對方做什麼：
  - 人類：第 3 類的三項，請確認預期行為應為何（或授權我逐項深入追查程式碼判定）。
  - 人類：是否要我執行 T-004b，修復第 2 類的 9 項過時 mock。
  - 人類：環境限制的 4 項需在 Windows 實機執行才有意義。
  - 設計B：T-009，複核 `ON_ACCENT='#10151c'` 於 `#38a169` 綠底與 `#e05252` 紅底上的表現，必要時提替代值。只改 `/design`，不要改 `source/`。
- 狀態：待審

### H-017 ｜ 2026-11-26 05:45 ｜ 寄件：製作A → 收件：人類
- 類型：交付
- 任務：T-004b
- 引用：H-016
- 內容：
  - **先更正 H-016 的數字**：該筆寫「60 通過、16 問題」為誤。重新核對後，修復前實際為 **58 通過、18 問題**（我把類別數加錯，且其中 2 項「失敗」是我執行時用錯測試類別名稱所致，那 2 項本來就是好的）。
  - **已修復 `test_entry_tabs`，6/6 全通過。** 最大的收穫是整組測試現在跑得完——先前 `test_cancellation_closes_extras_and_keeps_original` 會永久卡住，導致任何人執行完整回歸都會掛住，這是這套測試長期沒人跑的直接原因。
  - 修法：依 v1.5.26 的實際架構重寫替身。新增 `FakeCDPSession` 模擬 `Target.getTargetInfo` 與 `Runtime.evaluate`，並以 `spawn()` 模擬 `window.open` 產生分頁。原本的替身只提供 `context.new_page`，而 AGENTS.md v1.5.24／v1.5.26 已明文禁止該做法。**所有測試的驗證目的與斷言一律保留**，僅把「開分頁數」的斷言從 `new_page.await_count` 改為實際開出的分頁數。
  - 目前基線：**76 項中 62 通過、14 有問題**（3 行為差異 + 11 錯誤）。

  **調查中發現三處疑似死程式碼，這是比測試本身更重要的發現**

  1. `manager.py:387` 的 `load_home()` **定義後無任何呼叫**，全專案搜尋只有定義本身。
  2. `manager.py:47` `import login_store`，但 `login_store` 的四個函式（`protect`／`site_cookies`／`save`／`restore`）**在產品程式中完全沒有被使用**。
  3. `context.cookies()` 在 `manager.py` 中**沒有任何呼叫**。
  - 三者互相印證：登入快照（把 cookie 加密存檔）這項功能已不在現行流程中。這也解釋了為何 `test_login_store` 的 3 項需要 Windows DPAPI——它們測的是一個已經沒有被接上的模組。我先前把這 3 項歸為「環境限制」並不完整。

  **剩下 14 項的分類與建議（均未修改，等你決定）**

  | 測試 | 狀況 | 我的建議 |
  |---|---|---|
  | `test_open_home_timeout_keeps_browser` | 驗證 `load_home` 的逾時處理，但 `open()` 已不呼叫它 | 連同死程式碼一起決定去留 |
  | `test_open_home_aborted_preserves_window_in_both_modes` | 同上（2 個子測試） | 同上 |
  | `test_open_cookie_context_closed_can_reopen` | 驗證 cookie 還原失敗的處理，但已無 `cookies()` 呼叫 | 同上 |
  | `test_open_uses_visible_chrome_and_separate_account_profile` | 驗證 v1.5.23 的 `launch_persistent_context` 與獨立設定檔，v1.5.24 起已改 CDP 接管 | 改寫為驗證 `connect_over_cdp('chrome', timeout=60000)` |
  | `test_query_inventory_api_parses_html_and_sets_inventory` | 使用 `FakeSession`（aiohttp），v1.5.22 起已改頁內 fetch | 改寫為以 `page.evaluate` 為基礎 |
  | `test_soldout_resume_runs_once_and_respects_switch` | 呼叫已不存在的 `Account.schedule_soldout_resume` | 改寫為對應現行的 `resume_after_soldout` |
  | `test_login_store`（3 項） | 測試未被接上的模組，且需 Windows DPAPI | 視 login_store 去留而定 |
  | `test_service_runtime`（1 項） | 需 tkinter，Linux 容器無法安裝 | 保留，在 Windows 實機跑 |
  | 行為差異 3 項 | 見 H-016 | 仍待確認預期行為 |
- 改動檔案：
  - `source/test_entry_tabs.py`（重寫替身、1 處斷言）
  - `SOURCE-SHA256.json`、`HANDOFF.md`
- 需要對方做什麼：
  - 人類：`load_home` 與 `login_store` 是真的要廢棄，還是功能遺漏？這會決定 6 項測試與可能的程式碼清理（T-010）。
  - 人類：是否授權我改寫上表中 3 項「架構已變」的測試（T-004d）。
- 狀態：待審

### H-018 ｜ 2026-11-26 05:45 ｜ 寄件：製作A → 收件：人類
- 類型：交付
- 任務：T-010
- 引用：H-017
- 內容：
  - 人類確認「用不到這些功能了」，並核准執行刪除。
  - **已移除登入快照**：`source/login_store.py`（65 行）、`source/test_login_store.py`（43 行／4 測試）、`manager.py` 的 `import login_store`、`test_manager.test_open_cookie_context_closed_can_reopen`。理由：改為 CDP 接管既有 Chrome 後，登入狀態由使用者自己的 Chrome 保存，不需另存加密副本。
  - **已移除自動導向首頁**：`manager.Account.load_home()`（19 行）、`test_open_home_timeout_keeps_browser`、`test_open_home_aborted_preserves_window_in_both_modes`。理由：接管既有分頁後不應擅自導覽，避免洗掉使用者正在排隊的頁面。
  - 刪除前查核：`build_exe.py`、`desktop.py`、`service_runtime.py`、`native_ui.py` 皆未引用；全專案無任何呼叫點。刪除後再次全文搜尋 `login_store`／`load_home`，結果為零。
  - `SOURCE-SHA256.json` 移除兩個檔案條目並重算，由 40 檔變 **38 檔**，核對相符，CRLF 格式維持。
  - 兩份 `AGENTS.md` 均補上版本紀錄，載明這是刻意廢棄而非遺漏，並註明可從 `becf7a9` 之前的 commit 取回。
  - **測試基線：69 項中 62 通過、7 有問題**（刪除前為 76 項中 62 通過、14 問題）。通過數不變，代表刪掉的全是已失效的測試，沒有損及任何有效覆蓋。
  - 未重新打包 EXE，未重啟服務，未操作瀏覽器或隊伍。
- 改動檔案：
  - 刪除：`source/login_store.py`、`source/test_login_store.py`
  - 修改：`source/manager.py`、`source/test_manager.py`、`source/AGENTS.md`、`AGENTS.md`、`SOURCE-SHA256.json`、`HANDOFF.md`
- 需要對方做什麼：
  - 人類：剩餘 7 項的處理方式，見下一則說明（3 項行為差異、3 項架構已變、1 項需 Windows 實機）。
- 狀態：待審

### H-019 ｜ 2026-11-26 10:30 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：交付
- 任務：T-011、T-012
- 引用：H-018
- 內容：
  - **發現兩邊分岔。** 人類索取最新 EXE 時查出：設計B（Codex）在 `Documents\Codex\PrintLab\work\kuji-manager` 持續開發到 v1.5.37 並已建置 v1.5.35／36／37，但這些改動從未進入 GitHub。Codex 自己的 `CODEX_PROGRESS.md` 也寫明「GitHub 仍 34」。製作A 今天的全部工作（T-006／T-007／T-010／T-004b）則只做在 GitHub 這份 v1.5.34 快照上。
  - 人類裁示：**以 GitHub 為唯一來源**，且由製作A 直接推送合併結果，不再請 Codex 重做。
  - **以 `e5eac0a` 為共同起點做三方合併，五個程式檔與 `source/AGENTS.md` 全部零衝突**，兩邊改動不重疊：
    | 檔案 | 製作A | 設計B | 衝突 |
    |---|---|---|---|
    | `manager.py` | 70 行 | 186 行 | 0 |
    | `native_ui.py` | 63 行 | 4 行 | 0 |
    | `notifications.py` | 22 行 | 19 行 | 0 |
    | `details.py`／`build_exe.py` | 0 行 | 6 行 | 0 |
  - 合併後逐項驗證：`py_compile` 通過；版本正確保留設計B 的 **1.5.37**；Cloudflare 耦合字串兩檔仍完全一致；命名統一全數保留（舊詞歸零）；`login_store`／`load_home` 維持刪除（設計B 那份仍留著，合併後正確移除）。
  - **測試從 7 項問題降為 6 項**：`test_official_page_reload_retries_observation_without_submission` 已自行通過，代表設計B 在 v1.5.35～37 期間修好了該狀態標籤問題。目前 **69 項中 63 通過**。
  - 另取入設計B 單方面更新的 `README.md`，並新增其建立的 `ARCHITECTURE.md`（repo 原本沒有）。`KujiDesk.spec` 為 PyInstaller 產生物且 `.gitignore` 已排除，不納入。
  - 版本號衝突處理：製作A 原將死碼移除標為 v1.5.35，與設計B 已使用的 v1.5.35 相撞，已改標為 **v1.5.38**。
  - `SOURCE-SHA256.json` 由 38 檔增為 **39 檔**（新增 ARCHITECTURE.md），全部核對相符。
  - **T-012 角色放寬**：人類核准設計B 不限於 UI，製作A 得視需要指派開發任務。`AGENTS.md` 第 1、2、4 節已更新——受指派開發時適用與製作A 相同的規範，工作分支改用 `feature/<任務ID>`，且**指派紀錄必須明寫「授權修改 source/」與檔案範圍**，未寫明者仍只能動 `/design`。合併到 `main` 的權限仍僅限製作A。
  - **未執行**：未重新打包 EXE（PyInstaller 需在 Windows 執行，製作A 在 Linux 容器無法跨平台建置），未重啟服務，未操作瀏覽器或隊伍。
- 改動檔案：
  - `source/manager.py`、`source/native_ui.py`、`source/notifications.py`、`source/details.py`、`source/build_exe.py`、`source/AGENTS.md`、`source/README.md`
  - 新增 `source/ARCHITECTURE.md`
  - `AGENTS.md`、`SOURCE-SHA256.json`、`HANDOFF.md`
- 需要對方做什麼：
  - 人類：要產生含今日改動的 EXE，需在 Windows 執行 `python build_exe.py --share`。現行 v1.5.37 EXE 不含今日改動。
  - 人類：`work\kuji-manager` 之後請改為從 GitHub 更新，避免再次分岔。
### H-020 ｜ 2026-11-26 10:25 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-009
- 引用：H-009、H-015、H-016
- 內容：
  - 從 main 開立 design/T-009，靜態複核綠／紅按鈕的文字對比、互動狀態與適用範圍。
- 改動檔案：
  - `HANDOFF.md`（追加本紀錄）
- 狀態：進行中

### H-021 ｜ 2026-11-26 10:26 ｜ 寄件：設計B → 收件：製作A
- 類型：交付
- 任務：T-009
- 引用：H-009、H-015、H-016、H-020
- 內容：
  - 維持 `ON_ACCENT='#10151c'`。綠／紅底的 10 pt 粗體文字對比分別為 5.65:1／4.80:1，均達 4.5:1。Hover 沿用同一色對。深藍底 DC Webhook 快捷鈕維持白字，對比 11.10:1。設定對話框的綠底「儲存設定」適用 ON_ACCENT。
  - 帳號卡監看鈕的現行停用灰字配綠／紅底僅 1.40:1／1.19:1。提案採中性底 `#283648`、字 `#A0AEC0`（5.44:1），並以原生停用狀態及一般游標呈現。
  - 本輪以原始碼及 sRGB 色值靜態核對。Windows 的字型平滑、DPI 及 Tk 狀態切換待目視確認。
- 改動檔案：
  - `design/tokens.md`（T-009 規格）
  - `HANDOFF.md`（追加 H-020、H-021）
- 需要對方做什麼：
  - 審查規格、整合帳號卡監看鈕的停用配色與恢復路徑，並在 Windows 100%／150% 縮放驗收紅底文字、hover、停用與恢復，以及頂欄 DC Webhook 白字。
- 狀態：待審

### H-022 ｜ 2026-11-26 11:05 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：回覆
- 任務：T-009、T-013
- 引用：H-021
- 內容：
  - 已審查設計B 的 T-009 規格並**全數採納**，`design/T-009` 已合併。
  - 確認維持 `ON_ACCENT='#10151c'`：綠底 5.65:1、紅底 4.80:1，均過 WCAG AA 4.5:1。深藍 DC Webhook 鈕維持白字 11.10:1。規格也補上了我先前沒寫清楚的適用清單（七個實體按鈕），避免再發生我上次那種誤套。
  - **採納其發現的停用狀態問題**：監看鈕停用時沿用綠／紅底配共用灰字 `#6b7786`，對比只有 **1.40:1／1.19:1**，幾乎讀不到。這比正常狀態原本的問題更嚴重，是我和設計B 先前都漏掉的。
  - 已套用至 `native_ui.py`：新增 `DISABLED_BG='#283648'`／`DISABLED_FG='#A0AEC0'`（5.44:1），並新增共用函式 `style_toggle()` 統一處理監看鈕的啟用／停用外觀——啟用時綠或紅底配 `ON_ACCENT` 與手形游標，停用時中性底配 `#A0AEC0` 與一般箭頭。
  - 依規格要求，**缺少帳號資料的提前返回路徑也一併覆寫**（`native_ui.py:586`），避免留住前次的綠／紅底。新增 `self.monitor_color` 記住每張卡當下該用的顏色，恢復啟用時還原正確色對。
  - `SOURCE-SHA256.json` 重算，39 檔相符；`py_compile` 通過；測試維持 69 項中 63 通過，未因此改動而退步。
  - **未驗證**：顏色與游標變化只能在 Windows 實機目視確認。設計B 已明確要求在 100%／150% 縮放下核對紅底文字、滑入滑出、停用後滑入與恢復，以及頂欄 DC Webhook 仍為深藍底白字。這些我無法代做。
- 改動檔案：
  - `source/native_ui.py`、`SOURCE-SHA256.json`、`HANDOFF.md`、`design/tokens.md`（來自設計B）
- 需要對方做什麼：
  - 人類：在 Windows 實機目視驗收上述四項。
- 狀態：待審

### H-023 ｜ 2026-11-26 11:10 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：交付
- 任務：T-014
- 引用：H-019
- 內容：
  - 人類核准，已透過檔案橋接把 GitHub `source/` 的 13 個檔案寫回 `Documents\Codex\PrintLab\work\kuji-manager`，兩邊來源自此一致。該機未安裝 git，故以直接寫檔取代 `git pull`。
  - 寫入：`manager.py`、`native_ui.py`、`notifications.py`、`details.py`、`build_exe.py`、四個 `test_*.py`、`AGENTS.md`、`README.md`、`ARCHITECTURE.md`、`使用說明.md`。
  - **刻意未覆蓋 `AI_CONTEXT.md` 與 `CODEX_PROGRESS.md`**：設計B 今早（10:06）才更新過，本機版本比 repo 新。覆蓋會抹掉它最新的進度與驗證紀錄。這兩份應改為從本機往 GitHub 更新，開 T-016 追蹤。
  - **`login_store.py` 與 `test_login_store.py` 仍留在該目錄**：本 session 沒有在該機刪檔的能力。兩者已無任何 import，PyInstaller 以進入點追蹤相依，不會打包進 EXE，因此留著無害。人類可自行刪除。
  - 未觸碰：`KujiDesk.exe`、`KujiDesk.runtime.json`、Runtime 目錄、`.bak` 備份、`web/`、`browser-box-scan/`、PrintLab 父倉庫的任何其他內容。未執行任何程式，未重啟服務，未操作瀏覽器或隊伍。
  - **尚未建置**：PyInstaller 需在 Windows 執行，製作A 在 Linux 容器無法跨平台產生 Windows 執行檔；且終端機於本 session 為唯讀點擊權限，無法代為輸入指令。建置指令須由人類執行（T-015）。
- 改動檔案：
  - 使用者電腦 `work\kuji-manager` 的 13 個檔案（repo 本身未變動）
  - `HANDOFF.md`（本紀錄、看板更新）
- 需要對方做什麼：
  - 人類：執行建置，產生含今日改動的 EXE。建置前請確認目前沒有正在進行的監看或隊伍。
  - 人類：建置後新 EXE 會輸出為版本化資料夾，不會覆蓋執行中的舊檔。
- 狀態：完成

### H-024 ｜ 2026-11-26 11:20 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：指派
- 任務：T-015、T-016
- 引用：H-023
- 內容：
  - **版本升至 1.5.38**（`VERSION` 與 `UI_VERSION` 皆升）。原因：今日改動後版本號仍是 1.5.37，與設計B 昨晚的建置同號，建置會覆蓋 `KujiDesk-share-v1.5.37` 且日後無法分辨。`manager.py` 本身有變動（note 文字、死碼移除），故服務版本一併升，GUI 會提示需重新啟動服務；此為正確行為。
  - 1.5.38 內容：命名統一（背景服務／獨立視窗／主視窗）、按鈕對比度 `ON_ACCENT`、監看鈕停用配色、移除 `login_store` 與 `load_home`、修復 `test_entry_tabs`、併入設計B 的 v1.5.35～37。
  - 人類嘗試建置失敗：`ModuleNotFoundError: No module named 'aiohttp'`，原因是用了系統 Python 而非專案 venv（`PrintLab\Runtime\kuji-manager\venv`）。已從 `build-latest.log` 與 `開啟桌面總控.bat` 確認正確路徑。查核硬碟後確認**未產生任何新建置**，`KujiDesk-share-v1.5.37` 的 EXE 時間仍停在昨晚 23:56。
  - **委託設計B 執行建置（T-015）**。理由：製作A 在 Linux 容器無法產生 Windows 執行檔，且本 session 對終端機僅有唯讀點擊權限，無法輸入指令；設計B 在該機有可執行環境，v1.5.35～37 即為其建置。
  - **授權範圍（依 AGENTS.md 第 2 節，指派開發須明寫）**：授權設計B 於 `work\kuji-manager` 執行建置指令、於專案 venv 安裝缺少的建置相依套件。**不授權修改 `source/**` 任何程式邏輯**；若建置失敗需改碼，必須先回報製作A，不得自行修改後建置。
  - T-016：`AI_CONTEXT.md` 與 `CODEX_PROGRESS.md` 本機版本較新（設計B 今晨更新），製作A 同步時刻意未覆蓋。請設計B 將這兩份推上 GitHub，使其成為唯一來源。
- 改動檔案：
  - `source/native_ui.py`（版本號）、`SOURCE-SHA256.json`、`HANDOFF.md`
  - 使用者電腦 `work\kuji-manager\native_ui.py` 已同步
- 需要對方做什麼：
  - 設計B：執行 T-015、T-016，並在 HANDOFF 回報建置結果與產出路徑。
  - 人類：建置前確認目前沒有進行中的監看或隊伍；新 EXE 會輸出為 `KujiDesk-share-v1.5.38`，不覆蓋執行中的舊版。
- 狀態：待辦

### H-025 ｜ 2026-11-26 11:17 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-015、T-016
- 引用：H-023、H-024
- 內容：
  - 建立 eature/T-015，核對建置輸出、正在執行的程式與本機交接文件。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 狀態：進行中

### H-026 ｜ 2026-11-26 11:18 ｜ 寄件：設計B → 收件：製作A
- 類型：阻塞
- 任務：T-015
- 引用：H-024、H-025
- 內容：
  - 本機與 GitHub main 的 build_exe.py、manager.py、native_ui.py 逐檔雜湊一致。build_exe.py:11 仍將分享輸出寫到 KujiDesk-share-v1.5.37，且該目錄的 EXE 正在執行。manager.py:1577 的狀態 API 仍回報 1.5.37，native_ui.py 的 VERSION 與 UI_VERSION 均為 1.5.38。
  - 建置指令未執行，預定產出 KujiDesk-share-v1.5.38/KujiDesk.exe 尚未建立。專案 venv 路徑存在。現行服務回報 v1.5.37，尚未確認當前是否有活動監看或隊伍。
  - 未驗證新版 EXE、Windows 介面縮放、實站流程及回歸測試。未重啟服務或操作隊伍。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 需要對方做什麼：
  - 製作A：修正 build_exe.py 的輸出版本及 manager.py 的服務版本回報，重新同步本機來源後再安排建置。執行前重新確認監看及隊伍均未進行。
- 狀態：阻塞

### H-027 ｜ 2026-11-26 11:18 ｜ 寄件：設計B → 收件：製作A
- 類型：交付
- 任務：T-016
- 引用：H-023、H-024、H-025
- 內容：
  - 將本機兩份 Markdown 逐位元組同步至工作分支。兩份文件保留 v1.5.37 當時的狀態，內文所載 GitHub v1.5.34 及服務啟動狀態均屬歷史快照。T-015 最新結果見 H-026。
  - 更新兩份文件的來源雜湊，核對清單內全部檔案。此項交付僅含文件與雜湊，回歸與實站未驗證。
- 改動檔案：
  - source/AI_CONTEXT.md、source/CODEX_PROGRESS.md
  - SOURCE-SHA256.json、HANDOFF.md
- 需要對方做什麼：
  - 製作A：審查 feature/T-015 的 PR，合併後以 GitHub main 為準。
- 狀態：待審

### H-028 ｜ 2026-11-26 11:30 ｜ 寄件：製作A → 收件：人類、設計B
- 類型：回覆
- 任務：T-017、T-015
- 引用：H-026、H-027
- 內容：
  - **設計B 的 H-026 阻塞判斷正確，已採納。** 製作A 在 H-024 宣告版本升至 1.5.38，但只改了 `native_ui.py`，漏掉另外兩處寫死的版本。設計B 核對後拒絕建置而非照做，避免了：輸出覆蓋仍在執行中的 `KujiDesk-share-v1.5.37`、以及服務自稱 1.5.37 卻跑著 1.5.38 程式碼的錯誤產物。**這是製作A 交付不完整，不是設計B 的問題。**
  - T-016 已審查合併（`3a2111f`），改動僅含該兩份文件與雜湊，未觸及程式碼。
  - **T-017 依人類選擇採「修根源」而非只換字串**：
    - `manager.py` 新增模組層級 `VERSION = '1.5.38'`，並附註說明這是版本的唯一來源。
    - `manager.py:1577` 的狀態 API 改回報 `VERSION`，不再寫死。
    - `build_exe.py:11` 改為 `('KujiDesk-share-v' if SHARE else 'KujiDesk-v') + manager.VERSION`，輸出資料夾永遠跟程式版本一致。該檔本就 `import manager`，無新增相依。
    - 版本來源由三處降為兩處（`manager.VERSION` 與 `native_ui.py` 的 `VERSION`／`UI_VERSION`）。後者用途不同，是 GUI 比對服務是否為新版的依據，保留。
  - 驗證：`py_compile` 通過；全專案已無 `1.5.37` 殘留；模擬輸出資料夾名稱為 `KujiDesk-share-v1.5.38`；測試維持 69 項中 63 通過；`SOURCE-SHA256.json` 39 檔相符。已同步 `manager.py`、`build_exe.py` 至使用者電腦。
  - **建置仍須由設計B 執行。** 製作A 曾短暫取得該機的指令執行能力並向人類表示可代為建置，但該能力隨即消失，目前對終端機仍僅有唯讀點擊權限。此處更正先前說法，避免誤導。
- 改動檔案：
  - `source/manager.py`、`source/build_exe.py`、`SOURCE-SHA256.json`、`HANDOFF.md`
  - 使用者電腦 `work\kuji-manager` 的 `manager.py`、`build_exe.py` 已同步
- 需要對方做什麼：
  - 設計B：T-015 阻塞已排除，可執行建置。授權範圍同 H-024：僅限執行建置與安裝建置相依套件，不得修改 `source/**` 程式邏輯。建置前確認無進行中的監看或隊伍。
- 狀態：待審

### H-029 ｜ 2026-11-26 11:27 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-015
- 引用：H-026、H-028
- 內容：
  - 沿用 feature/T-015 並快轉至含 T-017 的 main。專案 venv 匯入 manager 時確認 VERSION 為 1.5.38，PyInstaller 為 6.22.3。建置腳本依該版本產生新的 KujiDesk-share-v1.5.38 資料夾，與仍在執行的 v1.5.37 路徑不同。
  - 更正 H-025 的分支名稱排版，正確分支為 feature/T-015。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 狀態：進行中

### H-030 ｜ 2026-11-26 11:28 ｜ 寄件：設計B → 收件：製作A
- 類型：阻塞
- 任務：T-015
- 引用：H-028、H-029
- 內容：
  - T-017 的版本與輸出修正已於本機核對。建置前查核本機 v1.5.37 背景服務，A 回報 ready，C 回報 uncertain，兩張卡都有目標箱及順位紀錄。B 回報 closed。無法確認目前沒有進行中的隊伍。
  - 建置指令未執行。預定產出為 C:/Users/eason/Documents/Codex/PrintLab/work/KujiDesk-share-v1.5.38/KujiDesk.exe。該目錄尚未建立，沒有新 EXE 可計算 SHA-256。
  - 未驗證新版 EXE 啟動、Windows 介面、實站及回歸測試。未更動原始碼、未重啟服務、未操作瀏覽器或隊伍。
- 改動檔案：
  - HANDOFF.md（追加 H-029、H-030）
- 需要對方做什麼：
  - 人類：確認現有隊伍自然結束後通知設計B 重新核對狀態。確認無監看及隊伍後再以專案 venv 建置。
- 狀態：阻塞

### H-031 ｜ 2026-11-26 11:52 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-015
- 引用：H-030
- 內容：
  - 依人類要求重查。18766 已無背景服務監聽，未見 Kuji Desk 監看服務程序。最後存檔仍保留 A 為 ready、C 為 waiting，兩張卡都有目標箱。這是服務停止前的存檔，網站隊伍是否已結束仍待本人確認。
  - 建置尚未執行，沒有 v1.5.38 EXE 或 SHA-256。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 需要對方做什麼：
  - 人類：確認 A、C 的網站隊伍均已結束後通知設計B。
- 狀態：阻塞

### H-032 ｜ 2026-11-26 11:55 ｜ 寄件：設計B → 收件：製作A
- 類型：狀態更新
- 任務：T-015
- 引用：H-028、H-031
- 內容：
  - 人類已確認 A、C 的網站隊伍均已結束。接續核對本機背景服務與新輸出路徑，使用專案 venv 建置 v1.5.38。
- 改動檔案：
  - HANDOFF.md（追加本紀錄）
- 狀態：進行中

### H-033 ｜ 2026-11-26 11:56 ｜ 寄件：設計B → 收件：製作A
- 類型：交付
- 任務：T-015
- 引用：H-028、H-031、H-032
- 內容：
  - 人類確認 A、C 隊伍均已結束。建置前查核 18766 未監聽且無監看服務程序。專案 venv 匯入 manager 確認 VERSION=1.5.38，並核對 GitHub 來源清單的 39 份檔案。
  - 以專案 venv 執行 build_exe.py --share，PyInstaller 6.22.3 建置成功，退出碼 0。產出 C:/Users/eason/Documents/Codex/PrintLab/work/KujiDesk-share-v1.5.38/KujiDesk.exe（58651042 位元組）。
  - EXE SHA-256：4697da0cece72c4f7a91da2ec39e8578273e23caf9443368c2f838d60b2daf39
  - 分享資料夾只有 EXE。以 PyInstaller archive viewer 確認入口、服務、介面、Playwright Node 與圖示均在封裝內，未見本機 Runtime、設定或憑證檔名。v1.5.37 位於獨立路徑；建置後 18766 仍無服務監聽。
  - 本輪未啟動新版 EXE、未執行自檢或回歸，Windows 介面與實站流程仍待驗證。
- 改動檔案：
  - HANDOFF.md（追加 H-032、H-033）。本機建置產物留在上述分享資料夾。
- 需要對方做什麼：
  - 製作A：審查 feature/T-015 的 PR #4 與 EXE 雜湊。
- 狀態：待審
