# Kuji Desk 本輪交接 · 2026-11-17

已從擴充套件方案改成本機 Python 管理程式，一個本機面板管理三個 Chrome 專用持久設定檔。程式與 UI 位於 work/kuji-manager；依賴與個人資料在 Runtime/kuji-manager。沒有更動 PrintLab 原有模型、設備、列印流程或 Git 暫存區。

已完成：集中啟停、帳號別名、開啟／切回專用視窗、背景 API GET 查新箱、2.2–4.5 秒隨機等待、新流水號與精確張數選擇、官方按鈕單次提交、個人順位／WebSocket 輪到提示、不同音高提醒、耗時紀錄、提交前磁碟持久化與重啟不重送。

驗證：9 項單元與本機 API 測試通過；Python／JS 語法檢查通過；總控響應式版面檢查完成；實際開啟帳號 A 的獨立 Chrome 成功，未登入、未提交真實排隊。QA 服務已停止，最新版服務以本機隱藏程序啟動，PID 記於 Runtime/kuji-manager/manager.pid；面板連線憑證僅在 Runtime/kuji-manager/panel-session.json。面板使用 127.0.0.1:18766。

下一步：使用者等舊隊伍結束後，在專用 A/B/C 視窗各登入一次，回列表後啟動監看，確認此新版實際順位與通知。網站若拒絕 APIRequestContext GET，需在保持同帳號隔離的前提下檢查實際回應；不繞過驗證或限制。原擴充套件 v0.3 曾由使用者回報看來成功，新本機版不承接其成功結論。

更新方式：完成隊伍後重啟同一份本機程式；不需安裝擴充套件，尚無網路自動更新服務。原始碼壓縮檔 work/kuji-desk-v1.0.zip 不含 Runtime、憑證、虛擬環境或第三方瀏覽器。


## 1.1 本輪更新

使用者要求退出本箱重排、顯示目前順位、籤數、各賞剩餘量，並提供官方摘要截圖。已用 computer-use 的 sky API 讀取真實箱子頁並在使用者明確授權下測試一個視窗退出：lbExitQueue → 確認視窗「はい」→ 返回同商品 SelectBox 列表。該帳號對應 C；未再加入新隊伍。

新增 details.py：解析「あとN人であなたの番です」，修正舊版只接受純數字而把真實隊伍誤標 uncertain 的問題。庫存採可見頁面摘要為優先，重複詳細段落不覆蓋摘要；Last One 未提供數量不推算，未知與零區分。

新增 requeue API 與本機確認視窗，驗證箱子及商品、透過官方退出和確認按鈕退出、等待返回選箱列表與個人隊伍消失，然後建立新基準監看；退出結果不明不再開始。新增 inventory API，沿用官方更新按鈕與網站冷卻，不額外輪詢伺服器庫存。

使用者已明確同意立刻重啟並接受中斷目前隊伍。已核對舊 PID 的執行檔與命令列後停止本機管理程式的程序樹，啟動 v1.1.0。保留所有設定檔與任務紀錄。已透過總控重新開啟 A/B/C 並只讀取隊伍，沒有重新提交排隊。實際讀到 A 前方54人、B前方50人，三箱均剩70枚，A–J共10賞數量齊備；C因已退出沒有順位，仍保留需確認狀態。使用者如要再開始C，先確認網站已退出、結束原助手任務並回選箱列表。

15項測試通過；已實測總控「更新籤數」按鈕，A隊伍仍在；已開啟並取消總控重排確認提示，沒有退出A。完整自動退出後再次排隊未以真實隊伍實測，只由自動測試覆蓋。新版已套用到正在使用的總控分頁。預覽 work/kuji-manager/preview-v1.1.jpg；來源包 work/kuji-desk-v1.1.zip 不含 Runtime 或登入資料。


## Discord 與執行檔交接

使用者提供 Discord Webhook 並明確要求通知，接著要求 Windows 執行檔。Webhook 只保存在 Runtime/kuji-manager/discord.json（不在來源碼、EXE 或來源包），請勿在回覆或日誌重印。已送出一則測試訊息，Discord 回覆 HTTP 200；收據記於工具結果及本機狀態，沒有要求使用者再次確認。

新增 notifications.py：獨立本機 worker 每秒只讀總控 API，ready／uncertain 時傳帳號標籤、箱號與頁面庫存。持久化事件去重、提交前保留紀錄、429 依回應等待；其他結果不明不自動重送。單實例檔案鎖防止重複程序。worker PID 記於 Runtime/kuji-manager/discord-worker.pid，狀態 discord-status.json。未重啟或改變正在排隊的主程式；目前主服務仍可為1.1，通知已由獨立worker服務。未來啟動新版 manager 或 EXE 時會自動確保 worker 執行。

新增 desktop.py、build_exe.py。PyInstaller 6.22.3 由 PyPI 安裝於專用 venv。work/KujiDesk/KujiDesk.exe 為約55MB單檔，包含Python、網頁資源與Playwright driver，使用本機已安裝的官方 Chrome。旁邊 KujiDesk.runtime.json 指向目前工作空間 Runtime，不含秘密；獨立搬移且缺少指標時預設使用 LocalAppData/KujiDesk。使用說明與第三方原授權文本在同資料夾。登入資料與Webhook均未包入EXE。

驗證：20項測試通過。EXE --self-test 的ok、web_assets、playwright_driver、driver_working、frozen全為true；實際執行EXE成功，退出碼0，重用既有總控並開啟新管理頁，不中斷現有隊伍。Cua確認新管理頁已出現。


## 原生介面懸停反白修正 v1.3.1

使用者截圖顯示「賞別」表頭滑過時變成亮底。原因是 clam 主題的狀態 map 優先於 configure，未覆寫 active／pressed 等狀態。已在 native_ui.py 為表頭 disabled／pressed／active／focus 明確設定深底、文字及邊框，並覆寫捲軸 active／pressed 配色。Tk Button 的 activeforeground／activebackground 也固定為該按鈕的原配色。選取資料列保留低對比藍底，不使用白色。

UI_VERSION 1.3.1 與背景相容 VERSION 1.3.0 分開，避免介面樣式更新被誤認為需要重啟隊伍。輸出 work/KujiDesk-v1.3.1/KujiDesk.exe，不覆蓋正在執行的舊版EXE。此次沒有重啟或操作背景隊伍。

已用實際 Tk runtime lookup 驗證表頭 active／pressed／focus／disabled 均為 #202c3a；捲軸 active／pressed 為 #3b5064。使用者只需關閉舊管理視窗並開新版，不按重新啟動服務。

## Discord 設定選單 v1.3.2
原生視窗新增 DC 設定：Webhook 遮蔽輸入、啟停、ready/uncertain 事件勾選、儲存及非阻塞測試通知。直接沿用本機 discord.json；worker 自動重讀，不重啟背景服務或隊伍。測試使用目前輸入網址，未儲存不改既有設定，錯誤不包含秘密。27 項測試通過，實際 Tk 建立設定視窗與遮蔽欄位通過。版本化輸出 work/KujiDesk-v1.3.2。C 帳號排隊顯示不一致仍待單獨確認，本次未修改排隊邏輯。

## v1.3.3 / v1.3.4 更新
速度：啟動時以可見列表作基準，首輪立即讀最新列表，後續維持隨機抖動。進入詳情只等 domcontentloaded 與排隊按鈕可見，保留身份核對與提交前持久化。修復切回已最小化 Chrome 視窗，透過 CDP 恢復視窗再 bring_to_front。使用者已同意中斷隊伍，背景服務已重啟並驗證版本 1.3.3；帳號保存為 uncertain，未自動重新提交。
v1.3.4 DC 新增 ahead_threshold（前方人數小於等於）、repeat_enabled、repeat_seconds（最短10秒），等待門檻與 ready/uncertain 各自去重，重複僅針對確定已送出事件；未知結果不盲目重送。30 項測試通過。通知 worker 已單獨更新，不動排隊服務。
使用者指定主標題與視窗名稱改為 suto 1 ban kuji。新版輸出 work/KujiDesk-v1.3.4。

## v1.3.5 視窗切換
使用者要求同一按鈕點一次最小化、再點還原。open 對既有分頁呼叫 focus_window(toggle=True)，用 CDP 實際 windowState 判斷，最大化還原時保留原狀；focus API 仍只帶到前景。切換不觸發導航或排隊提交。31 項測試通過，包含最大化→最小化→最大化及不導航驗證。目前 A/B/C 均 waiting/opened，尚未重啟背景服務套用以免中斷隊伍。

v1.3.5 使用者明確同意現在重啟並接受隊伍中斷。已執行 Client.restart_server，API 驗證 version=1.3.5；A/B/C 均 uncertain、opened=False，未自動重送排隊。已開啟新版原生 UI。

## v1.3.6 精簡按鈕與停止修正
開始/停止合併 monitor 按鈕，依 API canStop 切換，執行時再次讀取最新狀態。移除返回選箱列表及結束助手任務的 UI。stop 原先僅 cancel Event 後等待 task，網路請求可卡15秒；改取消 hunt task 並等待 CancelledError 清理，避免停止後進箱。32項測試通過，含阻塞請求可1秒內取消且不提交。輸出 work/KujiDesk-v1.3.6，背景仍待授權更新，未擅自中斷隊伍。

使用者已明確同意立即重啟 v1.3.6 並接受隊伍中斷。Client.restart_server 完成，API 驗證 version=1.3.6；A/B/C 皆 uncertain、opened=False，沒有自動重送排隊。已啟動 v1.3.6 原生介面，登入與本機設定保留。

## v1.3.7 一鍵更新籤數
原生 UI 新增更新全部籤數（F5），batch inventory 依各帳號 canRefresh 且非 busy 分派既有 inventory API，三帳號並行。沿用後端 page.reload，不點網站庫存按鈕。略過不可更新及繁忙帳號，無可更新時顯示說明。已驗證可更新 A/C、略過 B 與 busy C。僅 UI_VERSION 更新1.3.7，背景 VERSION 保持1.3.6，不需重啟隊伍。

## JSON/API 研究（帳號 B）
使用者要求直接網站 API 排隊、需要時才開網頁，並授權可中斷隊伍。已停止服務以獨立研究 B profile。登入後保存受保護頁面與23個站內腳本於 Runtime/kuji-manager/api-research（含個人資訊，只在本機，不打包）。網站 SelectBoxDetail 內嵌腳本確認：GetLotteryBoxWaitCountWithInsertQueue JSON加入；GetLotteryBoxWaitCount JSON唯讀順位；DeleteWaitingLotteryBox JSON退出；WebSocket LotteryBoxQueue 使用 StartWebSocket/StartViewing/HeartBeat，50000ms心跳；順位>3時官網每300000ms重查，<=3接WebSocket。尚未送加入/退出/購買請求，首次唯讀測試在Chrome重開後失去網站session而未送API。
修正 probe_queue_api.py：B可見視窗手動登入後，在同次context內取cookies，只放記憶體，關Chrome後以aiohttp讀detail並呼叫唯讀GetLotteryBoxWaitCount。正在等待第二次B登入，exec session70524。research_protocol.py為初次採集，已完成；profile指定B。後續先poll70524結果，勿另開同profile。全API實作尚未完成；不要聲稱成功。服務目前已停止，GUI可能顯示離線；研究結束需恢復服務（不要與研究B profile並行）。

## 唯讀 JSON 驗證成功，保留 B 視窗
probe_queue_api.py session70524已成功退出：Chrome關閉後 aiohttp GET detail仍登入有效、POST GetLotteryBoxWaitCount HTTP200，data.d欄位display_id,total_queue,your_waiting_no，your_waiting_no="27"。證明同次有效session可轉交背景HTTP查詢。使用者隨即要求「不要一直關掉」，後續嚴格保留B視窗，勿再自動close context。已啟動 hold_research_browser.py（exec session61281），B專用profile保持開啟，只有使用者自行關閉才結束。勿另起同profile，不要恢復會搶用B profile的服務。先前GUI/manager仍停止。原始probe會自動關Chrome，不要再次執行；後續需改成共用這個長駐研究context或在使用者明確同意後遷移。尚未驗證加入隊伍與WebSocket交接，不宣稱全API可用。

## v1.4.0 HTTP Session 同步與背景監看
- manager.py 新增 sync_cookies：視窗開啟時將 Cookie 同步至 aiohttp.ClientSession，並支援在專用視窗關閉時維持 Session 進行背景監看與排隊。
- start() baseline 與 fallback 調整：當瀏覽器開啟時沿用可見 DOM 為基準並支援 context.request fallback；無視窗時透過 aiohttp fetch_boxes 建立基準。
- 前端與原生 UI（web/app.js、native_ui.py）升級至 v1.4.0，加入 hasSession 狀態標記與無頭模式下直接開始監看的支援。
- 32 項單元測試通過。使用者明確授權重啟後，已執行 Client.restart_server 順利套用 v1.4.0；Discord 通知連線正常，帳號設定檔與登入狀態完整保留。

## Discord 籤筒抽完通知與介面用字修正
- notifications.py 新增 sold_out 事件：當箱子剩餘籤數為 0 或網站顯示售完時，觸發 Discord 通知「📢 籤筒已抽完（售完）」，包含帳號標籤、箱號與剩餘資訊；持久化去重防止重複洗頻。
- native_ui.py 的 Discord 設定視窗新增「籤筒抽完（售完）時通知」選項，設定檔 discord.json 已預設加入 sold_out。
- 介面用字修正：將主介面「張數」全面修正為「目標籤數」，彈出訊息與各處文字統一使用繁體「籤」（竹字頭：目標籤數、抽籤、剩餘籤數、更新全部籤數、籤筒抽完）。
- test_notifications.py 新增 test_sold_out_notification 單元測試，共 33 項測試全部通過。獨立的 Discord 通知 worker 已平滑重啟至最新版（PID 65452），未中斷主排隊服務。

## 剩餘籤數字體放大
- native_ui.py 將卡片「剩餘籤數」字體大小從 14 提升至 22（粗體），並支援狀態顏色高亮（有籤數時為亮綠色 LIME，0 枚抽完時為警告紅橘色 #ff6b6b）。
- web/style.css 將網頁版剩餘籤數數值 font-size 提升至 26px。
- 單元測試通過。


## v1.5.0 API 數值直讀、防 DOM 覆蓋與 UI 簡潔化

### 使用者回饋與問題診斷
1. 前方順位倒退／未依 API 更新：原本在進入箱子排隊後，後端 _api_poll_loop 雖會每 15 秒向官方 GetLotteryBoxWaitCount 取得精準的 your_waiting_no，但因為可見瀏覽器中的 SelectBoxDetail.aspx DOM 是靜態文字（例如「あと67人であなたの番です」），每秒執行的 observe_queue 輪詢 DOM 時會比對到 
umber != self.queue_no，進而把 queue_ahead 覆蓋回網頁的舊數值 67 人。
2. 剩餘籤數被 DOM 覆蓋：
ead_detail() 每秒解析 DOM 靜態文字，會把 self.inventory 覆蓋成網頁初始載入時的舊籤數，破壞 query_inventory_api() 查詢到的真實庫存。
3. 標籤繁雜問題：介面出現了過多「（以 API 為準）」、「（API 數值）」等標註，使用者明確要求「數值都不必特別顯示以 api 為準或是 api 數值」，直接顯示乾淨數字即可。
4. 剩餘籤數字體不夠大：需要進一步放大強化視覺層級。
5. F5 重新載入 GUI：需支援鍵盤快捷鍵 F5 立即重繪與查詢籤數。

### 修正與落實
1. 防 DOM 覆蓋機制：
   - observe_queue() 加入保護：僅在尚未取得 queue_ahead 或 DOM 順位明確前進（數值變小）時才採用 DOM 數值，嚴禁因靜態 DOM 倒退回舊的高順位。
   - 
ead_detail() 加入保護：當 self.inventory 來源已為 pi 時，靜態 DOM 不得覆寫現有籤數與各賞清單。
2. 背景自動化 API 同步：
   - _api_poll_loop() 輪詢間隔縮短至 10 秒，並在進入隊伍時立即啟動；每 180 秒（3 分鐘）自動呼叫 query_inventory_api() 更新即時剩餘籤數與獎品數量。
   - 
ative_ui.py 定時器同步觸發 pi_inventory，確保獨立視窗運行時亦維持 3 分鐘自動 API 庫存同步。
   - 鍵盤按下 F5 綁定 
eload_gui()，一鍵重新整理介面並查詢全部籤數。
3. 清理所有「API 數值」相關標註：
   - 移除 Native UI 與 Web UI 中的「（API 數值）」、「API 數值」徽章、「API 準確」、「· 數值以 API 為準」等字眼。
   - 順位維持「前方 X 人」，籤數維持「剩餘籤數：X 枚」。
4. 剩餘籤數字體放大：
   - 
ative_ui.py 剩餘籤數字體提升至 36 號粗體（Microsoft JhengHei UI）。
   - web/style.css 剩餘籤數字體提升至 64px。
5. 驗證與打包：
   - 	est_manager.py 新增 	est_read_detail_preserves_api_inventory 與 	est_observe_queue_does_not_rollback_queue_ahead_to_stale_dom，共 29 項測試全數通過。
   - 	est_notifications.py 通過。
   - 重新打包 work/KujiDesk-v1.5.0/KujiDesk.exe，--self-test 通過。
   - 背景服務已重啟至 v1.5.0，原生 UI v1.5.0 已啟動並連線。


## 按鈕介面簡化與功能整合（2026-11-18）
- 依使用者要求進行按鈕精簡與合併：
  1. 移除各帳號卡片與頂部設定列的「以 API 查詢籤數」按鈕。
  2. 移除卡片與頂部設定列的「視窗 F5 重新整理」按鈕。
  3. 將「切回視窗」與「切回此視窗」合併為單一按鈕（未開啟時顯示「開啟視窗／登入」，開啟後顯示「切回視窗」並具備視窗切換與最小化喚醒功能）。
  4. 帳號卡片操作區精簡為乾淨對稱的 2 欄 3 列配置：
     - 第一列：切回視窗／開始監看（或停止監看）
     - 第二列：離開目前箱並監看／重新查看／修復
     - 第三列：重啟此帳號視窗／修改帳號名稱
  5. 網頁版 web/app.js 同步移除籤數區的 API 查詢與 F5 重整按鈕。
  6. 重新編譯 KujiDesk.exe，單元測試全數通過，獨立桌面視窗已平滑重啟。


## 控制台開關取代網頁功能（2026-11-18）
- 依使用者要求，全面移除「開啟網頁」按鈕與功能：
  1. 移除介面頂部「開啟網頁（選用）」按鈕及工具選單「🌐 開啟網頁版總控」指令。
  2. 新增「開啟／關閉控制台」雙態開關按鈕（取代原本開啟網頁的位置）：
     - 服務運行中時：顯示為紅色「關閉控制台」按鈕，點擊經確認後可安全停止總控背景服務與監控。
     - 服務停止時：自動切換為綠色「開啟控制台」按鈕，點擊可立即重新拉起背景服務並重新連線。
  3. 重新編譯 KujiDesk.exe，單元測試通過，桌面視窗已平滑重啟。

暫時限制頁重試：新增 wait_temporary_page，進入列表／提交前箱頁出現一時的且無正常箱子或隊伍標記時，每3–4秒重整，最多100次；429數字Retry-After遵守等待。已排隊頁不重整。30項測試通過（原有AsyncMock警告仍在）。未重啟目前服務，背景純HTTP限制重試尚未加入。售完自動接續仍依賴Chrome返回列表。

商品頁接續：限制解除後，開啟流程辨識相同PID商品頁，以唯一可見購入/購入する入口進入SelectBox，驗證商品再start監看；不碰結帳按鈕。正常商品頁標題避免一時的注意事項誤判。31項測試通過，含入口單次點擊及不同PID拒絕。未實站驗證、未重啟排隊服務。

執行紀錄：native UI新增執行紀錄視窗，ABC分頁、毫秒時間、每帳號500筆、即時追加去重，讀Runtime/events-ID.jsonl歷史。後端記錄進箱載入/按鈕核對/提交前後耗時，事件持久追加JSONL；未記cookie或token。31測試及Tk紀錄視窗驗證通過。B已透過既有服務start，確認watching；未重啟A隊伍。既有視窗商品頁open及start接續補強。新版服務尚未套用。

修復lbAddToCart入口：實際B/C箱頁觀察このくじ箱にする；B點擊後網站顯示前方34人，inspect API確認B waiting34、C waiting54。程式支援兩種入口，替代入口核對站點/詳情路徑/PID/lbdid/文字，舊入口保留data屬性核對；提交前持久化、單次點擊。32測試通過（新增替代入口與不同箱拒絕），EXE已重包，背景未重啟（使用者要求稍後）。A隊伍保留。

## 精簡接手資料舊版存檔（截至 v1.5.16）
以下是歷史快照，版本和待辦以 AI_CONTEXT.md 為準。

# AI 精簡接手資料

更新：2026-11-18。動態隊伍狀態不得沿用本檔。

## 位置與執行
- source：本目錄。個人資料／虛擬環境：`../../Runtime/kuji-manager`。
- Python：`C:/Users/eason/Documents/Codex/PrintLab/Runtime/kuji-manager/venv/Scripts/python.exe`；GUI 用同目錄 pythonw.exe。
- GUI：`desktop.py` 或 `開啟桌面總控.bat`。本機服務 `127.0.0.1:18766`。
- `native_ui.Client(runtime).call()` 可讀狀態；從 panel-session.json 自動取憑證，不輸出 token。動作 `call('action', {'id':'B','action':...})`。不要隨意送 start/open/requeue/restart。
- `python build_exe.py` 輸出 `../KujiDesk-v1.5.10/KujiDesk.exe`，旁邊 runtime 指標不含登入；本目錄也有舊／同步 EXE，交付前確認雜湊及時間。
- VERSION=1.5.10；UI_VERSION=1.5.10。同版本號曾多次重包，不能僅憑號碼確認載入修正，需查看執行路徑、行為／事件。

## 檔案索引
| 檔案 | 用途／主要入口 |
|---|---|
| manager.py | Account、fetch_boxes/start/hunt/enter_queue、observe_queue、query_inventory_api、reconcile_queue_page、服務路由 |
| details.py | READ_DETAIL（DOM）、parse_detail_text、parse_detail_html |
| native_ui.py | 桌面 UI、Client、show_logs、reload_gui、toggle_control |
| notifications.py | Discord worker 與通知設定／去重 |
| desktop.py / build_exe.py | 桌面／凍結版入口、打包 |
| web/ | 仍保留網頁資源；桌面已移除開啟網頁入口 |
| test_manager.py / test_notifications.py | 隔離測試；不使用真實帳號排隊 |

## 現有流程與保護
- A/B/C 各自 Chrome persistent profile。開窗同步 cookies 至記憶體 aiohttp session。
- 選箱用 HTTP GET HTML，抓新流水號且精確符合目標籤數；目前不是完整 JSON 搶箱。首查立即，後續用使用者儲存的隨機秒數。
- 找到箱子後立即載入詳情、等待可見按鈕、驗證商品箱號、持久化 submitting，再單次點擊。
- 排隊入口支援 `a.waitingStart[id$="_lbAddQueue"]` 及可見 `a[id$="_lbAddToCart"]`。後者文字「このくじ箱にする」，核對 detail URL 的站點/PID/lbdid；前者驗證 data-product-id/data-display-id。
- 實站曾對 B 點後取得前方34人，隨後本機 inspect 讀回 B waiting34、C waiting54；只證明該入口成功，不能推論所有商品或現況。
- 順位 JSON：SelectBoxDetail.aspx/GetLotteryBoxWaitCount，讀 d.your_waiting_no。背景約10秒查；DOM 不可把順位倒退成舊值。庫存來源 api 後，DOM 不覆蓋。
- 籤數查詢名稱 api_inventory，但實作是 HTTP GET 詳情 HTML 解析；背景約180秒刷新。視窗關閉仍查資料，不代表已驗證完整無瀏覽器排隊／輪到後交接。
- 售完自動找新箱：需 autoResumeSoldOut，網站確認售完並返回同商品列表後清狀態/start；純背景讀到0目前停 uncertain，尚未完整自動接續。
- 暫時限制重試 wait_temporary_page：只有一時的且無正常頁／隊伍訊號才約3–4秒reload，最多100次；數字Retry-After另等待。一般商品頁含注意事項「一時的」，有正常商品標題時不當限制頁。
- follow_product_to_list：同PID ProductDetail 的唯一可見「購入／購入する」入口 → SelectBox → 驗證同PID。新開流程限制解除或經商品頁會start；既有商品頁 open/start也補入口。手動用電腦點購入不等於目前背景程式自動start。

## UI／使用者偏好
- 名稱 suto 1 ban kuji；獨立桌面 UI，三帳號一起管理。
- 籤（竹字頭），剩餘籤數大字；數字旁不標「API數值／以API為準」。
- 開始綠／停止紅，合併一顆；單一開啟／切回視窗按鈕保留縮小／還原切換。
- 已移除卡片API查詢、視窗F5重整、重複切回、返回列表、結束任務等按鈕。
- 原開網頁位置是開啟／關閉背景控制台，關閉有確認提示。關GUI本身不應退出網站隊伍。
- 執行紀錄：右上按鈕／工具選單，ABC分頁，每帳號最近500筆、毫秒時間、即時追加。來源 events-ID.jsonl 位於Runtime，完整歷史保留本機。新階段LOG需新版服務產生。
- DC 設定：使用者自行填Webhook、前方人數門檻、重複秒數、ready／uncertain／sold_out事件。

## 最近驗證／執行狀態
- 32項 manager 測試通過；舊測試 AsyncMock 未await警告仍存在，勿稱無警告。
- Tk GUI self-test與紀錄視窗建立／顯示／去重驗證通過；EXE已重新打包。
- 使用者回報手動重啟後已讀到新版商品入口事件及 events-A/B/C.jsonl。當時 B/C watching，A idle；現在必須重新查。

## 已知待辦：修改相關功能前先看
1. 已修F5重複排程：reload_gui直接submit讀取，不再呼叫poll建立新計時器。
2. 已還原act(api_inventory)專用處理：送出前讀最新帳號，監看/未選箱略過；batch同樣過濾。後端query_inventory_api遇watching/opening/leaving或可見頁非箱頁回空結果，不解析舊target。
3. 後端與GUI各有180秒更新，可能重複查；GUI關自動更新不一定會關後端。需要統一擁有者及設定語義。
4. hunt現仍檢查 self.page.url；完整關窗後背景監看／進箱路徑不能只憑hasSession宣稱可用。
5. JSON加入／退出／WebSocket協議曾研究，但目前enter_queue仍用瀏覽器；完整無前端模式未完成。
6. 確認按鈕座標的Windows工具曾遇到DPI／幾何錯誤，曾誤開服務重啟確認；未確認則不重啟。不要盲重試座標。

## 最短測試命令（在本目錄、使用上述venv）
`python test_manager.py`
`python -m unittest test_notifications`
`python -m py_compile manager.py native_ui.py details.py`
`python desktop.py --self-test <絕對結果檔路徑>`（可能短暫建立Tk視窗）

要深入研究官方協議才讀 Runtime/api-research；內有個人資料，只取必要片段，不能整份輸出。HANDOFF.md保留歷史，若與現碼／測試矛盾，以查證結果更新此檔。

2026-11-18 籤數錯誤修復：34項manager測試通過、UI略過監看及F5不建立額外timer驗證通過。UI v1.5.2已重開，背景服務未重啟，後端新保護仍待使用者擇時套用。

UI v1.5.3：實際唯讀查詢A api_inventory重現解析失敗；B/C watching且canRefresh=False。原因非B/C無箱，A回應缺少可辨識庫存，實際回應類型當時未記錄，不得斷言session失效。新增診斷HTTP/登入欄位/限制詞/庫存文字布林，不記HTML或URL參數；無庫存同步cookie後重試一次，仍失敗保留庫存。UI更新失敗改狀態列與已開紀錄視窗，不彈窗。34測試及無彈窗模擬驗證通過。UI已套用，後端診斷仍待重啟。

監看自停診斷：B/C事件出現空字串錯誤後auto-heal回列表idle；不是30分鐘到期。空字串未記型別，不能確定TimeoutError。hunt補TimeoutError/aiohttp.ClientConnectionError限3次退避(5/10秒加原抖動)，僅重試讀列表，第三次轉uncertain；其他例外仍停止。錯誤均記type及fallback文字。35測試通過，背景未套用。

登入記憶：使用者回報每次重開要登入。固定profile已確認存在，無法僅憑此保證session保留；未證明網站根因。新增login_store.py，DPAPI CurrentUser加密本站cookies至Runtime/login/A或B或C.bin，只在頁面辨識出userId時由sync_cookies保存；開context後導航前僅補缺失且未過期cookie，既有cookie優先；shutdown嘗試sync及context.close正常落盤。4項加密roundtrip/隔離/過期域名/損壞測試+35manager測試通過，未實站重開驗證，尚未套用。首次套用後需登入一次並start以建立快照。伺服器失效仍須手動登入，不保存密碼。

## 最新接手狀態：v1.5.5（2026-11-18）
- 使用者要求停止監看，最後讀回ABC皆idle；本輪未啟動監看、未重啟服務。
- 新增歷史箱LOG篩選及上一箱按鈕，讀本機JSONL全歷史、顯示選定箱最近500筆。事件加pid/boxId/boxSeq；舊記錄不猜箱號、列未分類。清target前記離箱成功。
- API庫存確認0且autoResumeSoldOut才schedule_soldout_resume；獨立task拿lock，核對pid/target/reason，按箱去重，沿用leave_and_requeue。失敗不重送、不自動重試離箱。關窗需使用者開窗；shutdown取消接續task。
- 已知正常空列表parse_boxes回[]（必須有くじ箱選択及selectbox__box-list容器或明確無箱訊息，排除密碼頁）。start空基準0。hunt連續空列表3600秒停idle，出現箱即reset；取消舊整體30分鐘到期。未知頁面仍報錯，空列表實站結構尚未驗證。
- 49項unittest通過，Tk上一箱與新箱／舊紀錄隔離驗證通過；原AsyncMock警告仍有。來源/EXE1.5.5已更新，執行中服務尚未套用。

## v1.5.6 入場與無PID入口
- 商品ProductDetail網址本來含PID卻被list_url拒絕；validate_config改entry_url，接受同站首頁/商品列表/商品介紹/選箱列表，可暫無PID；list_url仍嚴格用於抓箱階段。
- 用戶可先填首頁或空白，入場後自己選商品。開窗會arm entry_pending；idle狀態poll建立recover_entry，明確限制文案一時的に入場いただける人数を制限しております（去空白）會重試，不再被h1/h2排除。通過但無PID留idle等選品；同站商品頁取PID→購入→list→start。一般直接開正常選箱列表仍等手動start。
- stop支援recovering/entry_pending並取消task；recovering的stop API在lock前取消，避免卡在重試鎖。停止不再自動arm；新open/start才arm。已排隊帳號不進idle入場流程。
- 53項測試通過：商品網址/無PID/惡意站點、含h1限制文案、通過後取PID、取消恢復。未實站驗證或重啟執行中服務。EXE輸出../KujiDesk-v1.5.8。服務及UI版本均1.5.6。

## v1.5.7 入場timeout與重整設定
- 實際讀到1.5.6的ABC限制重試31次仍進行；GUI timed out原因是本機Client.call40秒上限，open/start同步等待100輪入場。改begin_entry：立即回recovering，背景recover_entry持lock等待，stop先取消task，避免重送。
- 開窗goto仍30秒上限；普通連線仍可能逾時，GUI改明確「本機總控等候逾時，操作結果尚未確認，勿重複提交」，不是宣稱所有timeout消失。
- wait_temporary_page移除100次上限，重整用帳號config minSeconds/maxSeconds（預設2.2–4.5秒），保留明確429冷卻。entry_only=True等待至同站ProductDetail/SelectBox；首頁/登入頁不reload，只等手動操作，任務可stop。
- 56項unittest通過，新增背景start立即返回、lock中停止、101次仍繼續且沿用7–9秒設定；原AsyncMock警告仍有。尚未重啟使用者服務／實站驗證；版本化EXE1.5.7。
- 多分頁最終需求見v1.5.8，下列舊版單分頁說明以最新段落為準。

## v1.5.8 同帳號五分頁
- 使用者明確要求同帳號5分頁入場，現已實作；只有recover_entry看到entry_limited且有context才啟動wait_entry_tabs，非限制頁維持既有單頁流程。
- 原頁+context.new_page建立4頁，選第一個成功的同站同PID ProductDetail/SelectBox；停掉其他等待task並關閉助手敗選頁。手動開的其他頁不碰。成功頁不同時先移除原頁close/websocket監聽，移交self.page與監聽後清理原頁，避免關頁誤停帳號。
- 五頁共用navigate_entry_page的entry_reload_lock，請求間隔沿用min/max；429/503 Retry-After（秒或HTTP日期）冷卻共用，缺值預設30秒。不是五倍請求，也不保證更快。取消會停所有子task、關額外4頁並保留原頁。
- wait_temporary_page增加page參數，不共享變更self.page做並行；既有離箱cancel_observer後建立新cancel Event供新流程使用。
- 60項unittest通過（新增test_entry_tabs：成功移交/取消/錯商品/共享冷卻）。另用隔離無頭Chrome與route.fulfill（UTF8）驗證5頁→保留1頁、無誤cancel，未對網站送請求、未用使用者profile。實站與現有服務尚未套用／驗證。
- 服務與UI1.5.8，EXE ../KujiDesk-v1.5.8。後續測試：python -m unittest test_manager test_login_store test_notifications test_entry_tabs。

## v1.5.9 分頁獨立抖動（使用者最終決定）
- 五頁各自random.uniform(minSeconds,maxSeconds)等待後發請求，不再使用entry_reload_lock；因此可能同時刷新。不是v1.5.8的序列化總間隔。只有網站429/503冷卻仍全帳號共用，等待期間若新冷卻延長會再等。
- 成功頁單次移交、PID核對、停止清理沿用v1.5.8。初始額外分頁導航與後續reload都使用同一獨立抖動邏輯。
- 61項測試通過：新增5個不同抖動且5個reload都進入後才放行的屏障測試，證明非序列刷新。未實站測試／重啟服務。版本化EXE../KujiDesk-v1.5.9。

## 帳號視窗重啟卡住修正（2026-11-18）
- recovering入場任務持有帳號lock時，restart API原本先等lock、再呼叫restart_account取消任務，造成互等與GUI逾時。已在lock外先stop入場任務，確認重啟後再執行；未確認的請求不停止任務。
- 新增隔離API測試重現持鎖任務，62項unittest通過。新版1.5.10 EXE已打包且self-test通過。現有服務未重啟；唯讀狀態查詢回 unavailable，實站重啟行為未驗證。

## 通過入場限制 Discord 通知（2026-11-18）
- 新增 `entry_passed` 通知事件：當帳號解除一時限制並進入商品頁或選箱頁時，送出 Discord 通知（綠色 Embed「已通過入場限制」）。
- 包含在 UI Discord 設定視窗的事件選項中，並寫入 `discord.json` 的 `events` 欄位（預設包含 `ready`、`uncertain`、`sold_out`、`entry_passed`）。
- 帳號以 `entryPassedAt` 時間戳記錄通過時間，通知 ledger 依帳號與該時間戳唯一去重，避免重複推播。
- 63 項 unittest 全數通過（含新增之 `test_entry_passed_notification`）。

## 支援選擇是否啟用入場重新整理功能（2026-11-18）
- 在桌面 UI 監看設定區新增「啟用入場重新整理功能」核取方塊（`entryRefresh`，預設為 True）。
- 設定同步存入 `ui-settings.json`，儲存時透過 API `config` 指令更新執行中帳號配置。
- 當停用時（False），遇網站一時入場限制（`一時的に入場いただける人数を制限しております`）不會進行多頁自動刷新或背景重整，維持在瀏覽器畫面並提示手動操作。
- 64 項 unittest 全數通過（含新增之 `test_entry_refresh_switch_disables_reloads`），Tk self-test 通過。
## Playwright Node 偵測與桌面捷徑更新（2026-11-18）
- 截圖報錯根因：使用者雙擊桌面捷徑開啟了舊版 work/KujiDesk-v1.5.0/KujiDesk.exe，該版本未正確探測 Node.js 且無最新入場／通知邏輯。
- 在 manager.py 與 desktop.py 增加 ensure_playwright_node()，依序探測環境變數、PyInstaller 解壓目錄、虛擬環境 Lib/site-packages 及系統 Node.exe。
- 重新以 build_exe.py 編譯 KujiDesk.exe (v1.5.10)，--self-test 通過（playwright_driver 與 driver_working 均為 true）。
- 桌面捷徑更新指向 KujiDesk-v1.5.10/KujiDesk.exe，並將新版同步複製至 KujiDesk-v1.5.0。
- 桌面獨立控制台視窗已置前，瀏覽器網頁控制台已自動開啟。
`n付款逾時新增自動原箱重排：可見彈窗明確取消後單次確認，等待同PID列表、無隊伍、原箱仍有庫存才enter_queue；失敗uncertain不重送。來源已改，背景尚未重啟。
`nopen 逾時修正：recovering 持帳號鎖時，切回既有頁改在鎖外執行、8秒上限並還原視窗。64項回歸通過，尚未重啟套用。
`n2026-11-19：返回同PID選箱列表確認無隊伍後一律自動監看，不再限SoldOut原因；其他商品不啟動。更新EndViewing回歸，64項通過；執行中服務未重啟。
`n2026-11-19：A售完重排與inspect逾時，cancel_observer原本僅設Event等待task，頁面讀取阻塞時無法退出。改明確task.cancel並await，新增阻塞任務回歸，65項通過。執行中服務尚未套用，實站原因未完全確認。
`n2026-11-19：新增build_exe.py --share對外打包模式，獨立輸出KujiDesk-share且不產生本機runtime指標。65項回歸通過。
`n首頁載入30秒逾時改保留視窗與中文狀態，不彈原始錯誤、不自動重送；新增open逾時測試，66項通過。分享版重新打包。
`n還原cookies時context已關閉修復：清除失效連線並回closed、中文提示重開，不刪登入檔。新增回歸，67項通過；分享版重打包。
`n修復切回視窗CDP錯誤：最小化先normal再恢復最大化/全螢幕，新增順序回歸測試。分享版重新打包，現有服務尚未重啟。
`n手動關Chrome後重開修復：context close清除失效參照，檢查context身分避免延遲事件清掉新視窗。69項測試通過；分享版重新打包，現有服務未重啟。
`n使用者IMG_6538.jpg轉為logo.png/ico，替換Tk視窗與EXE圖示、更新桌面Kuji Desk捷徑圖示。桌面self-test通過；分享版重新打包。
`nLOGO外圍白底已改透明，更新logo.png/ico並重打包分享版，原始JPG保留。

## 2026-11-19 v1.5.11 啟動衝突
- 使用者啟動失敗截圖根因已查證：LocalAppData/KujiDesk/desktop.log為三次WinError10048；18766被既有workspace服務占用，workspace token能認證、LocalAppData token不能。
- service_runtime.py：active-runtime.json只記本機runtime路徑（無token），resolve_runtime須用Client.alive認證；GUI選擇可用服務runtime而非再開第二份。
- manager.main先bind_listener持有socket，成功後才建立Manager/更新panel-session；用web.SockSite啟動。重複服務啟動直接結束，不覆寫其他服務憑證，不彈GUI錯誤。移除print完整panel token URL。
- 已認證現有workspace服務並建立本機active-runtime線索供新UI重用；未重啟既有1.5.10服務（當時ABC closed）。UI及服務新版本1.5.11。
- 73測試通過（69舊+4 startup回歸），分享版build_exe.py --share重新打包。發布位置../KujiDesk-share/KujiDesk.exe；仍不附Runtime或本機pointer。

發布驗證：原KujiDesk-share/EXE正在使用導致覆蓋WinError5，已改版本化KujiDesk-share-v1.5.11。EXE自檢全部true，實際開啟新GUI v1.5.11，原服務仍可認證、ABC closed。桌面Kuji Desk.lnk由舊share改指向新版。沒有關閉舊GUI或重啟背景。分享資料夾僅EXE，無Runtime指標。
v1.5.13 修正單檔子程序共用解壓目錄：背景服務及通知各自解壓，並清除指向父程序暫存 Node 的環境設定。73 項回歸、環境檢查及 EXE 自檢退出通過。未重啟既有服務。
v1.5.14 已整合 Cloudflare 驗證暫停，74 項測試、判斷器自測及分享版 EXE 自檢通過。既有服務尚未重啟。
UI v1.5.15：帳號卡片新增手動開啟瀏覽器，A 系統預設、B Edge、C Brave。74 項回歸、模擬啟動分派與分享版自檢通過。背景服務相容版本維持 1.5.14。

v1.5.16：A／B／C 專用視窗改用已安裝的 Brave，仍由 Playwright 開啟可見視窗。各帳號新建 Brave 設定檔與登入備份，舊 Chrome 資料保留。Cloudflare 暫停既有自動流程，使用者在該 Brave 視窗手動驗證。75 項回歸通過，隔離 Brave 啟動與模擬驗證暫停通過，分享 EXE 自檢通過。未連實站測試排隊，未重啟現有服務。

