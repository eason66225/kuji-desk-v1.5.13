# Kuji Desk AI 接手摘要

更新：2026-11-26。先讀本檔及 AGENTS.md；架構查 ARCHITECTURE.md，操作查 使用說明.md，歷史決策才讀 HANDOFF.md。

## 版本與套用狀態

| 範圍 | 版本／狀態 |
| --- | --- |
| 本機來源／最新分享 EXE | UI／服務 v1.5.37（已啟動） |
| 目前服務 | 2026-11-26 已換為 v1.5.37，loginOnly=true |
| 桌面 GUI | v1.5.37 已開啟，視窗標題已核對 |
| DC 通知程序 | 已獨立替換為 v1.5.36，已確認存活與連線心跳 |
| GitHub | 公開 main 與 Release 最新 v1.5.34；35／36 尚未同步 |

2026-11-26 使用者要求開新版本；實際發現舊服務1.5.11、所有帳號未開瀏覽器且沒有活動監看／隊伍任務，故換服務37並開新版GUI。設定與任務紀錄保留，未自動重送排隊；目前loginOnly，A/B/C closed，需本人連接Chrome再啟用控制台。重新讀帳號狀態，不依此處歷史狀態猜隊伍。

## v1.5.37 API 查詢恢復（已啟動，待本人連接Chrome）

查明接管 Chrome 後 api_wait_count 被改為回空 dict，query_inventory_api 只讀靜態 DOM。已改順位由頁內 POST SelectBoxDetail.aspx/GetLotteryBoxWaitCount，讀 d.your_waiting_no（字串或物件 d）；userId 從原頁記憶體取得，不輸出不複製 Cookie。庫存頁內 GET 當前箱頁並解析 HTML，來源標記 api。每10秒順位、每180秒庫存，手動更新庫存也查順位；查詢保留已登入分頁，不整頁刷新。30秒內最新順位優先於靜態DOM，切箱清除此優先狀態與舊庫存。失敗保留上次值，錯誤事件每類每分鐘最多一筆，驗證仍暫停。恢復查詢0籤時既有售完接續排程。

已用新 Account 方法對實站做唯讀驗證：順位10人、庫存75枚／12賞，DOM重讀不覆蓋最新順位，timeOrigin不變；更早原始接口驗證順位11人。語法檢查與v1.5.37分享打包成功。服務37已啟動；實際使用需重新連接Chrome，不能把先前唯讀測試等同本輪三帳號已接回。

## 最近修正

- v1.5.31 明確選擇 Chrome 設定檔名稱／目錄，避免 last_used 指向 A 造成 B 重複綁定。
- v1.5.34 Cloudflare DC 與本機非模態提示分開勾選，同次驗證各提示一次；彈窗需 GUI 開啟。作者只在本機停用「通過入場限制」通知，程式選項仍保留。
- v1.5.35 待套用：辨識倒數＋可見購入入口的 ready 頁；無退出入口時，離箱改等待網站釋放後返回同商品列表，可停止，不再直接 goto 後報讀不到箱子。完整流程未驗證。
- v1.5.36 已套用通知程序：一般 uncertain 同箱同 note 持續15秒才通知，恢復即取消；按帳號／商品／箱號去重，跨重排沿用。repeat_enabled 仍生效；Cloudflare、ready、售完不延遲。

## 開發入口與命令

- 來源 desktop.py；GUI native_ui.py；本機服務與 Account 流程 manager.py；DOM 解析 details.py；通知 notifications.py。完整資料流和函式見 ARCHITECTURE.md。
- 本機使用 ../../Runtime/kuji-manager/venv/Scripts/python.exe；可攜來源依 README 建立 .venv。
- 語法：python -m py_compile manager.py native_ui.py notifications.py details.py desktop.py build_exe.py
- 分享打包：python build_exe.py --share，最新輸出 ../KujiDesk-share-v1.5.37/KujiDesk.exe。
- 舊回歸入口：python -m unittest test_manager test_login_store test_notifications test_entry_tabs test_service_runtime。部分契約過時；依使用者要求近期未跑離線測試。
- 執行中版本以已認證 Client(runtime).alive() 核對，不輸出完整 state／設定或 token。

## 驗證範圍

已驗證：語法與 Windows 打包、既有 Chrome 多 profile 連接、頁內 fetch HTTP200／100箱且 timeOrigin 不變、同 profile window.open、v1.5.34 設定頁、Discord 實際測試 HTTP200、v1.5.36 通知程序存活且 connected=true。GitHub v1.5.34 已核對40份來源雜湊。

未驗證：其他電腦首次啟動、五分頁完整入場通過、新 Cloudflare DC／彈窗的實際挑戰觸發、35倒數釋放後自動接續、36刻意觸發異常穩定／復原／跨重排去重。不得將語法檢查或打包稱為實站成功。

## 下一步

取得本輪重啟授權才套用服務37（包含35離箱修正）；保留本人 Chrome，重新連線後確認實際離箱接續。通知36不需等待服務重啟。GitHub若再次更新，需同步來源、文件、來源雜湊與Release，勿覆蓋根目錄原始 v1.5.13 EXE。
