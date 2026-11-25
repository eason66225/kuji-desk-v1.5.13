# Kuji Desk

最新版為 **v1.5.20 Chrome 版**。

## 下載與來源

- [下載最新版 Windows 執行檔](https://github.com/eason66225/kuji-desk-v1.5.13/releases/tag/v1.5.20)
- [完整程式碼](source/)
- [操作說明](source/使用說明.md)
- [架構與已知問題](source/AI_CONTEXT.md)

先安裝 Google Chrome，再開啟 KujiDesk.exe。帳號 A／B／C 使用獨立 Chrome 設定檔；首次切換需各自登入。控制台關閉時仍可開啟專用視窗手動登入，需要監看時再開啟控制台。

## 原始碼

source/ 為本機現存完整來源的逐位元快照，包含 Python 程式、測試、網頁資源、擴充套件、歷史備份和文件。來源檔雜湊見 SOURCE-SHA256.json。

```powershell
cd source
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python desktop.py
```

打包入口為 `python build_exe.py --share`。現版透過 Playwright Chromium 的 chrome channel 開啟本機 Chrome。切回視窗會聚焦目前分頁，縮小使用瀏覽器視窗按鈕。

本次發布通過 Python 語法檢查及 Windows 打包。依使用者要求未執行離線測試，實站登入及排隊尚未驗證。

## 舊版保存

根目錄 KujiDesk.exe 為 v1.5.13 原始執行檔，SHA256SUMS.txt 為該檔校驗值。v1.5.13 對應的完整來源快照尚未找到。倉庫名稱沿用既有名稱，最新版來源位於 source/。

Runtime、登入設定檔、Cookie、控制台憑證、Discord Webhook 與本機執行記錄未納入。原始文件中的歷史版本紀錄應按當時版本閱讀。
