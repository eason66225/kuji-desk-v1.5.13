# Kuji Desk AI 接手摘要

更新：2026-11-25。先讀本檔及 AGENTS.md；舊版決策查 HANDOFF.md，操作查 使用說明.md。

## 現版與架構

- 桌面 UI／分享包 v1.5.34；服務相容版本 VERSION=1.5.30。勿將這兩種版本視為不一致故障。
- 來源入口 desktop.py；manager.py 管理本機 18766 認證 API、帳號與任務；native_ui.py 為 Tk 桌面介面；notifications.py 為獨立 DC 通知程序。
- 依賴為 aiohttp 3.14.5、Playwright 1.65.2、BeautifulSoup 4.15.0。Windows 打包環境 Python 3.13.1、PyInstaller 6.22.3。
- 使用者啟用 Chrome 遠端偵錯並允許連線後，用 connect_over_cdp('chrome', timeout=60000) 接管既有 Chrome；不是無頭模式，也不另外啟動專用 profile。
- Chrome 多個真實設定檔可能只呈現一個 Playwright context。逐頁 Target.getTargetInfo 的 browserContextId 才能區分 profile；外部 context 不可關閉。

## 主要機制與陷阱

- 綁定：GUI 從 Local State 的 info_cache 顯示明確名稱／目錄下拉清單，預設不選；禁止以 last_used 代替本人選取。B 曾因讀到 A 的 Default 被判定重複。
- pick_chrome_page 掃描開啟中的 profiles，用短暫 chrome://version 頁辨識 profile_path 的目錄名稱，快取 profile ID→目錄，斷線清除。既有網站頁不導航；重複綁定拒絕。
- 原生 profile-picker 為 browser_ui target。選既有視窗未必產生新 page；CLI 帶 nonce 開頁也不可靠，不能用其作唯一完成訊號。
- 共用 CDP 連線以 browser_lock 串行建立；disconnected 清引用及取消任務，舊回呼不得清除新連線。GUI open 的等待涵蓋授權時間。
- fetch_boxes 用 page.evaluate(FETCH_BOX_HTML) 發同源 fetch，credentials=include、cache=no-store、15 秒 AbortController。核對回應 URL／商品／HTTP／驗證訊號，再解析 HTML；精確比對籤數，不能用 includes。
- 正常找箱不整頁 reload；庫存／順位從頁面 DOM／網站訊號讀取。不可宣稱官方 JSON API 或把失敗讀取當 0。
- 五分頁只用於明確一時入場限制並受 entryRefresh 控制，各頁依 minSeconds/maxSeconds 抖動；429/503 明確冷卻共用，首個同商品成功頁接續。
- new_entry_page 必須從原 profile 分頁 window.open 並核對 browserContextId；共享 context.new_page 會建錯 profile，Target.createTarget 指定一般 profile ID 也不支援。只清理本次助手追蹤的頁面。
- 排隊提交一次，結果不明讀回；不自動付款、處理驗證或重送。外部 Chrome 在服務關閉後保留。
- Cloudflare 暫停 note 為固定訊息。notifications.cloudflare_event_key 由該 note 與同訊息事件 at 產生每次驗證的鍵。
- cloudflare_enabled 預設 true，cloudflare_popup 預設 false，存於本機 discord.json。DC 與本機提示分開勾選；提示只在 GUI 開啟時生效，非模態 Toplevel，不阻塞輪詢。
- DC 與本機提示各自去重；本機 cloudflare-popups.json 不可打包。關閉 Cloudflare DC 通知也不應轉發成一般 uncertain 通知。
- 「已通過入場限制」事件仍可選；作者目前僅在本機關閉。不要將 Runtime 偏好複製到來源或分享包。

## 已驗證與待驗證

已驗證：Python 語法、Windows EXE 打包、實際多 profile Chrome 連接、分頁內 fetch HTTP 200／100 箱且 timeOrigin 不變、同 profile window.open、v1.5.34 設定頁兩勾選項與儲存鈕可見、實際 Discord 測試 HTTP 200。換 GUI／通知程序時保留 v1.5.30 服務及網站任務。

未驗證：其他電腦首次使用、五分頁入場通過後的完整流程、新 Cloudflare DC／彈窗的實際挑戰觸發。舊瀏覽器架構的測試契約部分過時；依使用者要求近期未跑離線測試，不得宣稱現版全套回歸通過。

## 維護命令

本機開發來源使用既有 ../../Runtime/kuji-manager/venv/Scripts/python.exe；可攜來源按 README 建立 .venv。

- 語法：python -m py_compile manager.py native_ui.py notifications.py desktop.py build_exe.py
- 歷史回歸入口（本輪未跑）：python -m unittest test_manager test_login_store test_notifications test_entry_tabs test_service_runtime
- 分享打包：python build_exe.py --share
- 請區分來源、打包版本與實際執行服務；本次 GitHub 整理不重啟任何服務或瀏覽器。

Runtime 含 Cookie、通知設定與控制台 token，只讀必要欄位。關閉／重啟會影響隊伍時先核對授權；不得分享 Runtime 或整份設定。
