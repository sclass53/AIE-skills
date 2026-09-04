---
name: photo-retoucher
description: 专业修图师技能。支持查看直方图、提取EXIF镜头信息、调整色温/高光/阴影/曝光/对比度/饱和度、裁剪、青橙/冷灰等颜色分级、观察图像，并支持RAW文件。
---

# 修图师 Skill

本技能通过命令行脚本 `retouch.py` 完成照片处理。适用文件包括 JPEG、PNG、TIFF 以及常见 RAW 格式（如 .dng, .nef, .cr2, .cr3, .arw, .orf, .rw2, .raf 等）。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 命令概览

| 命令 | 功能 |
|------|------|
| `inspect`   | 观察图像：尺寸、模式、平均颜色、亮度统计、ASCII 缩略图 |
| `histogram` | 查看直方图，返回曝光信息数字（均值/中位数/欠曝过曝比例等） |
| `exif`      | 获取 EXIF 信息，重点包含镜头信息 |
| `adjust`    | 调整色温、色调、曝光、对比度、饱和度、高光、阴影 |
| `crop`      | 按归一化坐标裁剪图像 |
| `grade`     | 颜色偏移/分级：青橙、冷灰、暖调、冷调、黑白等预设 |
| `list-presets` | 列出所有可用颜色分级预设（含 style.md 中自定义预设） |

## 使用示例

### 观察图像
```bash
python retouch.py inspect photo.dng --width 80
```

### 查看直方图（数字摘要）
```bash
python retouch.py histogram photo.jpg
# 或输出完整JSON
python retouch.py histogram photo.jpg --json
```

### 获取EXIF
```bash
python retouch.py exif photo.nef
```

### 调整色温/高光/阴影等
```bash
python retouch.py adjust photo.cr2 -o output.tif \
    --temperature 15 --tint 0 \
    --highlight -30 --shadow 20 \
    --exposure 0.2 --contrast 10 --saturation 5
```

参数说明：
- `--temperature`：色温偏移，-100（冷）到 +100（暖），0 为原始白平衡。
- `--tint`：色调偏移，负值偏绿，正值偏品红。
- `--highlight`：高光调整，负值压暗高光，正值提亮高光。
- `--shadow`：阴影调整，正值提亮阴影，负值压暗阴影。
- `--exposure`：曝光补偿，单位 EV（如 0.3 表示增加 0.3 档）。
- `--contrast`：对比度，-100 到 +100。
- `--saturation`：饱和度，-100（去色）到 +100（增强）。
- `--kelvin`：可选，设置绝对色温（开尔文），会覆盖相机白平衡。

### 裁剪
```bash
python retouch.py crop photo.jpg -o cropped.jpg \
    --left 0.1 --top 0.1 --right 0.9 --bottom 0.9
```
坐标均为归一化值，范围 0~1。

### 颜色分级
```bash
python retouch.py grade photo.dng -o graded.jpg --preset teal-orange --strength 0.8
```
预设值：`teal-orange`, `cold-gray`, `warm`, `cool`, `noir`。

### 列出所有颜色分级预设
```bash
python retouch.py list-presets
```

### 自定义预设
颜色分级预设存储在 `style.md` 中（JSON 格式）。用户可以直接编辑该文件，添加新的预设条目，即可在 `grade` 命令中使用 `--preset 名称` 调用。例如添加：

```json
"vintage": {
    "shadow_rgb": [0.03, -0.01, -0.03],
    "highlight_rgb": [0.05, 0.02, -0.05],
    "strength_default": 0.6,
    "pre_saturation": -15
}
```

保存后即可运行：

```bash
python retouch.py grade photo.jpg -o vintage.jpg --preset vintage
```

## 输出格式

- 输出为 `.tif` / `.tiff` 时保存为 16-bit TIFF。
- 输出为 `.png` 时保存为 16-bit PNG（若可用）。
- 输出为 `.jpg` / `.jpeg` 时保存为 8-bit JPEG。

## 注意事项

- RAW 文件会通过 `rawpy` 自动解码为 sRGB 色彩空间，并应用相机白平衡与自动亮度。
- 直方图与统计基于 sRGB 伽马编码的亮度值。
- 色温调整默认是相对偏移，适合所有图像；使用 `--kelvin` 可设置绝对色温。
- `style.md` 文件应位于脚本同一目录下，或通过环境变量 `STYLE_MD_PATH` 指定路径。
