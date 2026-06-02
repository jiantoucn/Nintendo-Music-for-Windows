# Changelog

所有重要更改均记录在此文件中。

## [v2.2.0] - 2026-06-02

### 新增

- 防止应用多开：使用 Windows Mutex 检测单实例
- 多开时弹出对话框，询问用户是否关闭前一个实例并重新打开
- 支持中英文弹窗提示（跟随系统语言或手动设置）

---

## [v2.1.0] - 2026-06-02

### 修复

- Cookie 持久化：关闭隐私模式，登录状态跨会话保留

### 新增

- About 对话框显示版本号 `v2.1.0`
- 语言切换功能（设置 > 语言：跟随系统 / 中文 / 英文）
- 软件名称改为 `Nintendo Music for Windows`

---

## [v2.0.1] - 2026-06-02

### 修复

- 移除 `create_window()` 不支持的 `icon` 参数，改为通过 `webview.start(icon=...)` 设置图标

---

## [v2.0.0] - 2026-06-02

### 重大升级

- 完整中英文本地化（自动检测系统语言）
- 菜单系统重构：
  - 菜单名根据语言显示"设置"或"Settings"
  - 子菜单 + 勾选状态实时更新
  - 新增"关于"对话框（含 LOGO 和开发者信息）
  - 新增"退出"按钮
- 后台运行修复：使用 `window.hide()` + pystray 托盘
- 登录弹窗修复：禁用 `OPEN_EXTERNAL_LINKS_IN_BROWSER`
- LOGO.png 作为 exe 图标和 About 对话框展示

---

## [v1.1.1] - 2026-06-02

### 修复

- 修复 `webview` 模块未找到问题：使用 Python 3.14 重新打包

---

## [v1.0.1] - 2026-06-02

### 修复

- 修复 `ModuleNotFoundError: No module named 'webview'`：统一 Python 版本打包

---

## [v1.0.0] - 2026-06-02

### 初始版本

- 浏览器套壳访问 https://music.nintendo.com/
- 域名限制：仅允许访问 nintendo.com 及其子域名
- 单文件 exe 打包
