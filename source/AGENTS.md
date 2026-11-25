# Kuji 管理程式工作規範

## 現版優先（v1.5.34）

下方逐版條目保留作歷史參考；現版以 AI_CONTEXT.md 為準。使用 CDP 接管既有 Chrome，以 browserContextId 區分真實設定檔，不關閉外部 context；不使用專用 persistent profile。UI_VERSION=1.5.34、服務 VERSION=1.5.30。查箱為頁內 fetch；Cloudflare 通知與彈窗各自可選。發布至既有 GitHub，維持程式來源與分享 EXE 對應，排除所有 Runtime 與私人設定。


## 最短接手流程
1. 讀 `AI_CONTEXT.md`（架構、已驗證行為、待修問題）。使用介面問題查 `使用說明.md`。
2. 用 `rg` 定位相關函式，只讀相關段落；不要預設讀整份 HANDOFF、Runtime、聊天或 PrintLab 文件。
3. 用既有 venv，做最小必要修改與有意義的測試。來源碼、EXE、正在執行的服務是三個不同狀態。
4. 更新 `AI_CONTEXT.md` 的現況／待辦；重大決策再追加 HANDOFF。回覆變更、驗證、是否套用，使用繁體中文、簡短清楚。

## 操作邊界
- 保留使用者既有修改、設定與登入。不得擅自關閉專用瀏覽器、退出隊伍、重送排隊、重啟服務；先核對本次要求是否包含這些動作。舊次重啟同意不視為永久授權。
- 使用者要求修復時可檢查、改碼、測試、打包。若套用會中斷當前隊伍，準備好新版再詢問，或依使用者「稍後重啟」保留執行狀態。
- 進箱入口只提交一次；結果不明先讀回狀態，不自動再點。不得自動付款、購買確認或處理驗證碼。
- 看到商品頁可依使用者既有要求點「購入する」進選箱；需核對同商品。這不是付款授權。
- 暫時限制頁可按現有機制等待重試；遵守明確冷卻，不繞過限制／驗證。已排隊頁不得套用一般自動重整。
- 不把 Runtime、Cookie、個人資料、panel token、Discord Webhook 放入回覆、來源包、EXE、Git。只讀必要欄位，勿整份輸出設定。
- 此目錄屬附屬工具；不修改 PrintLab 設備、模型、列印流程，不批次暫存或提交父倉庫其他變更。

## 驗證與溝通
- 使用現有工具／應用 API；電腦操作先遵循當前可用的電腦操作指引，網址辨識被阻止時停止，不改走其他手段規避。
- 不把模擬測試說成實站成功，不把 UI 更新說成背景服務已更新。API 查籤目前實際是 HTTP GET HTML 解析，不能宣稱官方 JSON 庫存介面。
- GUI F5 只更新資料，不會重新載入 Python 原始碼。更換 UI 與重啟排隊服務分開處理。
- 用時間與實測耗時說明效能，不能只依體感保證更快。狀態與順位要重新讀，不照抄過時交接。

## 維護約定（v1.5.5）
- 事件使用event()寫入，保留at/message/pid/boxId/boxSeq，清除target前先記離箱結果；UI不可猜舊紀錄的箱號。
- 售完接續用獨立task取得帳號lock後呼叫既有leave_and_requeue，禁止在observer自身直接取消／等待自身；shutdown必須取消接續task。
- 空列表只有可辨識正常選箱頁才能成立，登入／限制回應不可當空列表。連續無箱計時用monotonic，非空列表歸零。
- 回歸：venv python -m unittest test_manager test_login_store test_notifications test_entry_tabs test_service_runtime；歷史UI改動另用隔離Tk驗證篩選／上一箱，不連線真實帳號。

- 入口設定用entry_url（首頁/商品頁/列表，可暫無PID）；真正抓列表仍用嚴格list_url。沒有PID不得拼箱頁、不得沿用其他商品。入場後從同站商品網址取得PID，首頁等待使用者選商品。
- 入場限制以entry_limited比對去空白後的明確文字；商品頁標題不可排除該訊號。recover_entry任務可用停止按鈕取消，不能因輪詢狀態重新啟動已停止的入場流程。

- 入場等待必須是begin_entry背景任務，不可讓本機open/start HTTP等完整入場循環。重整用帳號minSeconds/maxSeconds抖動、無次數上限，stop取消task；首頁/登入頁只等待操作，已排隊頁不進入場任務。

- 多分頁只在明確入場限制頁建立：同context原分頁+4新分頁；只能選一個同PID成功分頁進後續提交。只清理本次助手分頁，絕不遍歷context.pages全關。切換主分頁先解除舊close監聽，避免清理觸發帳號cancel。每個分頁各自依min/max隨機等待且可同時發請求；只有429/503冷卻共用，不再使用entry_reload_lock。新回歸另跑test_entry_tabs。
- 帳號重啟若遇recovering／entry_pending，須先在帳號lock外取消入場task，再取得lock關窗重開；避免與recover_entry持鎖互等。回歸看test_restart_api_cancels_entry_before_waiting_for_account_lock。
- 付款逾時僅辨識可見 customAlert 明確取消文案；單次確認返回同商品列表並核對無隊伍後，原箱有庫存才重排，失敗不重送。
- recovering 狀態切回既有視窗須在帳號 lock 外執行並限制等待時間，避免等待入場任務持鎖造成 open 逾時。
- 返回同商品正常選箱列表且無有效隊伍時，預設自動start重建監看基準；不限售完原因，其他商品不沿用設定。
- cancel_observer 必須取消並await舊task，不可只set Event後等待可能卡在瀏覽器讀取的task；保留current_task防護。
- 對外交付用 venv python build_exe.py --share，輸出版本化 KujiDesk-share-v<版本>；僅封裝EXE與公開使用說明，不附 KujiDesk.runtime.json 或 Runtime。
- 首次首頁導覽逾時或 net::ERR_ABORTED 時保留視窗、停止入場等待並提示手動確認。登入模式等待導覽 commit，不等待 DOM 解析。
- 還原登入cookies發生Playwright連線錯誤時，關閉失效context並清除page/context/entry_pending，回closed供重新開啟；不刪profile。
- Chrome 使用 Playwright bring_to_front 切回目前分頁。禁止使用 Chromium CDP；最小化請使用視窗自己的按鈕。
- context close用捕捉該context的回呼清空page/context/entry_pending；舊context延遲close不可清除新連線，page close不等同context close。
- 程式圖示資產為logo.png與logo.ico；native_ui載入PNG，build_exe使用ICO並將PNG納入單檔資源。

- 服務啟動先以service_runtime.bind_listener保留18766，再建立Manager／發布panel-session。不可在bind前覆寫憑證。GUI透過active-runtime.json線索加authenticated probe尋找已在執行的資料目錄；不能只相信線索檔。
- 新啟動回歸包含test_service_runtime：異runtime重用、損壞registry、重複bind與憑證不被覆寫。desktop.log不可寫含panel token的網址。

- 分享EXE若被使用中不可強制覆蓋或殺程序；改輸出版本化分享資料夾並更新既有Kuji Desk捷徑。

- 手動籤數更新沿用 NativeUI.batch(api_inventory)，只查可更新的箱子，不重整 Chrome。純 UI 更新只調 UI_VERSION，服務相容版本維持 VERSION。

- 單檔版啟動長駐服務或通知程序時，使用 background_environment()，讓子程序獨立解壓並重新尋找套件內的 Playwright Node。
- Cloudflare 驗證辨識使用 cloudflare_pause.py。遇到驗證時取消目前自動流程，保留原視窗與隊伍資料，例外不可當成一般重試。

- A／B／C 使用本機安裝的 Chrome，啟動 channel=chrome。各帳號用 `profiles-chrome/<帳號>` 與 `login-chrome/<帳號>.bin`。分享版只發行 EXE。Cloudflare 由使用者在專用視窗驗證。
- 帳號卡片使用「開啟／登入」與「切回視窗」操作專用 Chrome。控制台關閉後，「開啟／登入」啟動 login-only；後端限制此模式的動作與狀態，按「開啟控制台」後以 resume 沿用視窗。

- `browser-box-scan/` 是獨立 Chrome MV3 套件。使用 activeTab 與 session storage 管理單一選箱分頁，使用者開始後才用單次 alarm 排程 60–90 秒刷新。刷新限正常選箱列表，遇驗證、限制、離頁或找到新箱即停。新箱僅沿用網站提供的同商品箱頁連結，排隊由使用者確認。擴充套件 JS 用 `node --input-type=module --check` 從標準輸入檢查。

- `queue-flow-demo.html` 是獨立離線測試頁，以假資料驗證 2–3 秒抖動、找箱與手動／自動模擬排隊。可直接用瀏覽器開啟，驗證時使用隔離 Brave 並確認測試頁無網路請求。

- v1.5.21 改用 connect_over_cdp('chrome') 接現有工作階段。先由使用者在 chrome://inspect/#remote-debugging 啟用並授權。僅選一個本站分頁，同 context 不能同時交給兩張帳號卡；重連與 shutdown 不可 close 使用者的 context。

- v1.5.22 接管模式的查詢使用 Chrome 分頁。fetch_boxes 只重整同商品列表，庫存與順位讀現有 DOM。排隊頁不可套用列表重整，不再用 aiohttp 複製登入來查詢。

- v1.5.23 使用 launch_persistent_context(channel=chrome, headless=False)，A／B／C 各用 profiles-chrome/<ID>。登入由使用者手動操作，Chrome 設定檔持久保存。此版不使用 CDP 接管；shutdown 只關閉自己建立的 context。不要把登入設定檔上傳 GitHub。

- v1.5.24 以 CDP 連接既有 Chrome，逐頁 Target.getTargetInfo 的 browserContextId 區分真實 profile。A/B/C 綁定不同 profile ID，依視窗 ID 排序首次分配，開始前由使用者切回核對。禁止關閉外部 context；入場等待只用原頁，不能用共享 Playwright context.new_page 建跨設定檔分頁。

- v1.5.25 的 fetch_boxes 透過 page.evaluate(FETCH_BOX_HTML) 在每個真實 profile 的頁面發起同源 fetch，credentials=include、cache=no-store、15 秒上限。驗證回應網址/商品/HTTP/驗證訊號，查詢後再檢查停止及導覽，正常找箱不 reload 畫面。

- v1.5.26 恢復 entryRefresh 開關控制的五分頁。new_entry_page 由原頁 window.open 建頁並以 Target.getTargetInfo 核對 browserContextId，禁止用共享 context.new_page；僅取消／清理助手追蹤的頁面，429/503 明確冷卻共用，遇 Cloudflare 驗證暫停。

- v1.5.27 共用 browser_lock 串行建立 CDP 連線，授權等待60秒。open 先核對 browser.is_connected，disconnected 回呼清除舊引用與取消任務，舊 browser 的延遲回呼不得清除新連線。GUI open/restart 的 HTTP 等待需涵蓋排隊連線時間。

- v1.5.28 使用 chrome://profile-picker/ 讓使用者選 profile；只接受選擇後新增的空白／新分頁。從新頁 chrome://version 的 profile_path 讀取目錄名稱，存 job 的 chromeProfile；後續用 --profile-directory 開啟。以 CDP profile ID 阻止跨卡片重複綁定，官網既有隊伍頁優先沿用。不要記錄完整 profile_path。

- v1.5.29 設定檔綁定使用原生 profile-picker 由使用者選，再在總控確認 Local State 的 profile.last_used 對應名稱。確認後以明確 profileDirectory 開 nonce 標記分頁，辨識工作階段後沿用該 profile 的既有官網頁，避免只等新分頁而卡住。

- v1.5.30 綁定不依賴 CLI 開出的 nonce 分頁。掃描既有 CDP profile ID，在每個 profile 以原頁開短暫辨識頁讀 chrome://version 的 profile_path 目錄名稱後關閉，快取 ID->目錄並於斷線清除；既有官網頁不導航。

- v1.5.31 介面綁定使用明確的設定檔名稱／目錄下拉選單，不依賴 Local State 的 last_used；該值可能仍指向別張卡片。UI_VERSION=1.5.31，相容服務 VERSION=1.5.30；純介面修正不重啟正在監看的服務。

- v1.5.32 通知程序使用 check_cloudflare 既有的明確 note 與同訊息事件 at 辨識驗證；按帳號與事件時間去重，不套用一般重複通知，也不再發同次 uncertain 通知。支援 v1.5.30 服務，可僅換通知程序而保留監看／Chrome。通知測試必須明示為測試，不宣稱實際發生驗證。

- v1.5.34 的 Discord 設定增加 cloudflare_enabled（舊設定預設 true）及 cloudflare_popup（預設 false）；後者與 DC 啟用無關，只在 GUI 開啟時輪詢提示。兩者共用 notifications.cloudflare_event_key；提示為非模態 Toplevel，不阻塞輪詢，已提示事件寫入本機 cloudflare-popups.json，不能打包或上傳。
