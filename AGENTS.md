# 專案維護

- 最新來源在 source/；先讀 source/AGENTS.md、source/AI_CONTEXT.md。根目錄 KujiDesk.exe 僅保存 v1.5.13，新版 EXE 放 GitHub Release，不覆蓋舊檔。
- 現版 UI／分享包 1.5.34，服務相容 VERSION=1.5.30。source/ 保留既有歷史備份與研究工具，桌面入口 desktop.py。
- 在 source/ 建立 .venv，安裝 requirements.txt；語法檢查用 python -m py_compile，分享打包 python build_exe.py --share（另需 PyInstaller）。詳細命令與驗證限制見 source/README.md；近期依使用者要求不執行離線測試。
- 更新來源後重新計算 SOURCE-SHA256.json，發布前比對 Python 原碼與本機來源、檢查私密設定排除、核對 EXE 雜湊。同步使用說明、CHANGELOG 及 release notes。
- 不提交 Runtime、Cookie、Webhook、Chrome 設定檔、憑證、個人執行紀錄；不得因發布而中斷目前監看或隊伍。
