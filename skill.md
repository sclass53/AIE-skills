---
name: photo-edit
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

### 用户喜好

建议在用户要求你调整图片的过程中逐渐了解用户的喜好，并在下次调整图片的时候以喜好为准。可将喜好记录在 `taste.md` 中，以文本形式保存，例如：

```md
- 用户喜欢暖色调，
```

## 推荐调整流程

1. **观察图像**  
   使用 `inspect` 命令查看图像基本信息、亮度统计和 ASCII 缩略图，快速判断曝光、构图和色彩倾向。

2. **检查直方图**  
   使用 `histogram` 命令获取曝光数据。重点关注：  
   - `underexposed_ratio` 和 `overexposed_ratio`：判断整体曝光是否准确。  
   - `clipped_shadow_ratio` 和 `clipped_highlight_ratio`：检查是否有死黑或死白。  
   - `median` 与 `mean`：若中位数明显偏离 0.5，可能需要曝光补偿。

3. **调整曝光**  
   根据直方图结果，使用 `adjust` 命令的 `--exposure` 参数进行整体曝光补偿。通常以 0.1~0.5 EV 步长微调，避免高光溢出。

4. **恢复阴影与高光细节**  
   使用 `--shadow` 提亮阴影区域，使用 `--highlight` 压暗高光区域。参考直方图，确保 `clipped_*` 比例降低，同时保留合理对比度。

5. **调整白平衡与色彩倾向**  
   - 若已知场景色温，可使用 `--kelvin` 设置绝对色温。  
   - 若仅需微调，使用 `--temperature`（暖/冷）和 `--tint`（绿/品红）。  
   - 可结合 EXIF 中的 `WhiteBalance` 信息决定是否保留相机白平衡。

6. **优化对比度与饱和度**  
   使用 `--contrast` 和 `--saturation` 增强或减弱画面冲击力。注意不要过度饱和导致色彩溢出。

7. **应用颜色分级**  
   使用 `list-presets` 查看可用预设，然后选择合适风格（如 `teal-orange`、`cold-gray`、`cinematic` 等）执行 `grade` 命令。可通过 `--strength` 控制效果强度。  
   若用户有自己的偏好，可编辑 `style.md` 添加自定义预设。

8. **输出与检查**  
   调整完成后保存为高质量格式（如 16-bit TIFF），并可再次运行 `inspect` 和 `histogram` 验证最终效果。
   此外，可以将用户喜好以文本记录在taste.md中，并且可将此次预设（若用户喜欢的话）记录在style.md中，以便复用，增强对用户品味的学习。

> **提示**：每一步调整都可以单独输出中间文件，以便回溯和比较。对于 RAW 文件，脚本会自动应用相机白平衡和自动亮度，因此初始直方图可能已经比较均衡。

### 修图准则

1. 饱和度不要太高，太高了反而刺眼。
2. 直方图中间值偏低时，适当提亮阴影和整体曝光。
3. 直方图表示的是每个亮度的像素分布，建议第一步先按需调整曝光和阴影/高光。例如，若直方图中间偏高，两边过低，则说明对比度不够。
4. 不要更改原图，修改后的原图不要覆盖原始图像。

## 输出格式

- 输出为 `.tif` / `.tiff` 时保存为 16-bit TIFF。
- 输出为 `.png` 时保存为 16-bit PNG（若可用）。
- 输出为 `.jpg` / `.jpeg` 时保存为 8-bit JPEG。

## 注意事项

- RAW 文件会通过 `rawpy` 自动解码为 sRGB 色彩空间，并应用相机白平衡与自动亮度。
- 直方图与统计基于 sRGB 伽马编码的亮度值。
- 色温调整默认是相对偏移，适合所有图像；使用 `--kelvin` 可设置绝对色温。
- `style.md` 文件应位于脚本同一目录下，或通过环境变量 `STYLE_MD_PATH` 指定路径。
