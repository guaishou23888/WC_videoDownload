# WC_videoDownload - 微信视频号视频下载器

一个轻量级的微信视频号视频下载工具，采用两步解析法获取视频直链，无需登录、无需证书、无需修改代理。

## ✨ 特性

- **零配置**：无需安装证书，无需登录微信
- **在线解析**：复用公开解析服务，无需自建服务器
- **多编码支持**：同时提供 H.264（兼容版）和 H.265（省空间版）
- **进度显示**：实时显示下载进度和预计大小
- **完整性验证**：自动使用 ffmpeg 验证下载的视频文件
- **智能命名**：根据作者和描述自动生成文件名

## 🚀 快速开始

### 命令行使用

```bash
# 基本用法：下载 H.264 版本
python3 resolve_video.py --url "https://weixin.qq.com/sph/AO22ZztN3h"

# 指定输出目录
python3 resolve_video.py --url "https://weixin.qq.com/sph/AO22ZztN3h" --output-dir "/path/to/downloads"

# 下载所有可用版本
python3 resolve_video.py --url "https://weixin.qq.com/sph/AO22ZztN3h" --quality all
```

### 参数说明

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `--url` | ✓ | - | 视频号分享链接 |
| `--quality` | | `h264` | 视频编码：`h264` / `h265` / `all` |
| `--output-dir` | | `E:/05-下载/Workbuddy-download` | 输出目录 |
| `--timeout` | | `30` | 请求超时秒数 |

## 🔧 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                    用户操作流程                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  weixin.qq.com/sph/xxx                                     │
│       ↓                                                     │
│  POST /api/fetch_video_profile                             │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────┐          │
│  │         wx.defou.ai (Cloudflare Worker)      │          │
│  │                                              │          │
│  │  第一步：调用元宝接口                         │          │
│  │  POST https://yuanbao.tencent.com/api/...   │          │
│  │  → 获取 exportId + token                     │          │
│  │                                              │          │
│  │  第二步：查询 Feed 信息                        │          │
│  │  POST https://channels.weixin.qq.com/...    │          │
│  │  → 返回 H.264/H.265 视频直链                 │          │
│  └──────────────────────────────────────────────┘          │
│       ↓                                                     │
│  finder.video.qq.com/251/.../stodownload?...              │
│       ↓                                                     │
│  本地保存为 MP4 文件                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 技术细节

**两步解析法：**

1. **元宝接口解析**
   - 端点：`https://yuanbao.tencent.com/api/weixin/get_parse_result`
   - 入参：`type=video_channel_url`, `url=<分享链接>`, `scene=1`
   - 出参：`wx_export_id` (exportId) 和 `playable_url` (含 token)

2. **Feed信息查询**
   - 端点：`https://channels.weixin.qq.com/finder-preview/api/feed/get_feed_info`
   - 入参：`generalToken` 和 `exportId`
   - 出参：完整的视频元数据，包括 H.264/H.265 视频直链

**关键点：**
- 不需要微信登录态
- 不依赖本机微信客户端
- 无需安装中间人证书
- 视频URL有时效性（约5分钟），需尽快下载

## 📦 安装

### 系统要求

- Python 3.10+
- Windows / macOS / Linux

### 依赖项

```bash
pip install requests
# 可选：ffmpeg（用于视频验证）
```

### 克隆仓库

```bash
git clone https://github.com/<username>/WC_videoDownload.git
cd WC_videoDownload
```

## 🎯 使用示例

### 示例 1：基本下载

```bash
python3 resolve_video.py --url "https://weixin.qq.com/sph/AO22ZztN3h"
```

输出：
```
[1/3] 正在解析视频...
  URL: https://weixin.qq.com/sph/AO22ZztN3h

==================================================
视频信息:
  作者: 佳佳玻璃
  描述: #玻璃瓶生产厂家#香水化妆品瓶#玻璃行业
  时长: ?秒
  点赞: 134 | 评论: 10 | 转发: 261
==================================================

[2/3] 正在下载 (H264版本)...
  目标: ./downloads/佳佳玻璃_视频号_H264.mp4
  预计大小: 11.1 MB
  进度: 11.1MB / 11.1MB (100.0%)
  ✓ 完成: 11.1 MB

[3/3] 验证视频完整性...
  Duration: 00:01:21.55
  Stream #0:0[0x1](und): Video: h264 (High), 1024x576, 30 fps
```

### 示例 2：批量下载多个视频

```bash
for url in "https://weixin.qq.com/sph/xxx1" "https://weixin.qq.com/sph/xxx2"; do
    python3 resolve_video.py --url "$url"
done
```

## ⚠️ 注意事项

1. **时效性**：视频下载链接有效期约 5 分钟，获取后请尽快下载
2. **版权**：请仅下载您有权访问的内容，尊重创作者权益
3. **可用性**：本工具依赖第三方解析服务 `wx.defou.ai`，如服务不可用可稍后重试
4. **合规**：仅限个人学习研究使用，请勿用于商业目的

## 🏗️ 项目结构

```
WC_videoDownload/
├── README.md                  # 项目说明文档
├── resolve_video.py           # 核心下载脚本
├── requirements.txt           # Python 依赖
└── LICENSE                    # MIT License
```

## 📝 开发说明

### 添加新平台支持

如需支持其他视频平台，可在 `resolve_video.py` 中添加新的解析函数：

```python
def resolve_platform(url: str) -> dict:
    """解析平台特定逻辑"""
    # 实现解析逻辑
    pass
```

### 自定义解析服务

如果自有解析服务，只需修改：

```python
RESOLVER_URL = "https://your-resolver.com/api/fetch_video_profile"
```

## 🙏 致谢

- [ltaoo/wx_channels_download](https://github.com/ltaoo/wx_channels_download) - 开源的微信视频号下载工具，本项目借鉴其在线解析架构
- [wx.defou.ai](https://wx.defou.ai) - 由 wangdefou 部署的 Cloudflare Workers 解析服务

## 📄 License

MIT License - 详见 [LICENSE](LICENSE) 文件

---

**免责声明**：本工具仅供技术交流和学习研究使用，请遵守相关法律法规，勿用于非法用途。
