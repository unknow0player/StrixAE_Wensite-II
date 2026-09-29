# StrixAE 本地音频管理后台

## 启动和使用

1. 安装 Python 3.11–3.13，并勾选 Add Python to PATH。本机已经准备好运行环境。
2. 双击本文件夹的 `start.bat`，保持启动窗口开启。首次使用会按需安装依赖，需要网络。
3. 打开管理后台：http://127.0.0.1:8000/admin 。首次启动后，打开 `data/admin-password.txt` 并复制密码登录。
4. 选择 Sample 1–3 和 Mixture / Ground Truth / TF-GridNet / StrixAE，选择音频，点击“上传并更新展示页”。
5. 等待成功提示，打开 http://127.0.0.1:8000/demo.html 查看。已打开的展示页每 10 秒检查更新，切回页面也会更新。
6. 停止服务：在启动窗口按 Ctrl+C。再次启动后，上传记录仍然保留。

**必须通过上述 http 地址查看上传后的内容。** 双击 `StrixAE-Website/demo.html` 使用 file 地址时仍显示原始静态内容。GitHub Pages 等纯静态托管不能运行 Python 后端。

## 频谱与页面

- 不修改展示页的布局、样式或其他页面。仅在 demo.html 末尾增加数据脚本入口，所有后端代码和管理界面放在 backend。
- `spectrogram.py` 直接导入项目根目录 `plot_specs.py` 的 `plot_spec`，原文件保持不变。
- 计算完全沿用原脚本：librosa.load(sr=16000)、STFT 默认 n_fft=2048、win_length=600、hop_length=50、amplitude_to_db(abs(stft))。800×800 PNG，沿用无坐标轴的原绘图风格。
- 按你的要求不计算 Mel 频谱；页面原有 `.mel` 容器名称保留。
- Mixture 原来没有图片位置，生成图只在后台预览；另外三个位置同时更新音频和图。
- 支持 WAV、FLAC、OGG、MP3（由 SoundFile 解码，损坏或不支持的编码会提示）。上限 25 MB、120 秒、8–96 kHz、1–2 声道。
- 为统一浏览器播放，保存为 PCM 24-bit WAV，保持原采样率、声道和时长。绘图使用上传源文件，以复用原脚本处理方式。源文件名作为记录保留，原上传二进制不会归档。
- 这里只管理已生成的音频，不运行 TF-GridNet 或 StrixAE 推理。四个位置独立上传，不自动对齐时长。

## 数据和恢复

- `data/library.sqlite3`：当前版本、上传历史和音频信息。
- `data/media/<版本编号>/`：每版的 audio.wav 和 spec.png。发布使用新地址，避免浏览器缓存旧图。
- 先完成音频校验和绘图，再提交数据库；失败时保留上一个成功版本。历史文件不覆盖原始 Audios/figs。
- 后台可恢复任意历史版本，或恢复当前选中位置的原始页面内容。恢复不会删除历史文件。
- **备份**：先停止后台，再复制整个 `data` 文件夹到其他位置；恢复时停止后台，用备份替换 data，再启动。完整迁移需同时复制 backend、StrixAE-Website 和根目录 plot_specs.py；`.venv` 可以重新创建。
- 历史版本会持续占用磁盘，当前版本没有自动清理功能。不要手动删除正在使用的媒体文件。
- 忘记密码：停止后台，删除 `data/admin-password.txt` 和 `data/session.key`，重启会生成新密码并使旧登录失效。
- `data/server.log` 记录错误和更新操作，自动轮转保留 3 个旧日志。

## 运行范围与排错

默认只监听本机 127.0.0.1:8000，使用 Waitress。具备管理员登录、8 小时会话、CSRF 校验、登录限速、上传限制、文件类型和音频内容校验、路径限制。不要将 data、密码、日志或整个 backend 当静态文件公开。若以后需要公网部署，还需要按部署环境配置 HTTPS、域名、身份认证和备份策略。

- 页面没有更新：确认使用 http 地址，检查后台上传是否成功；刷新展示页。
- 首次绘图较慢：librosa/Numba 初始化可能耗时，等待完成；处理期间另一次上传会返回忙碌提示。
- 端口被占用：关闭之前的后台窗口，再启动。
- 安装依赖失败：在 backend 打开终端，执行 `.venv\Scripts\python.exe -m pip install -r requirements.txt`，查看具体错误。
- 启动失败：确认上一级目录保留 `plot_specs.py` 和 `StrixAE-Website`，并检查启动窗口的报错。

## 开发验证与接口

在 backend 运行 `.venv\Scripts\python.exe -m unittest discover -s tests -v`。测试使用临时数据，不改真实上传记录。

公开只读接口：`GET /api/health`、`GET /api/samples`、`GET /media/<id>/audio.wav` 或 `spec.png`，音频支持 Range 请求。

登录流程：`GET /api/session` 获取 CSRF，携带返回的 Cookie 和 `X-CSRF-Token`，`POST /api/login` JSON `{ "password": "..." }`。登录成功后使用新 CSRF。

管理员接口：`GET /api/slots/<sample>/<role>/history`；`POST .../upload` multipart 字段 file；`POST .../restore` JSON `{ "version_id": "历史编号" }`，null 表示恢复原始内容；`POST /api/logout`。所有写操作要求 CSRF，角色值为 mixture、ground_truth、tf_gridnet、strixae。
