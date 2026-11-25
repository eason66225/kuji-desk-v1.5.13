# Kuji Desk · suto 1 ban kuji

目前 Windows 分享版與桌面介面為 **v1.5.34**，服務相容版本 **v1.5.30**。管理最多三個本人已登入的 Chrome 設定檔，監看新滿箱、接續網站排隊，顯示順位與剩餘籤數。

- [下載 Windows 分享包](https://github.com/eason66225/kuji-desk-v1.5.13/releases/tag/v1.5.34)
- [第一次使用教學](source/使用說明.md)
- [完整來源與開發命令](source/README.md)
- [架構、驗證範圍與 AI 接手](source/AI_CONTEXT.md)
- [版本整理](CHANGELOG.md)

## 第一次使用

1. 安裝並更新 Google Chrome；解壓分享包，執行 KujiDesk.exe。
2. 每個帳號用不同 Chrome 設定檔登入一番賞。先開啟各設定檔的網站分頁。
3. 開啟 chrome://inspect/#remote-debugging，啟用遠端偵錯；連線提示由本人允許。
4. 在帳號卡片連接 Chrome，從下拉選單選擇相同的設定檔名稱與目錄；先完成一張，再綁下一張。
5. 設定商品網址、目標籤數、最短／最長監看秒數，儲存後開始監看。
6. DC 通知請填自己的 Webhook；Cloudflare DC 提醒與本機彈窗可分別勾選。驗證、購買確認與付款由本人處理。

一般查箱使用已登入分頁內的同源 fetch 解析 HTML，不會整頁 F5，也不是官方 JSON 庫存 API。關閉桌面視窗不代表退出網站隊伍；完整注意事項見使用說明。

## 本次整理

保留現有功能，更新 Chrome 連接、設定檔明確綁定、五分頁入場等待與 Cloudflare 通知說明。SOURCE-SHA256.json 可核對 source/ 全部來源檔。桌面分享包附使用說明與 SHA256 校驗值；不包含作者的 Runtime、登入、Webhook 或通知偏好。

已完成語法檢查、打包、本機 Chrome 查箱與介面驗證、實際 Discord 測試。尚未在另一台電腦驗證首次使用，也未完成五分頁通過與 Cloudflare 提示的實際觸發驗證；近期未跑離線／模擬測試，不能視為完整回歸通過。

## 舊版保存

根目錄 KujiDesk.exe 是 **v1.5.13 原始保存檔**，不是最新版；SHA256SUMS.txt 為其校驗值。對應 v1.5.13 的完整來源快照尚未找到。倉庫名稱沿用既有名稱，最新版程式碼位於 source/，新版執行檔請至 Releases 下載。
