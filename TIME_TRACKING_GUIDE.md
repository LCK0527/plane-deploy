# Time Tracking 功能使用指南

## 📍 功能位置

Time Tracking 功能位於 **Work Item (工作項目) 的詳細頁面側邊欄**。

## 🚀 如何啟用 Time Tracking

### 步驟 1: 進入專案設定
1. 點擊左側邊欄的專案名稱（例如 "Testing 1129"）
2. 點擊 **"Settings"** 或直接訪問：`/{workspaceSlug}/settings/projects/{projectId}/features`

### 步驟 2: 啟用 Time Tracking
1. 在 **"Other Features"** 區塊找到 **"Time Tracking"**
2. 切換開關啟用此功能
3. 功能啟用後，所有該專案的工作項目都會顯示 Time Tracking 小工具

## 📝 如何使用 Time Tracking

### 在 Work Item 詳細頁面：

1. **打開任何 Work Item**
   - 從專案頁面點擊任何工作項目
   - 或從 "Your work" 頁面選擇工作項目

2. **找到 Time Tracking 區塊**
   - 在右側邊欄（Sidebar）中
   - 標題為 "Time Tracking"，帶有 ⏱️ 圖示

3. **使用功能：**

   **a) 啟動計時器（Timer）**
   - 點擊 **"Start Timer"** 按鈕
   - 計時器會開始計時，顯示已用時間
   - 點擊 **"Stop Timer"** 停止計時
   - ⚠️ 每個工作項目同時只能有一個活躍的計時器

   **b) 手動記錄時間（Manual Entry）**
   - 點擊 **"Add Time"** 按鈕
   - 輸入時間（以分鐘為單位）
   - 可選：添加備註（Note）
   - 點擊 **"Add"** 保存

   **c) 查看時間摘要**
   - **Total Logged**: 總記錄時間
   - **Estimated**: 預估時間（如果已設定）
   - **Recent Entries**: 最近的時間記錄列表

   **d) 刪除時間記錄**
   - 在 "Recent Entries" 列表中
   - 點擊記錄旁邊的 🗑️ 圖示
   - 只能刪除自己創建的記錄

## 🎯 功能特點

- ✅ **即時計時器**: 開始/停止計時，自動計算時間
- ✅ **手動記錄**: 可以手動輸入已完成的時間
- ✅ **時間摘要**: 查看總時間、預估時間、按用戶分組的時間
- ✅ **備註功能**: 為每個時間記錄添加備註
- ✅ **多用戶支援**: 每個用戶可以獨立記錄時間
- ✅ **權限控制**: 只有記錄的創建者可以刪除自己的記錄

## 📊 API 端點（給開發者）

### 工作項目時間記錄
- `GET /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/` - 獲取所有時間記錄
- `POST /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/` - 創建手動記錄
- `PATCH /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/{id}/` - 更新記錄
- `DELETE /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/{id}/` - 刪除記錄

### 計時器控制
- `POST /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/start/` - 啟動計時器
- `PUT /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/stop/` - 停止計時器
- `GET /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/active/` - 獲取活躍計時器

### 時間摘要
- `GET /api/workspaces/{slug}/projects/{projectId}/work-items/{issueId}/time-entries/summary/` - 獲取時間摘要

### 時間報告（Analytics）
- `GET /api/workspaces/{slug}/time-reports/summary/?group_by=user|work_item|project|module` - 獲取時間報告
- `GET /api/workspaces/{slug}/time-reports/export/` - 導出 CSV

## 🔧 技術細節

- **資料庫模型**: `TimeEntry` (在 `apps/api/plane/db/models/issue.py`)
- **前端組件**: `IssueTimeTrackingProperty` (在 `apps/web/core/components/issues/time-tracking/property.tsx`)
- **API 服務**: `TimeEntryService` (在 `apps/web/core/services/issue/time_entry.service.ts`)
- **功能開關**: `is_time_tracking_enabled` (專案級別設定)

## ⚠️ 注意事項

1. **功能必須先啟用**: 在專案設定中啟用 Time Tracking 後，功能才會顯示
2. **權限要求**: 
   - 查看時間記錄：所有成員
   - 創建/編輯/刪除：需要 Member 或 Admin 權限
3. **計時器限制**: 每個用戶在每個工作項目上同時只能有一個活躍的計時器
4. **時間格式**: 手動輸入以分鐘為單位，顯示時會自動轉換為小時和分鐘

## 📸 截圖位置

Time Tracking 小工具會出現在：
- Work Item 詳細頁面的右側邊欄
- 在 "Labels" 區塊下方
- 在 "Additional Properties" 區塊上方

