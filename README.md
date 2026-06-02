# Nintendo Music for Windows

一个基于 WebView2 的 Nintendo Music 桌面客户端，提供接近原生的桌面体验。

## 功能特性

- 默认打开 https://music.nintendo.com/
- 仅允许访问 `nintendo.com` 及其子域名
- 登录页面在应用内打开，不跳转系统浏览器
- Cookie 持久化，登录状态跨会话保留
- 媒体键支持（暂停/播放、上一曲、下一曲）
- 系统托盘后台运行
- 可选开机自启
- 中英文界面自动适配（支持手动切换）
- About 对话框展示版本和开发者信息

## 菜单结构

```
设置
├── 返回主页
├── 清除 Cookies 和缓存
├── 开机自启          (ON / OFF)
├── 后台运行          (ASK / Always / Never)
├── 语言              (跟随系统 / 中文 / 英文)
├── 关于
└── 退出
```

## 构建

```bash
pip install pywebview pyinstaller pynput pystray Pillow
pyinstaller --onefile --windowed --name "NintendoMusic" --icon icon.ico --add-data "LOGO.png;." --add-data "icon.ico;." main.py
Rename-Item "dist\NintendoMusic.exe" "Nintendo Music for Windows.exe"
```

## 依赖

- Python 3.14+
- pywebview 6.x
- pythonnet
- pynput
- pystray
- Pillow

## 许可证

此软件由 Sayaka 开发，使用 Trae CN 配合 MiMo-V2.5-Pro 开发。
