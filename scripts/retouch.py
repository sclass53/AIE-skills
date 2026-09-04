#!/usr/bin/env python3
"""
修图师命令行工具
支持查看直方图、EXIF、调整色温/高光/阴影、裁剪、颜色分级、观察图像，并支持 RAW。
"""

import argparse
import json
import os
import math
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
import imageio
import exifread

# ----------------------------------------------------------------------
# 常量
# ----------------------------------------------------------------------
RAW_EXTENSIONS = {
    '.raw', '.dng', '.nef', '.cr2', '.cr3', '.arw', '.orf',
    '.rw2', '.raf', '.pef', '.srw', '.x3f', '.3fr', '.kdc',
    '.mef', '.mrw', '.nrw', '.ptx', '.r3d', '.srw', '.x3f'
}

ASCII_CHARS = " .:-=+*#%@"  # 从暗到亮


# ----------------------------------------------------------------------
# 基础图像加载与保存
# ----------------------------------------------------------------------
def is_raw(path: str) -> bool:
    ext = Path(path).suffix.lower()
    return ext in RAW_EXTENSIONS


def load_image(path: str) -> np.ndarray:
    """
    加载图像并返回 float32 RGB 数组，值域 0~1。
    支持 RAW 和普通图像。
    """
    if is_raw(path):
        import rawpy
        with rawpy.imread(path) as raw:
            # 使用相机白平衡，自动亮度，输出 sRGB gamma 编码
            rgb = raw.postprocess(
                output_bps=16,
                gamma=(2.222, 4.5),
                output_color=rawpy.ColorSpace.sRGB,
                use_camera_wb=True,
                no_auto_bright=False
            )
        img = rgb.astype(np.float32) / 65535.0
    else:
        with Image.open(path) as pil:
            pil = pil.convert('RGB')
            img = np.asarray(pil, dtype=np.float32) / 255.0
    return img.astype(np.float32)


def save_image(img: np.ndarray, path: str):
    """保存图像，根据扩展名选择位深。"""
    img = np.clip(img, 0.0, 1.0)
    ext = Path(path).suffix.lower()
    out_dir = Path(path).parent
    if out_dir and not out_dir.exists():
        out_dir.mkdir(parents=True, exist_ok=True)

    if ext in ['.tif', '.tiff']:
        data = (img * 65535.0).astype(np.uint16)
        imageio.imwrite(path, data)
    elif ext == '.png':
        # 尝试保存 16-bit PNG
        data = (img * 65535.0).astype(np.uint16)
        imageio.imwrite(path, data)
    elif ext in ['.jpg', '.jpeg']:
        data = (img * 255.0).astype(np.uint8)
        imageio.imwrite(path, data, quality=95)
    else:
        # 默认为 8-bit PNG
        data = (img * 255.0).astype(np.uint8)
        imageio.imwrite(path, data)


# ----------------------------------------------------------------------
# 颜色与色调工具
# ----------------------------------------------------------------------
def luma(img: np.ndarray) -> np.ndarray:
    """sRGB 伽马编码亮度，值域 0~1。"""
    return 0.2126 * img[..., 0] + 0.7152 * img[..., 1] + 0.0722 * img[..., 2]


def kelvin_to_rgb(kelvin: float) -> tuple:
    """
    将色温（开尔文）转换为近似的 sRGB 线性增益（Tanner Helland 算法）。
    返回 (R, G, B) 增益，值域约 0~1。
    """
    temp = kelvin / 100.0
    # 红色
    if temp <= 66:
        red = 255
    else:
        red = temp - 60
        red = 329.698727446 * (red ** -0.1332047592)
    # 绿色
    if temp <= 66:
        green = temp
        green = 99.4708025861 * math.log(green) - 161.1195681661
    else:
        green = temp - 60
        green = 288.1221695283 * (green ** -0.0755148492)
    # 蓝色
    if temp >= 66:
        blue = 255
    elif temp <= 19:
        blue = 0
    else:
        blue = temp - 10
        blue = 138.5177312231 * math.log(blue) - 305.0447927307

    def clip(v):
        return min(1.0, max(0.0, v / 255.0))

    return clip(red), clip(green), clip(blue)


def adjust_temperature_offset(img: np.ndarray, temp: float, tint: float) -> np.ndarray:
    """
    色温/色调偏移调整。
    temp: -100（冷） ~ +100（暖）
    tint: -100（绿） ~ +100（品红）
    """
    img = img.copy()
    # 简单线性增益，避免过冲
    r_scale = 1.0 + temp * 0.0025 + tint * 0.0015
    g_scale = 1.0 - tint * 0.0015
    b_scale = 1.0 - temp * 0.0025 + tint * 0.0015

    img[..., 0] *= r_scale
    img[..., 1] *= g_scale
    img[..., 2] *= b_scale
    return img


def apply_kelvin(img: np.ndarray, kelvin: float) -> np.ndarray:
    """应用绝对色温（改变白平衡）。"""
    gains = kelvin_to_rgb(kelvin)
    img = img.copy()
    img[..., 0] *= gains[0]
    img[..., 1] *= gains[1]
    img[..., 2] *= gains[2]
    return img


def adjust_exposure(img: np.ndarray, ev: float) -> np.ndarray:
    """曝光补偿，ev 单位 EV。"""
    factor = 2.0 ** ev
    return img * factor


def adjust_contrast(img: np.ndarray, contrast: float) -> np.ndarray:
    """对比度调整，-100~+100。"""
    # 映射到 0~2 左右的系数
    c = 1.0 + contrast / 100.0
    return (img - 0.5) * c + 0.5


def adjust_saturation(img: np.ndarray, saturation: float) -> np.ndarray:
    """饱和度调整，-100~+100。"""
    gray = luma(img)[..., np.newaxis]
    sat = 1.0 + saturation / 100.0
    return gray + (img - gray) * sat


def adjust_highlight_shadow(img: np.ndarray, highlight: float, shadow: float) -> np.ndarray:
    """
    高光/阴影调整。
    highlight: 正值压暗高光，负值提亮高光。
    shadow: 正值提亮阴影，负值压暗阴影。
    """
    img = img.copy()
    L = luma(img)
    # 高光区域掩码：亮度 > 0.5
    h_mask = np.clip((L - 0.5) * 2.0, 0.0, 1.0)[..., np.newaxis]
    # 阴影区域掩码：亮度 < 0.5
    s_mask = np.clip((0.5 - L) * 2.0, 0.0, 1.0)[..., np.newaxis]

    # 高光调整因子：正值降低高光（乘以 <1），负值增强高光
    h_factor = 1.0 - highlight / 150.0
    # 阴影调整因子：正值提亮阴影（乘以 >1），负值压暗
    s_factor = 1.0 + shadow / 150.0

    # 仅在对应区域应用
    img = img * (1.0 - h_mask) + (img * h_factor) * h_mask
    img = img * (1.0 - s_mask) + (img * s_factor) * s_mask
    return img


def split_toning(img: np.ndarray, shadow_rgb: tuple, highlight_rgb: tuple,
                strength: float = 0.8, balance: float = 0.5) -> np.ndarray:
    """
    分离色调（split toning）。
    shadow_rgb / highlight_rgb: 三元组，每个通道偏移量，范围约 -0.3~0.3。
    strength: 强度 0~1。
    balance: 阴影/高光分界，默认 0.5。
    """
    img = img.copy()
    L = luma(img)
    # 平滑过渡
    shadow_weight = 1.0 - np.clip((L - (balance - 0.2)) / 0.4, 0, 1)
    highlight_weight = np.clip((L - balance) / 0.4, 0, 1)

    # 应用偏移
    for c in range(3):
        offset = shadow_rgb[c] * shadow_weight + highlight_rgb[c] * highlight_weight
        img[..., c] += offset * strength
    return img

def load_presets_from_style_md(path: str = None) -> dict:
    """
    从 style.md 文件加载预设（JSON 格式）。
    优先使用传入路径，否则使用环境变量 STYLE_MD_PATH，最后回退到脚本目录下的 style.md。
    """
    if path is None:
        path = os.environ.get('STYLE_MD_PATH')
    if path is None:
        # 默认脚本同目录下的 style.md
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, 'style.md')

    if not os.path.exists(path):
        return {}

    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        # 去除 HTML 注释（简单处理，假设注释不包含 JSON 花括号）
        import re
        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        presets = json.loads(content)
        return presets
    except Exception as e:
        print(f"警告：无法读取或解析 style.md（{path}）: {e}", file=sys.stderr)
        return {}

def apply_grade_preset(img: np.ndarray, preset: str, strength: float = 0.8,
                       presets_dict: dict = None) -> np.ndarray:
    """
    颜色分级预设。
    预设参数从 presets_dict 中获取（若未提供则使用默认内置预设）。
    """
    if presets_dict is None:
        # 默认内置预设（与 style.md 保持一致）
        presets_dict = {
            'teal-orange': {
                'shadow_rgb': (-0.06, 0.03, 0.06),
                'highlight_rgb': (0.07, 0.02, -0.07),
                'strength_default': 0.8,
                'pre_saturation': None
            },
            # ... 其他内置预设（可简化为从 style.md 读取，若 style.md 存在则覆盖）
        }

    if preset not in presets_dict:
        raise ValueError(f"未知预设: {preset}. 可选: {list(presets_dict.keys())}")

    cfg = presets_dict[preset]
    # 转换 RGB 列表为元组（兼容性）
    shadow_rgb = tuple(cfg['shadow_rgb'])
    highlight_rgb = tuple(cfg['highlight_rgb'])
    strength_default = cfg.get('strength_default', 0.8)
    pre_saturation = cfg.get('pre_saturation', None)

    img = img.copy()
    if pre_saturation is not None:
        img = adjust_saturation(img, pre_saturation)
    # 使用传入的 strength 覆盖默认值（若用户指定）
    img = split_toning(img, shadow_rgb, highlight_rgb, strength=strength)
    return img

# ----------------------------------------------------------------------
# 直方图与统计
# ----------------------------------------------------------------------
def compute_histogram(img: np.ndarray, bins: int = 256) -> dict:
    """计算亮度直方图及曝光统计。"""
    L = luma(img)
    hist, bin_edges = np.histogram(L, bins=bins, range=(0, 1))
    # 统计量
    mean = float(np.mean(L))
    median = float(np.median(L))
    std = float(np.std(L))
    p1 = float(np.percentile(L, 1))
    p99 = float(np.percentile(L, 99))
    underexposed = float(np.mean(L < 5 / 255))
    overexposed = float(np.mean(L > 250 / 255))
    clipped_shadow = float(np.mean(L < 1 / 255))
    clipped_highlight = float(np.mean(L > 254 / 255))
    dynamic_range = p99 - p1

    ch_means = [float(np.mean(img[..., i])) for i in range(3)]
    ch_medians = [float(np.median(img[..., i])) for i in range(3)]

    return {
        'mean': mean,
        'median': median,
        'std': std,
        'p1': p1,
        'p99': p99,
        'underexposed_ratio': underexposed,
        'overexposed_ratio': overexposed,
        'clipped_shadow_ratio': clipped_shadow,
        'clipped_highlight_ratio': clipped_highlight,
        'dynamic_range': dynamic_range,
        'channel_means': {'R': ch_means[0], 'G': ch_means[1], 'B': ch_means[2]},
        'channel_medians': {'R': ch_medians[0], 'G': ch_medians[1], 'B': ch_medians[2]},
        'histogram': hist.tolist()
    }


# ----------------------------------------------------------------------
# EXIF 提取
# ----------------------------------------------------------------------
def extract_exif(path: str) -> dict:
    """提取 EXIF 信息，重点包含镜头信息。"""
    tags_of_interest = [
        'Image Make', 'Image Model', 'Image DateTime', 'Image Artist',
        'EXIF LensMake', 'EXIF LensModel', 'EXIF FocalLength',
        'EXIF FNumber', 'EXIF ApertureValue', 'EXIF ExposureTime',
        'EXIF ISOSpeedRatings', 'EXIF ExposureProgram',
        'EXIF WhiteBalance', 'EXIF Flash', 'EXIF MeteringMode',
        'EXIF ExposureBiasValue', 'EXIF FocalLengthIn35mmFilm'
    ]
    result = {}
    try:
        with open(path, 'rb') as f:
            tags = exifread.process_file(f, details=False)
        for tag in tags_of_interest:
            if tag in tags:
                result[tag] = str(tags[tag])
        # 补充一些可能以不同 key 存在的标签
        for key, value in tags.items():
            if 'Lens' in key and key not in result:
                result[key] = str(value)
            if 'FocalLength' in key and key not in result:
                result[key] = str(value)
    except Exception as e:
        result['error'] = f"无法读取 EXIF: {e}"
    return result


# ----------------------------------------------------------------------
# ASCII 缩略图
# ----------------------------------------------------------------------
def ascii_thumbnail(img: np.ndarray, width: int = 60) -> str:
    """生成 ASCII 亮度缩略图。"""
    h, w, _ = img.shape
    # 字符高度约为宽度的 2 倍，所以行数减半
    aspect = 0.5
    new_w = width
    new_h = max(1, int(h * (new_w / w) * aspect))
    pil = Image.fromarray((img * 255).astype(np.uint8))
    pil = pil.resize((new_w, new_h), Image.Resampling.BILINEAR)
    arr = np.asarray(pil, dtype=np.float32) / 255.0
    L = luma(arr)
    lines = []
    for y in range(new_h):
        line = ''
        for x in range(new_w):
            val = L[y, x]
            idx = min(len(ASCII_CHARS) - 1, int(val * (len(ASCII_CHARS) - 1)))
            line += ASCII_CHARS[idx]
        lines.append(line)
    return '\n'.join(lines)


# ----------------------------------------------------------------------
# 子命令处理
# ----------------------------------------------------------------------
def cmd_inspect(args):
    img = load_image(args.input)
    h, w, _ = img.shape
    L = luma(img)
    avg_color = img.reshape(-1, 3).mean(axis=0)
    hex_color = '#{:02x}{:02x}{:02x}'.format(
        int(avg_color[0] * 255), int(avg_color[1] * 255), int(avg_color[2] * 255)
    )
    print(f"文件: {args.input}")
    print(f"尺寸: {w} x {h} 像素")
    print(f"平均颜色: {hex_color}  (RGB: {avg_color[0]:.3f}, {avg_color[1]:.3f}, {avg_color[2]:.3f})")
    print(f"亮度统计: 最小={L.min():.3f}  最大={L.max():.3f}  均值={L.mean():.3f}  中位数={np.median(L):.3f}")
    if args.exif:
        exif = extract_exif(args.input)
        if exif:
            print("\nEXIF 摘要:")
            for k, v in list(exif.items())[:5]:
                print(f"  {k}: {v}")
    print("\nASCII 缩略图（亮度）:")
    print(ascii_thumbnail(img, width=args.width))


def cmd_histogram(args):
    img = load_image(args.input)
    stats = compute_histogram(img)
    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(f"亮度直方图统计 ({args.input})")
        print(f"  均值:               {stats['mean']:.4f}")
        print(f"  中位数:             {stats['median']:.4f}")
        print(f"  标准差:             {stats['std']:.4f}")
        print(f"  1% 分位:            {stats['p1']:.4f}")
        print(f"  99% 分位:           {stats['p99']:.4f}")
        print(f"  动态范围 (P99-P1):  {stats['dynamic_range']:.4f}")
        print(f"  欠曝比例 (<5/255):  {stats['underexposed_ratio']:.2%}")
        print(f"  过曝比例 (>250/255):{stats['overexposed_ratio']:.2%}")
        print(f"  暗部剪切 (<1/255):  {stats['clipped_shadow_ratio']:.2%}")
        print(f"  高光剪切 (>254/255):{stats['clipped_highlight_ratio']:.2%}")
        print(f"  通道均值: R={stats['channel_means']['R']:.4f} "
            f"G={stats['channel_means']['G']:.4f} "
            f"B={stats['channel_means']['B']:.4f}")
        print(f"  通道中位数: R={stats['channel_medians']['R']:.4f} "
            f"G={stats['channel_medians']['G']:.4f} "
            f"B={stats['channel_medians']['B']:.4f}")


def cmd_exif(args):
    exif = extract_exif(args.input)
    if args.json:
        print(json.dumps(exif, ensure_ascii=False, indent=2))
    else:
        print(f"EXIF 信息 ({args.input})")
        if not exif:
            print("  未找到 EXIF 数据")
        for k, v in exif.items():
            print(f"  {k}: {v}")


def cmd_adjust(args):
    img = load_image(args.input)
    # 绝对色温
    if args.kelvin is not None:
        img = apply_kelvin(img, args.kelvin)
    # 色温偏移
    if args.temperature != 0 or args.tint != 0:
        img = adjust_temperature_offset(img, args.temperature, args.tint)
    # 曝光
    if args.exposure != 0:
        img = adjust_exposure(img, args.exposure)
    # 对比度
    if args.contrast != 0:
        img = adjust_contrast(img, args.contrast)
    # 饱和度
    if args.saturation != 0:
        img = adjust_saturation(img, args.saturation)
    # 高光阴影
    if args.highlight != 0 or args.shadow != 0:
        img = adjust_highlight_shadow(img, args.highlight, args.shadow)

    save_image(img, args.output)
    print(f"已保存调整后图像: {args.output}")


def cmd_crop(args):
    img = load_image(args.input)
    h, w, _ = img.shape
    left = max(0, min(args.left, 1))
    top = max(0, min(args.top, 1))
    right = max(left, min(args.right, 1))
    bottom = max(top, min(args.bottom, 1))

    x0 = int(left * w)
    x1 = int(right * w)
    y0 = int(top * h)
    y1 = int(bottom * h)
    cropped = img[y0:y1, x0:x1]
    save_image(cropped, args.output)
    print(f"已保存裁剪图像: {args.output}  (原 {w}x{h} -> 新 {x1-x0}x{y1-y0})")

def cmd_list_presets(args):
    presets_dict = load_presets_from_style_md()
    if not presets_dict:
        print("未找到 style.md 或内容为空，使用内置预设。")
        # 这里可硬编码内置列表或读取内置默认
        presets_dict = {
            'teal-orange': {}, 'cold-gray': {}, 'warm': {}, 'cool': {}, 'noir': {}
        }
    print("可用颜色分级预设：")
    for name in presets_dict.keys():
        print(f"  - {name}")

def cmd_grade(args):
    img = load_image(args.input)
    # 加载预设字典
    presets_dict = load_presets_from_style_md()
    if not presets_dict:
        # 若加载失败，使用内置最小预设（避免崩溃）
        presets_dict = {
            'teal-orange': {'shadow_rgb': (-0.06,0.03,0.06), 'highlight_rgb': (0.07,0.02,-0.07), 'strength_default':0.8, 'pre_saturation':None},
            'cold-gray': {'shadow_rgb': (0,0,0.07), 'highlight_rgb': (0.02,0.02,0.05), 'strength_default':0.8, 'pre_saturation':-40},
            'warm': {'shadow_rgb': (0.02,0.01,-0.02), 'highlight_rgb': (0.08,0.03,-0.06), 'strength_default':0.8, 'pre_saturation':None},
            'cool': {'shadow_rgb': (-0.02,-0.01,0.05), 'highlight_rgb': (-0.03,-0.02,0.07), 'strength_default':0.8, 'pre_saturation':None},
            'noir': {'shadow_rgb': (0,0,0), 'highlight_rgb': (0,0,0), 'strength_default':0.8, 'pre_saturation':-100}
        }
    try:
        graded = apply_grade_preset(img, args.preset, args.strength, presets_dict)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    save_image(graded, args.output)
    print(f"已保存颜色分级图像: {args.output}  预设: {args.preset}")

# ----------------------------------------------------------------------
# 主入口
# ----------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description='修图师命令行工具')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # inspect
    p_inspect = subparsers.add_parser('inspect', help='观察图像')
    p_inspect.add_argument('input', help='输入图像路径')
    p_inspect.add_argument('--width', type=int, default=60, help='ASCII缩略图宽度')
    p_inspect.add_argument('--exif', action='store_true', help='同时显示EXIF摘要')
    p_inspect.set_defaults(func=cmd_inspect)

    # histogram
    p_hist = subparsers.add_parser('histogram', help='查看直方图')
    p_hist.add_argument('input', help='输入图像路径')
    p_hist.add_argument('--json', action='store_true', help='输出JSON格式')
    p_hist.set_defaults(func=cmd_histogram)

    # exif
    p_exif = subparsers.add_parser('exif', help='获取EXIF信息')
    p_exif.add_argument('input', help='输入图像路径')
    p_exif.add_argument('--json', action='store_true', help='输出JSON格式')
    p_exif.set_defaults(func=cmd_exif)

    # adjust
    p_adj = subparsers.add_parser('adjust', help='调整色温/高光/阴影等')
    p_adj.add_argument('input', help='输入图像路径')
    p_adj.add_argument('-o', '--output', required=True, help='输出图像路径')
    p_adj.add_argument('--temperature', type=float, default=0.0,
                       help='色温偏移 -100~+100（正=暖，负=冷）')
    p_adj.add_argument('--tint', type=float, default=0.0,
                       help='色调偏移 -100~+100（负=绿，正=品红）')
    p_adj.add_argument('--kelvin', type=float, default=None,
                       help='绝对色温（开尔文），覆盖相机白平衡')
    p_adj.add_argument('--highlight', type=float, default=0.0,
                       help='高光调整：正值压暗高光，负值提亮高光')
    p_adj.add_argument('--shadow', type=float, default=0.0,
                       help='阴影调整：正值提亮阴影，负值压暗阴影')
    p_adj.add_argument('--exposure', type=float, default=0.0,
                       help='曝光补偿 EV（如 0.3）')
    p_adj.add_argument('--contrast', type=float, default=0.0,
                       help='对比度 -100~+100')
    p_adj.add_argument('--saturation', type=float, default=0.0,
                       help='饱和度 -100~+100')
    p_adj.set_defaults(func=cmd_adjust)

    # crop
    p_crop = subparsers.add_parser('crop', help='裁剪图像')
    p_crop.add_argument('input', help='输入图像路径')
    p_crop.add_argument('-o', '--output', required=True, help='输出图像路径')
    p_crop.add_argument('--left', type=float, default=0.0, help='左边界归一化坐标 0~1')
    p_crop.add_argument('--top', type=float, default=0.0, help='上边界归一化坐标 0~1')
    p_crop.add_argument('--right', type=float, default=1.0, help='右边界归一化坐标 0~1')
    p_crop.add_argument('--bottom', type=float, default=1.0, help='下边界归一化坐标 0~1')
    p_crop.set_defaults(func=cmd_crop)

    # grade
    p_grade = subparsers.add_parser('grade', help='颜色分级')
    p_grade.add_argument('input', help='输入图像路径')
    p_grade.add_argument('-o', '--output', required=True, help='输出图像路径')
    p_grade.add_argument('--preset', required=True,
                         choices=['teal-orange', 'cold-gray', 'warm', 'cool', 'noir'],
                         help='颜色分级预设')
    p_grade.add_argument('--strength', type=float, default=0.8,
                         help='强度 0~1')
    p_grade.set_defaults(func=cmd_grade)

    # list-presets
    p_list = subparsers.add_parser('list-presets', help='列出所有颜色分级预设')
    p_list.set_defaults(func=cmd_list_presets)
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()