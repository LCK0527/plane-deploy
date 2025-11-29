# 修復頁面卡頓問題

## 原因
前端可能還在編譯，或者太多套件在 watch 模式運行。

## 解決方案

### 方案 1: 等待編譯完成
- 查看前端終端，等待看到 `✓ Compiled` 訊息
- 通常需要 1-2 分鐘

### 方案 2: 重啟前端（如果卡太久）
1. 在前端終端按 `Ctrl+C` 停止
2. 重新運行：`cd apps/web && pnpm dev`
3. 等待編譯完成

### 方案 3: 清理並重建（如果還是卡）
```bash
# 停止前端
# 然後運行：
cd "/Users/philip/Desktop/Linux Final Project/Plane/apps/web"
rm -rf .next
pnpm dev
```

### 方案 4: 檢查是否有太多 dev 進程
如果之前運行了 `pnpm dev` 在根目錄，可能會啟動所有套件的 watch 模式，導致卡頓。

**只運行前端：**
```bash
cd "/Users/philip/Desktop/Linux Final Project/Plane/apps/web"
pnpm dev
```

**不要運行：**
```bash
cd "/Users/philip/Desktop/Linux Final Project/Plane"
pnpm dev  # 這會啟動所有套件，很慢
```

