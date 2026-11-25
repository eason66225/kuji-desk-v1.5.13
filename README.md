# Kuji Desk

原始執行檔備份與完整來源，供程式碼審查及問題討論。

## 版本與檔案

| 位置 | 內容 |
| --- | --- |
| `KujiDesk.exe` | 原樣保留的 v1.5.13 Windows 執行檔 |
| `SHA256SUMS.txt` | v1.5.13 EXE 的 SHA-256 |
| [source-v1.5.19](source-v1.5.19) | 本機現存完整來源，版本為 v1.5.19 |
| `SOURCE-SHA256.json` | 各來源檔的 SHA-256 |

v1.5.13 對應的完整來源快照目前未找到。來源資料夾保留備份當下的檔案內容與歷史來源備份，逐檔核對雜湊後上傳。此處的來源和根目錄 EXE 分屬上表列出的版本。

## 程式碼入口

- [manager.py](source-v1.5.19/manager.py) 管理帳號、網站狀態、找箱及排隊流程。
- [native_ui.py](source-v1.5.19/native_ui.py) 提供桌面介面和服務控制。
- [desktop.py](source-v1.5.19/desktop.py) 是桌面執行入口。
- [details.py](source-v1.5.19/details.py) 解析箱子與庫存。
- [notifications.py](source-v1.5.19/notifications.py) 處理 Discord 通知。
- [AI_CONTEXT.md](source-v1.5.19/AI_CONTEXT.md) 提供架構、已知問題及交接資料。

來源內也附有測試、前端資源、擴充套件、requirements.txt、build_exe.py、操作說明和歷史文件。歷史說明中的實測狀態請按記錄版本閱讀。

## 原始碼啟動

在 source-v1.5.19 內建立 Python 虛擬環境並執行以下命令。

```powershell
python -m pip install -r requirements.txt
python -m playwright install firefox
python desktop.py
```

現版使用 Playwright 專用 Firefox。首次登入由使用者在各帳號的專用視窗完成。Windows 打包入口為 `python build_exe.py --share`。v1.5.13 EXE 直接在 Windows 開啟，功能依該版執行結果為準。

## 此次保存

此次僅複製及上傳，未變更程式邏輯、重建 EXE 或執行網站流程。Runtime、Cookie、登入設定檔、Discord Webhook、控制台憑證及本機記錄未納入。問題回報請提供使用的版本、觸發步驟及錯誤訊息。
