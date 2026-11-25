# Kuji Desk AI 交接

更新於 2026-11-25。從此頁和同目錄的 `AGENTS.md` 開始。只有追查舊版決策時才讀 `HANDOFF.md`。介面操作查 `使用說明.md`。

## 專案與版本

- 專案名稱為 suto 1 ban kuji（Kuji Desk）。Windows 桌面總控管理 A／B／C 三個獨立的一番賞帳號，提供監看、隊伍與庫存顯示、歷史紀錄和 Discord 通知。
- 來源位於 `C:/Users/eason/Documents/Codex/PrintLab/work/kuji-manager`。`C:/Users/eason/Documents/ChatGPT/一番賞` 是接手入口。來源掛在 PrintLab 父目錄，操作 Git 時限於本專案。
- 桌面 UI 和服務為 **v1.5.20**，開窗使用本機 Chrome。關閉控制台可開專用視窗登入；首頁導覽被中斷時保留視窗並記錄狀態。分享版位於 `../KujiDesk-share-v1.5.20/KujiDesk.exe`。來源、打包檔、執行中的服務要分別確認。
- 相對來源目錄的 Runtime 為 `../../Runtime/kuji-manager`。分享版可用本機 AppData 的 Runtime，並透過已認證的探測重用既有服務。A／B／C 各用 `profiles-chrome/<帳號>`，登入備份為 `login-chrome/<帳號>.bin`，由 Windows DPAPI 保護。首次切換至 Chrome 需要手動登入。

## 檔案入口

| 要改的範圍 | 從這裡找 |
| --- | --- |
| 開窗、監看、排隊狀態、售完接續 | `manager.py` 的 `Account`，先定位 `open`、`start`、`observe_queue`、`reconcile_queue_page` 或 `leave_and_requeue` |
| 商品網址與入場狀態 | `manager.py` 的 `entry_url`、`validate_config`、`recover_entry`，以及 `cloudflare_pause.py` |
| 籤數、各賞、順位 | `details.py` 解析頁面，`manager.py` 的 `query_inventory_api` 與隊伍狀態同步。順位可讀 JSON，籤數的「API」是 HTTP GET 後解析 HTML |
| 桌面控制台、批次更新、歷史 | `native_ui.py` 的 `NativeUI`、`batch`、`show_logs` 和 `Client`；F5 更新 GUI 資料 |
| 啟動與發行 | `desktop.py` 分派 GUI／服務／通知，`service_runtime.py` 管理 18766 與 Runtime 尋址，`build_exe.py` 打包 |
| 登入與通知 | `login_store.py` 負責本機登入備份；`notifications.py` 管理 Discord 設定、通知與去重 |

## 目前最重要的未解問題

- **舊 Brave 版的驗證診斷。** 最後一次診斷認證到本機服務 v1.5.16，並核對 A、C 是獨立 Brave 程序。兩個商品頁視窗標題仍為「請稍候…」，總控卻顯示「請選擇商品」。當時電腦操作擷取失敗，缺少實際頁面內容與 HTTP 證據，反覆驗證的根因未明。當時帳號狀態僅供比對。
- 使用者在專用視窗自行完成驗證。後續若收到同一問題，先核對當下版本、視窗畫面和總控紀錄。若確認畫面是安全驗證但總控誤判待命，檢查 `Account.check_cloudflare` 何時收到導覽回應或頁面證據，優先修正暫停與提示。手動驗證完成後，分別確認實站選箱頁及監看狀態。
- v1.5.18 的 78 項回歸、隔離 Brave 導覽中斷及 EXE 自檢通過。已開啟新版 GUI；當時登入服務仍是 v1.5.17，保留既有登入視窗。重啟會沿用登入模式。
- v1.5.17 的 76 項回歸、隔離 Brave 登入模式、Tk 按鈕狀態及分享版 EXE 自檢均通過。當次已開啟新版桌面視窗，確認 18766 未啟動。這些結果只覆蓋本機行為。完整關閉專用瀏覽器後的實站排隊流程也未驗證。

## 維護重點

- 先用現有的 `native_ui.Client(runtime).alive()` 讀版本與必要狀態。服務使用 `127.0.0.1:18766`。執行事件在 Runtime 的 `events-A.jsonl` 等檔案，啟動問題看 `desktop.log` 或 `native-server.log`。只輸出必要欄位。
- 以同帳號、同商品、同箱核對狀態。結果不明時確認順位，避免重複提交。遇到安全驗證保留視窗，交由使用者處理。需要影響隊伍的測試或重啟，先依 `AGENTS.md` 核對本輪授權。
- 尚未選定箱子的帳號略過籤數更新。缺資料顯示「—」，只有可辨識的資料才顯示 0。保留「籤」字、大字庫存、開始綠／停止紅，以及開啟／切回共用按鈕。
- 保留歷史事件的 `at`、`message`、`pid`、`boxId`、`boxSeq`，先記錄再清除箱號。不要將 Runtime、登入資料、Webhook 或控制台憑證放入交付或輸出。

## 測試與打包

從來源目錄執行。分享版和來源啟動使用同一組測試。

```powershell
$kujiPython = '..\..\Runtime\kuji-manager\venv\Scripts\python.exe'
& $kujiPython -m unittest test_manager test_login_store test_notifications test_entry_tabs test_service_runtime
& $kujiPython build_exe.py --share
```

打包後，以新 EXE 執行 `--self-test <絕對結果檔路徑>`，確認結果中 `ok`、`frozen`、`native_ui` 為 true，分享目錄包含 EXE。交付時分別記錄測試結果、產物路徑及服務是否已套用。

## 一般瀏覽器選箱掃描

`browser-box-scan/` 為獨立 Chrome 擴充套件。點圖示時讀取已載入的選箱列表，依目標籤數列出結果，並比較同商品同頁的上次最大箱號。套件自行使用瀏覽器的本機儲存，無需啟動 Kuji Desk。模擬頁解析及語法檢查通過，尚未在使用者瀏覽器安裝或測試實站。

v1.1.0 新增單分頁選箱刷新。由使用者開始，每分鐘一次、最多 10 分鐘。遇到驗證、入場限制、列表無法辨識或離頁即停。找到符合條件的新箱時標出原頁箱子，保留網站原本的選箱及排隊操作。模擬頁驗證刷新、停止、標示、到期及離頁；尚未安裝至實際瀏覽器。

v1.1.1 改為每輪重新抽取 60–90 秒後刷新，保留單分頁、10 分鐘與各停機條件。

v1.1.2 找到新箱時，若網站現有連結指向同站同商品的箱頁，直接開啟並停止刷新。無相符連結時停止並提示使用者選取，排隊保留由使用者在網站確認。模擬測試驗證開箱、拒絕不符連結與停止條件，尚未驗證實站連結格式。

已用隔離 Brave 驗證 `queue-flow-demo.html`：手動／自動兩種模式、2–3 秒抖動、單次模擬排隊與停止均通過，測試頁無 HTTP 請求。此測試獨立於擴充套件與實站。

v1.5.19 已打包並執行。原登入服務無帳號開窗，已切至 Firefox 版登入服務。帳號 A 的專用 Firefox 已進入實站，視窗標題先為「一番くじONLINE — Nightly」，稍後轉為「Just a moment... — Nightly」，仍待使用者確認頁面。控制台維持關閉，實站登入、監看與排隊未操作。本輪按使用者要求未跑離線測試。
