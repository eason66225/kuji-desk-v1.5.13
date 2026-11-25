# v1.5.11 啟動修復完成
目標：修復Kuji Desk無法啟動。
原因：分享版預設LocalAppData runtime與workspace服務runtime不同，認證不到已在18766執行的服務而重複啟動，觸發WinError10048。舊startup在bind前寫token也有競態風險。
完成：新增service_runtime.py認證式runtime尋址、綁定socket後才發布憑證；GUI重用既有runtime；移除token URL日誌。版本1.5.11。
驗證：73項unittest通過，EXE self-test全true。實際新GUI v1.5.11已開，舊服務原樣保留、ABC closed。未開瀏覽器或重排。
交付：../KujiDesk-share-v1.5.11/KujiDesk.exe，資料夾僅EXE；桌面Kuji Desk.lnk已更新。
注意：舊share EXE正在用，不能覆蓋，所以採版本化目錄。現有服務仍1.5.10，啟動前綁定的新保護下次新服務啟動才生效。
下一步：使用者用新版介面；不要自動關舊GUI、重啟服務或操作隊伍。無阻礙。
