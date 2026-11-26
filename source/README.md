# Kuji Desk · suto 1 ban kuji

Windows 桌面工具，用同一個總控管理最多三個已登入的一番賞 Chrome 設定檔。
目前來源／最新分享版為 **v1.5.37**，內含服務 **v1.5.37**；本機服務仍為 **v1.5.30**，僅通知程序已更新36。GitHub公開版仍為 **v1.5.34**。套用狀態見 [AI_CONTEXT.md](AI_CONTEXT.md)，模組與資料流見 [架構說明](ARCHITECTURE.md)。

## 開始使用

執行分享版 `KujiDesk.exe`，依照 [使用說明](使用說明.md) 啟用 Chrome 遠端偵錯、綁定設定檔，再設定商品網址與監看間隔。不需要安裝 Python。

## 現有功能

- A／B／C 綁定不同的既有 Chrome 設定檔，沿用瀏覽器登入。
- 以設定檔名稱及目錄明確選取，避免依最後使用的設定檔誤綁。
- 正常列表由分頁內同源 fetch 取得 HTML，依可儲存的最短／最長秒數隨機監看新滿箱；不是整頁 F5，也不是官方 JSON 庫存 API。
- 找到箱子後走既有網站排隊流程；順位、剩餘籤數與各賞庫存顯示在卡片。
- 明確入場限制時可使用同帳號五分頁等待，各頁獨立隨機刷新；成功後保留一頁、清理助手建立的其他頁。
- 售完接續監看、離箱重排、批次更新籤數與執行歷史紀錄。
- Discord Webhook 設定、順位門檻、重複提醒，以及可分開勾選的 Cloudflare DC 通知／本機提示。
- Cloudflare 驗證由本人手動完成；程式暫停自動操作，不自動付款。

## 開發與打包

建議使用與現有打包環境一致的 Python 3.13；依賴版本見 `requirements.txt`。

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python desktop.py
```

打包另需安裝 PyInstaller（現有環境使用 6.22.3）：

```powershell
.venv/Scripts/python -m pip install pyinstaller==6.22.3
.venv/Scripts/python build_exe.py --share
```

產物為上一層 `KujiDesk-share-v1.5.37/KujiDesk.exe`。使用已安裝的 Google Chrome，不需下載 Playwright 的 Chromium。

既有回歸入口：`python -m unittest test_manager test_login_store test_notifications test_entry_tabs test_service_runtime`。部分測試仍反映舊瀏覽器契約，不能宣稱最新版全套通過；依使用者要求，近期沒有執行離線／模擬測試。現版已做語法檢查、打包、實際 Chrome 查箱及介面檢查、Discord 實際傳送測試；完整驗證範圍見 [AI_CONTEXT.md](AI_CONTEXT.md)。

舊的 `web/`、`browser-box-scan/`、研究工具與 `.bak` 檔保留供追溯；桌面版主入口是 `desktop.py`。舊網頁介面和獨立擴充套件不代表目前桌面功能。
