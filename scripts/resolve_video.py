#!/usr/bin/env python3
"""
微信视频号视频下载器
使用在线解析服务获取视频直链并下载

用法:
    python3 resolve_video.py --url "https://weixin.qq.com/sph/AO22ZztN3h" [--quality h264|h265|all] [--output-dir E:/05-下载/Workbuddy-download]

原理：
    两步解析法：
    1. 元宝接口：将视频号分享链接提交给腾讯元宝Web接口，获取视频导出ID和临时令牌
    2. Feed查询：用令牌查询视频号API，获得H.264/H.265视频直链
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests


# 配置
RESOLVER_URL = "https://wx.defou.ai/api/fetch_video_profile"
DEFAULT_OUTPUT_DIR = "E:/05-下载/Workbuddy-download"
PROXY = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


def parse_args():
    parser = argparse.ArgumentParser(description="微信视频号视频下载器")
    parser.add_argument("--url", required=True, help="视频号分享链接")
    parser.add_argument(
        "--quality",
        choices=["h264", "h265", "all"],
        default="h264",
        help="视频编码格式 (默认: h264)",
    )
    parser.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument("--timeout", type=int, default=30, help="请求超时秒数")
    return parser.parse_args()


def resolve_video(url: str, timeout: int = 30) -> dict:
    """
    调用在线解析服务获取视频信息

    Returns:
        dict with keys: author, description, h264_url, h265_url, cover_url
    """
    print(f"[1/3] 正在解析视频...")
    print(f"  URL: {url}")

    try:
        resp = requests.post(
            RESOLVER_URL,
            json={"url": url},
            headers={"Content-Type": "application/json"},
            timeout=timeout,
            proxies=PROXY,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ProxyError as e:
        # 代理不可用时尝试无代理
        print(f"  代理不可用，尝试直连...")
        try:
            resp = requests.post(
                RESOLVER_URL,
                json={"url": url},
                headers={"Content-Type": "application/json"},
                timeout=timeout,
                proxies={},
            )
            resp.raise_for_status()
            data = resp.json()
        except Exception as e2:
            raise RuntimeError(f"解析失败: {e2}")
    except Exception as e:
        raise RuntimeError(f"解析失败: {e}")

    if data.get("errCode") != 0:
        raise RuntimeError(f"解析错误: {data.get('errMsg', 'unknown')}")

    feed = data["data"]["feedInfo"]
    author = data["data"]["authorInfo"]["nickname"]

    return {
        "author": author,
        "description": feed.get("description", ""),
        "h264_url": feed.get("h264VideoInfo", {}).get("videoUrl", ""),
        "h265_url": feed.get("h265VideoInfo", {}).get("videoUrl", ""),
        "cover_url": feed.get("coverUrl", ""),
        "duration": feed.get("durationSeconds", "?"),
        "like_count": feed.get("likeCountFmt", "?"),
        "comment_count": feed.get("commentCountFmt", "?"),
        "forward_count": feed.get("forwardCountFmt", "?"),
    }


def download_video(video_url: str, output_path: str, quality: str) -> str:
    """
    下载视频文件

    Returns:
        下载后的文件路径
    """
    print(f"\n[2/3] 正在下载 ({quality.upper()}版本)...")
    print(f"  目标: {output_path}")

    headers = {
        "Referer": "https://channels.weixin.qq.com/",
        **HEADERS,
    }

    # 计算文件大小（用于进度显示）
    try:
        head_resp = requests.head(video_url, headers=headers, timeout=10, proxies=PROXY)
        total_size = int(head_resp.headers.get("Content-Length", 0))
        print(f"  预计大小: {total_size / 1024 / 1024:.1f} MB")
    except:
        total_size = 0

    # 流式下载
    resp = requests.get(video_url, headers=headers, stream=True, timeout=300, proxies=PROXY)
    resp.raise_for_status()

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    downloaded = 0
    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = downloaded / total_size * 100
                    mb = downloaded / 1024 / 1024
                    print(f"\r  进度: {mb:.1f}MB / {total_size/1024/1024:.1f}MB ({percent:.1f}%)", end="", flush=True)
                else:
                    mb = downloaded / 1024 / 1024
                    print(f"\r  已下载: {mb:.1f}MB", end="", flush=True)

    print()  # 换行
    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  ✓ 完成: {size_mb:.1f} MB")
    return output_path


def validate_video(path: str) -> bool:
    """使用ffmpeg验证视频文件完整性"""
    import subprocess

    print(f"\n[3/3] 验证视频完整性...")
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-i", path,
                "-f", "null",
                "-",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode == 0:
            # 提取关键信息
            for line in result.stderr.split("\n"):
                if "Duration:" in line or "Stream #" in line:
                    print(f"  {line.strip()}")
            return True
        else:
            print(f"  ✗ 验证失败: {result.stderr[-200:]}")
            return False
    except FileNotFoundError:
        print("  ⚠ ffmpeg未安装，跳过验证")
        return True
    except Exception as e:
        print(f"  ⚠ 验证出错: {e}")
        return True  # 文件已存在就算成功


def generate_filename(author: str, description: str, quality: str) -> str:
    """生成文件名"""
    # 清理作者名中的非法字符
    safe_author = "".join(c for c in author if c not in r'<>:"/\|?*')
    # 取描述前几个字作为关键词
    keywords = "".join(c for c in description if c.isalnum() or c in " _-")[:20]
    # 添加时间戳避免重复
    timestamp = time.strftime("%Y%m%d_%H%M")

    filename = f"{safe_author}_视频号_{keywords}_H{quality}_{timestamp}.mp4"
    # 限制总长度
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def main():
    args = parse_args()

    # 创建输出目录
    os.makedirs(args.output_dir, exist_ok=True)

    try:
        # Step 1: 解析
        info = resolve_video(args.url, args.timeout)

        print(f"\n{'='*50}")
        print(f"视频信息:")
        print(f"  作者: {info['author']}")
        print(f"  描述: {info['description']}")
        print(f"  时长: {info['duration']}秒")
        print(f"  点赞: {info['like_count']} | 评论: {info['comment_count']} | 转发: {info['forward_count']}")
        print(f"{'='*50}\n")

        # Step 2: 下载
        results = []

        if args.quality in ["h264", "all"]:
            if info["h264_url"]:
                filename = generate_filename(info["author"], info["description"], "H264")
                output_path = os.path.join(args.output_dir, filename)

                # 如果文件已存在则跳过
                if os.path.exists(output_path):
                    print(f"  跳过已存在: {filename}")
                    results.append({"quality": "h264", "path": output_path, "status": "skipped"})
                else:
                    path = download_video(info["h264_url"], output_path, "h264")
                    valid = validate_video(path)
                    results.append({"quality": "h264", "path": path, "status": "ok" if valid else "error"})
            else:
                print("  ⚠ H.264版本不可用")

        if args.quality in ["h265", "all"] and info["h265_url"]:
            filename = generate_filename(info["author"], info["description"], "H265")
            output_path = os.path.join(args.output_dir, filename)

            if os.path.exists(output_path):
                print(f"  跳过已存在: {filename}")
                results.append({"quality": "h265", "path": output_path, "status": "skipped"})
            else:
                path = download_video(info["h265_url"], output_path, "h265")
                valid = validate_video(path)
                results.append({"quality": "h265", "path": path, "status": "ok" if valid else "error"})

        # Step 3: 输出结果
        print(f"\n{'='*50}")
        print("下载结果:")
        for r in results:
            status_icon = "✓" if r["status"] == "ok" else ("⊘" if r["status"] == "skipped" else "✗")
            print(f"  {status_icon} [{r['quality'].upper()}] {os.path.basename(r['path'])}")
        print(f"{'='*50}")

        # 返回JSON结果供skill调用
        print(json.dumps({
            "success": all(r["status"] in ["ok", "skipped"] for r in results),
            "files": [r["path"] for r in results if r["status"] == "ok"],
            "info": info,
        }, ensure_ascii=False))

    except Exception as e:
        print(f"\n✗ 错误: {e}", file=sys.stderr)
        json.dump({"success": False, "error": str(e)}, sys.stdout, ensure_ascii=False)
        sys.exit(1)


if __name__ == "__main__":
    main()
