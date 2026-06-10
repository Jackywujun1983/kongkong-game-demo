# 前端 UI 原型审核说明

## 原型入口

- 本地文件：`frontend/ui-prototype.html`
- 浏览器地址：`file:///E:/Codex_Space/PythonDemo/frontend/ui-prototype.html`

## 设计方向

本次原型不覆盖现有 `preview.html` 和 `detail.html`，用于先审核视觉风格和信息布局。

整体采用当前主流的游戏库界面结构：

- 顶部：品牌、搜索、当前版入口、详情页入口。
- 左侧：游戏类型筛选，展示类型名称和数量。
- 中间：焦点游戏位、数据统计、游戏库卡片、分页。
- 右侧：当前选中游戏的详情预览，展示封面、类型、大小、年份、工作室和下载地址。

## 审核重点

- 首页整体视觉风格是否符合预期。
- 游戏卡片的信息密度是否合适。
- 左侧分类和右侧详情预览是否方便浏览。
- 焦点游戏位是否需要保留或调整。
- 当前深色游戏库风格是否作为最终方向。

## 后续落地

审核确认后，再将原型方案拆分合并到：

- `frontend/preview.html`
- `frontend/detail.html`
- `frontend/public/site.css`
- React 源码中的游戏卡片和详情组件
