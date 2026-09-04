<!-- 颜色分级预设文件 -->
<!-- 此文件为 JSON 格式，键为预设名称，值为参数对象。 -->
<!-- 参数说明：
  shadow_rgb: 阴影偏移 (R,G,B)，范围约 -0.3 ~ 0.3
  highlight_rgb: 高光偏移 (R,G,B)，范围约 -0.3 ~ 0.3
  strength_default: 默认强度 (0~1)
  pre_saturation: 可选，应用预设前先调整饱和度 (数值，-100~+100)
-->
<!-- 请勿删除注释，下方 JSON 为有效数据 -->

{
    "teal-orange": {
        "shadow_rgb": [-0.06, 0.03, 0.06],
        "highlight_rgb": [0.07, 0.02, -0.07],
        "strength_default": 0.8,
        "pre_saturation": null
    },
    "cold-gray": {
        "shadow_rgb": [0.0, 0.0, 0.07],
        "highlight_rgb": [0.02, 0.02, 0.05],
        "strength_default": 0.8,
        "pre_saturation": -40
    },
    "warm": {
        "shadow_rgb": [0.02, 0.01, -0.02],
        "highlight_rgb": [0.08, 0.03, -0.06],
        "strength_default": 0.8,
        "pre_saturation": null
    },
    "cool": {
        "shadow_rgb": [-0.02, -0.01, 0.05],
        "highlight_rgb": [-0.03, -0.02, 0.07],
        "strength_default": 0.8,
        "pre_saturation": null
    },
    "noir": {
        "shadow_rgb": [0, 0, 0],
        "highlight_rgb": [0, 0, 0],
        "strength_default": 0.8,
        "pre_saturation": -100
    },
    "moody": {
        "shadow_rgb": [-0.02, -0.01, 0.04],
        "highlight_rgb": [0.04, 0.02, -0.02],
        "strength_default": 0.7,
        "pre_saturation": -20
    },
    "golden-hour": {
        "shadow_rgb": [0.03, 0.01, -0.04],
        "highlight_rgb": [0.08, 0.06, -0.08],
        "strength_default": 0.6,
        "pre_saturation": 10
    },
    "cinematic": {
        "shadow_rgb": [-0.03, -0.02, 0.05],
        "highlight_rgb": [0.05, 0.03, -0.05],
        "strength_default": 0.75,
        "pre_saturation": -10
    }
}