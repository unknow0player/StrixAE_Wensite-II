# StrixAE 网页与音频管理后台

本项目包含 StrixAE 展示网站、Python 音频管理后台和频谱绘图脚本。展示页保留原布局，通过后台替换指定样本的音频后，自动生成并更新对应频谱图片。

## 公开前端

- 网站首页：https://unknow0player.github.io/StrixAE_Wensite-II/
- 音频展示：https://unknow0player.github.io/StrixAE_Wensite-II/StrixAE-Website/demo.html

GitHub Pages 使用 `main` 分支的根目录发布。根目录 `index.html` 自动进入 `StrixAE-Website/index.html`，`.nojekyll` 禁用 README 的 Jekyll 页面生成。访客无需登录即可浏览前端、播放仓库中的示例音频。

公开前端展示仓库内的静态音频和图片。**本机后台上传的内容不会自动同步到 GitHub Pages**；要让访客看到新内容，需将对应的音频、图片与页面引用更新并推送到仓库，或另行部署可公开访问的 Python 后端。GitHub Pages 不提供管理员登录入口。

## 管理员如何进入后台

1. 下载或克隆整个仓库并解压。保留 `StrixAE-Website`、`backend` 和 `plot_specs.py` 的相对位置。
2. 安装 Python 3.11–3.13，并勾选 Add Python to PATH。
3. Windows 用户双击 `backend/start.bat`。首次运行会创建虚拟环境并安装依赖，请保持窗口开启。
4. 在运行服务的同一台电脑打开 **http://127.0.0.1:8000/admin**。
5. 首次启动自动生成密码，打开本机 `backend/data/admin-password.txt`，复制密码登录。密码不会随代码上传到 GitHub，也不是 GitHub 登录密码。
6. 选择 Sample 和音频位置，上传音频，等待生成完成。展示页地址是 **http://127.0.0.1:8000/demo.html**，主页是 **http://127.0.0.1:8000/**。

管理员可预览音频和频谱、恢复历史版本或恢复某个位置的原始内容。按 Ctrl+C 停止服务，重新启动后上传记录仍保留。

## GitHub 仓库与在线网站的区别

**将代码上传到 GitHub 不会自动启动 Python 后端。** 本项目默认只允许在运行服务的电脑上访问。其他人打开自己的 `127.0.0.1` 不会连接到你的电脑。

GitHub Pages 只能托管静态网页，不能运行此项目的 Python 上传和绘图功能。如需所有人在线访问网站、管理员远程上传音频，需要另外部署支持 Python 的服务，并配置域名、HTTPS、访问限制和持久化存储。当前仓库不代表已完成公网部署。

直接双击 HTML 文件会显示原始静态内容；要查看后台上传后的音频，请使用服务提供的 HTTP 地址。

## 项目结构

```text
StrixAE-Website/       原有前端、示例音频和图片
backend/
  app.py              Web 服务、上传、登录与历史版本接口
  spectrogram.py      复用原绘图脚本生成频谱
  static/             管理页面与展示页数据脚本
  tests/              自动化测试
  requirements.txt    Python 依赖
  start.bat           Windows 启动入口
  README.md           详细操作、备份与排错说明
plot_specs.py         原始 STFT 频谱绘图代码
```

## 频谱与上传规则

- 按原 `plot_specs.py` 的 STFT 和分贝转换方式绘图，不另行计算 Mel 频谱。
- Mixture 的原布局没有图片位置，生成图仅在后台预览；另外三个位置同步更新音频和图片。
- 支持 WAV、FLAC、OGG、MP3，最多 25 MB、120 秒，采样率 8–96 kHz，单声道或双声道。
- 每个位置独立更新，不执行模型推理、不自动对齐音频长度。
- 上传失败保留当前内容，历史版本存放在本机 `backend/data`。

## 数据与密码

仓库不包含虚拟环境、上传数据库、历史媒体、管理员密码、会话密钥或日志。不同电脑首次启动时会生成各自的数据和密码。

备份时先停止服务，再复制整个 `backend/data` 文件夹；不要把它上传到公开仓库。忘记密码时，停止服务，删除本机 `backend/data/admin-password.txt` 和 `backend/data/session.key`，重新启动生成新密码。

完整说明见 [后台使用文档](backend/README.md)。
