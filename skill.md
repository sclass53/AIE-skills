---
name: photo-edit
description: 专业修图师技能。支持查看直方图、提取EXIF镜头信息、调整色温/高光/阴影/曝光/对比度/饱和度、局部修图（径向/矩形局部调整、瑕疵修复、磨皮）、降噪、丁达尔光（体积光）、构图裁剪、青橙/冷灰等颜色分级、观察图像，并支持RAW文件。
---

# 修图师 Skill

本技能通过命令行脚本 `retouch.py` 完成照片处理。适用文件包括 JPEG、PNG、TIFF 以及常见 RAW 格式（如 .dng, .nef, .cr2, .cr3, .arw, .orf, .rw2, .raf 等）。

## 安装依赖

```bash
pip install -r requirements.txt
```

> `heal`（瑕疵修复）与 `denoise`（降噪）在安装 `opencv-python` 后效果最佳（requirements.txt 已包含）。未安装时脚本会自动回退到简化算法，效果略差但可用。

## 命令概览

| 命令 | 功能 |
|------|------|
| `inspect`   | 观察图像：尺寸、平均颜色、亮度统计、ASCII 缩略图 |
| `histogram` | 查看直方图，返回曝光数字（均值/中位数/欠曝过曝比例/通道均值等） |
| `exif`      | 获取 EXIF 信息，重点包含镜头信息与 ISO |
| `adjust`    | 全局调整：色温、色调、曝光、对比度、饱和度、高光、阴影 |
| `local`     | 局部调整：对圆形/矩形区域单独施加曝光、色温、饱和度、模糊（磨皮）等 |
| `heal`      | 瑕疵修复：点掉痘痘、痣、污点、灰点等小面积瑕疵，支持一次多点 |
| `denoise`   | 降噪：去除高 ISO 噪点与彩色噪点，保留细节 |
| `tyndall`   | 丁达尔光（体积光/耶稣光）：从光源位置放射光束，增强光线氛围感 |
| `crop`      | 按归一化坐标裁剪图像（构图裁切） |
| `grade`     | 颜色偏移/分级：青橙、冷灰、暖调、冷调、黑白等预设 |
| `list-presets` | 列出所有颜色分级预设及其适用场景（含 presets.md 中自定义预设） |
| `show`      | 用系统默认看图软件打开图像（修图完成后向用户展示成品） |

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

### 全局调整（色温/曝光/高光/阴影等）
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

### 局部调整（局部修图的基础工具）
对画面某个区域单独施加调整，其余部分不变。圆形区域（径向渐变）：
```bash
python retouch.py local photo.jpg -o out.jpg \
    --cx 0.5 --cy 0.4 --radius 0.25 --feather 0.5 \
    --exposure 0.3 --temperature 10 --saturation -5
```
矩形区域：
```bash
python retouch.py local photo.jpg -o out.jpg \
    --shape rect --left 0.6 --top 0.0 --right 1.0 --bottom 0.4 --temperature 25
```
- `--cx/--cy`：区域中心，归一化坐标（x 相对宽度、y 相对高度，0~1，左上角为原点）。
- `--radius`：半径，相对图像短边的比例（0~1）。
- `--shape`：`radial` 圆形（默认）或 `rect` 矩形；矩形用 `--left/--top/--right/--bottom` 定界。
- `--feather`：羽化比例 0~1，控制边缘过渡的柔和度，默认 0.5。处理人脸皮肤时建议 ≥0.5，避免出现明显边界。
- `--exposure/--temperature/--tint/--contrast/--saturation/--highlight/--shadow`：含义与 `adjust` 相同，只作用于区域内。
- `--blur`：局部模糊/柔肤 0~10，实际高斯半径随图像尺寸缩放。磨皮建议 2~5，宁轻勿重。

### 瑕疵修复（祛痘/去污点）
```bash
python retouch.py heal photo.jpg -o out.jpg \
    --spot 0.42,0.35,0.012 --spot 0.55,0.40,0.010
```
- `--spot x,y,r`：可重复多次。x、y 为归一化坐标（0~1），r 为瑕疵半径（相对图像短边，常用 0.005~0.02）。
- 通过采样瑕疵周围像素进行内容填充，适合痘痘、痣、灰尘、镜头污点等小面积瑕疵。
- **坐标必须先看图确认**：建议先把目标区域 `crop` 成临时文件放大观察，估算归一化坐标后再执行。

### 降噪
```bash
python retouch.py denoise photo.jpg -o out.jpg --strength 0.6
```
- `--strength` 0~1：0.3 以下轻微去彩噪；0.5~0.7 通用；>0.8 用于高 ISO 严重噪点（可能损失细节）。
- **何时需要**：EXIF 中 ISO ≥ 800、暗光/夜景/室内抓拍、inspect 或放大观察时可见颗粒与彩色噪点。
- 大尺寸图像降噪较慢，属正常现象。降噪应放在磨皮与颜色分级之前。

### 丁达尔光（体积光）
```bash
python retouch.py tyndall photo.jpg -o out.jpg \
    --source-x 0.7 --source-y 0.2 --strength 0.5 --rays 14 --length 0.8 --warmth 0.7
```
- `--source-x/--source-y`：光源位置（归一化坐标）。缺省时自动定位在画面最亮区域（如太阳、天空亮部）。
- `--strength`：强度 0~1，建议 0.3~0.6，宁轻勿重。
- `--rays`：光束条数（角向条纹频率），8~20 比较自然；设 0 则只加柔光不加条纹。
- `--length`：光束延伸长度 0~1。
- `--warmth`：光线暖度 0~1，逆光/夕阳场景建议 0.6~0.9。
- `--threshold`：参与发光的亮度阈值 0~1（默认 0.65）。画面整体偏暗时可降到 0.45~0.55。

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
**选择预设前必须先做场景匹配**：运行 `list-presets`，每个预设都带有 `scene` 适用场景描述。先看图判断当前画面内容（建筑？人像？风景？），再选 `scene` 与之匹配的预设。
- 同时对照 `styles.yml` 中命中照片类型的 guidance：各类型的调色禁忌（什么类型禁用什么影调）都记录在那里。
- 拿不准时用 `--strength 0.5~0.6` 保守尝试，并让用户确认。

### 列出所有颜色分级预设
```bash
python retouch.py list-presets
```
输出包含每个预设的 `scene` 适用场景描述，选预设前务必阅读并与当前画面内容对照。

### 展示图像（用系统默认软件打开）
修图完成后向用户展示成品：
```bash
python retouch.py show out.jpg
```
所有输出类命令（adjust、crop、local、heal、denoise、tyndall、grade）都支持 `--show`，保存成功后自动用系统默认看图软件打开结果：
```bash
python retouch.py grade photo.jpg -o graded.jpg --preset warm --show
```
（也可以用 `show` 打开原图或中间文件，便于与成品对比。）

### 自定义预设
颜色分级预设存储在 `presets.md` 中（JSON 格式）。用户可以直接编辑该文件，添加新的预设条目，即可在 `grade` 命令中使用 `--preset 名称` 调用。例如添加：

```json
"vintage": {
    "shadow_rgb": [0.03, -0.01, -0.03],
    "highlight_rgb": [0.05, 0.02, -0.05],
    "strength_default": 0.6,
    "pre_saturation": -15,
    "scene": "适用场景描述（必填）：说明该预设适合什么画面内容、不适合什么。例如人像慎用/建筑适用等"
}
```

`scene` 字段用自然语言描述适用场景，会在 `list-presets` 时显示，帮助选择时避开不匹配的画面内容（如给人像用了建筑调）。

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
   若你能观察图像，建议用眼睛再观察一下图像。
   
2. **检查直方图与 EXIF**  
   使用 `histogram` 命令获取曝光数据。重点关注：  
   - `underexposed_ratio` 和 `overexposed_ratio`：判断整体曝光是否准确。  
   - `clipped_shadow_ratio` 和 `clipped_highlight_ratio`：检查是否有死黑或死白。  
   - `median` 与 `mean`：若中位数明显偏离 0.5，可能需要曝光补偿。
   使用 `exif` 查看 ISO：高 ISO（≥800）提示后面需要降噪。

3. **全局基础调整**  
   根据直方图用 `adjust` 做 `--exposure`（0.1~0.5 EV 步长）、`--shadow`/`--highlight` 恢复、`--temperature`/`--tint` 白平衡、`--contrast`/`--saturation` 微调。
   **若在 `styles.yml` 中命中了照片类型，此步按该类型 guidance 中的曝光/白平衡要求执行**（如人像的肤色标准）。

4. **按类型专项处理**  
   依据 `styles.yml` 中命中条目的 guidance 进行专项处理（例如人像的祛瑕疵/磨皮、风光的构图检查与丁达尔光），命中条目带 `doc` 时先阅读该风格文档。

5. **降噪（如需要）**  
   发现噪点（高 ISO、暗部彩噪、明显颗粒）时，用 `denoise` 处理。放在磨皮与颜色分级之前效果最好。

6. **构图裁切**  
   按 `styles.yml` 中命中类型的构图建议检查画面，用 `crop` 裁掉干扰物、修正构图。

7. **应用颜色分级**  
   使用 `list-presets` 查看可用预设，**先阅读每个预设的 `scene` 场景描述，与当前画面内容匹配后才可选用**，再对照 `styles.yml` 中命中类型的调色禁忌确认无误，然后执行 `grade`。可通过 `--strength` 控制效果强度。  
   若用户有自己的偏好，可编辑 `presets.md` 添加自定义预设。

8. **输出、复查与展示（必做，见【收尾自查清单】）**  
   调整完成后保存为高质量格式（如 16-bit TIFF），再次运行 `inspect` 并亲眼复查成品。
   **向用户展示**：复查通过后，用 `show` 命令（或在最后一步输出命令上加 `--show`）用系统默认看图软件打开成品照片给用户看。
   可将用户喜好记录在 taste.md 中，并可将此次预设（若用户喜欢）记录在 presets.md 中以便复用。

---

## 照片类型与风格要求（styles.yml，必读）

摄影类型繁多，**类型相关的建议与禁忌不在本文件中，统一记录在技能目录下的 `styles.yml`**（与 SKILL.md 同目录）。本文件只保留适用于所有照片的通用准则。

修图时按以下方式使用 `styles.yml`：

1. **判断照片类型**：观察画面内容，可结合 EXIF（焦段、光圈、ISO、拍摄时间）辅助判断。
2. **查找匹配条目**：打开 `styles.yml`，将画面与 `styles` 下各条目的 `match` 字段对照，找到匹配的类型。可能同时命中多个类型（如"夜景人像"同时匹配 portrait 与 night），此时合并遵循所有命中条目的 guidance，冲突时以更具体的类型为准。
3. **遵循 guidance**：命中条目的 `guidance` 包含这类照片的建议与禁忌（曝光/肤色标准、构图思路、调色禁忌、该做与不该做的特效等），必须遵循。
4. **阅读 doc 文档**：条目带有 `doc` 字段时，先完整阅读该字段指向的风格文档（路径相对 `styles.yml` 所在目录）再动手。
5. **无匹配时**：没有任何条目匹配就按本文件的通用准则处理，不要硬套某种风格。

`styles.yml` 由用户维护，可自行新增类型条目或补充风格文档。若你发现某类照片反复出现却没有对应条目，可以建议用户添加。

## 收尾自查清单（每次修图完成后必做）

> **⚠️ 复查提醒——再看一眼，别急着交付**
>
> 1. **再次观察图像**：用 `inspect` 输出统计数据 + 亲眼查看成品，逐项检查：
>    - **玻璃反光、镜面反光、镜头眩光、灰尘斑点**等明显瑕疵：小面积的用 `heal` 点掉，大面积反光可用 `local` 压暗高光缓解；处理不了要明确告知用户，不要假装不存在；
>    - 边缘是否有裁切残留的杂物、半截肢体/树枝；
>    - 过度调整的痕迹：肤色是否蜡像、光效是否穿帮、饱和度是否溢出。
> 2. **噪点检查**：若复查时发现噪点（暗部彩噪、高 ISO 颗粒），用 `denoise --strength 0.5~0.7` 处理后再复查一次。
> 3. **合理裁切**：最后再审视一次构图，必要时用 `crop` 二次裁切。
> 4. 全部通过后用 `show` 打开成品向用户展示，再交付；并按需把用户喜好写入 `taste.md`、把受欢迎的预设写入 `presets.md`。

### 修图准则

1. 饱和度不要太高，太高了反而刺眼。
2. 直方图中间值偏低时，适当提亮阴影和整体曝光。
3. 直方图表示的是每个亮度的像素分布，建议第一步先按需调整曝光和阴影/高光。例如，若直方图中间偏高，两边过低，则说明对比度不够。
4. 特效类操作（丁达尔光、磨皮、局部调整）宁可轻微不可过度——过度的痕迹会毁掉照片的真实感。
5. 降噪放在磨皮和颜色分级之前；磨皮避开五官和轮廓。
6. 多步操作时使用链式中间文件（a → b → c），便于回溯比较。
7. 颜色分级预设必须与画面内容匹配：先读 `list-presets` 中的 `scene` 描述，再对照 `styles.yml` 中命中照片类型的调色禁忌确认无误后才选用。
8. 不要更改原图，修改后的结果不要覆盖原始图像。

## 输出格式

- 输出为 `.tif` / `.tiff` 时保存为 16-bit TIFF。
- 输出为 `.png` 时优先 16-bit，若环境不支持则自动回退 8-bit。
- 输出为 `.jpg` / `.jpeg` 时保存为 8-bit JPEG。

## 注意事项

- RAW 文件会通过 `rawpy` 自动解码为 sRGB 色彩空间，并应用相机白平衡与自动亮度。
- 直方图与统计基于 sRGB 伽马编码的亮度值。
- 色温调整默认是相对偏移，适合所有图像；使用 `--kelvin` 可设置绝对色温。
- 所有坐标类参数（crop、local、heal、tyndall 的位置）都是归一化坐标：x 相对宽度、y 相对高度，0~1，左上角为原点。
- `presets.md`（颜色分级预设）与 `styles.yml`（摄影风格库）位于技能根目录或脚本同目录下均可被找到；`presets.md` 的路径也可通过环境变量 `PRESETS_MD_PATH` 指定。
