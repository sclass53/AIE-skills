<!-- 颜色分级预设文件 -->
<!-- 此文件为 JSON 格式，键为预设名称，值为参数对象。 -->
<!-- 参数说明：
  shadow_rgb: 阴影偏移 (R,G,B)，范围约 -0.3 ~ 0.3
  highlight_rgb: 高光偏移 (R,G,B)，范围约 -0.3 ~ 0.3
  strength_default: 默认强度 (0~1)
  pre_saturation: 可选，应用预设前先调整饱和度 (数值，-100~+100)
  scene: 适用场景的文字描述。选择预设前必须先读 scene，
         判断与当前图像内容是否匹配；不匹配就不要用该预设。
-->
<!-- 请勿删除注释，下方 JSON 为有效数据 -->

{
    "teal-orange": {
        "shadow_rgb": [-0.06, 0.03, 0.06],
        "highlight_rgb": [0.07, 0.02, -0.07],
        "strength_default": 0.8,
        "pre_saturation": null,
        "scene": "城市建筑、夜景霓虹、街拍、玻璃幕墙、科幻感城市风光。慎用于人像：橙色高光会让肤色发脏发橘、青色阴影让皮肤显病态，人像特写禁止使用"
    },
    "cold-gray": {
        "shadow_rgb": [0.0, 0.0, 0.07],
        "highlight_rgb": [0.02, 0.02, 0.05],
        "strength_default": 0.8,
        "pre_saturation": -40,
        "scene": "阴天城市、极简建筑、工业风、雨天街道、混凝土/钢结构。不适合人像：低饱和加冷调会让肤色发灰发青、气色差"
    },
    "warm": {
        "shadow_rgb": [0.02, 0.01, -0.02],
        "highlight_rgb": [0.08, 0.03, -0.06],
        "strength_default": 0.8,
        "pre_saturation": null,
        "scene": "人像（通用，让肤色红润健康）、室内暖光、咖啡店、家居、烛光晚餐、食物摄影"
    },
    "cool": {
        "shadow_rgb": [-0.02, -0.01, 0.05],
        "highlight_rgb": [-0.03, -0.02, 0.07],
        "strength_default": 0.8,
        "pre_saturation": null,
        "scene": "雪景、海边清晨、蓝天下的现代建筑、冷色调静物、冬日户外。人像慎用，除非追求清冷情绪感"
    },
    "noir": {
        "shadow_rgb": [0, 0, 0],
        "highlight_rgb": [0, 0, 0],
        "strength_default": 0.8,
        "pre_saturation": -100,
        "scene": "黑白艺术处理：强光影建筑、街头纪实、几何线条、情绪人像（需用户明确想要黑白时再用）"
    },
    "moody": {
        "shadow_rgb": [-0.02, -0.01, 0.04],
        "highlight_rgb": [0.04, 0.02, -0.02],
        "strength_default": 0.7,
        "pre_saturation": -20,
        "scene": "乌云密布的风景、废墟、森林迷雾、暴风雨前的海面、压抑氛围创作。人像慎用，会显得阴郁"
    },
    "golden-hour": {
        "shadow_rgb": [0.03, 0.01, -0.04],
        "highlight_rgb": [0.08, 0.06, -0.08],
        "strength_default": 0.6,
        "pre_saturation": 10,
        "scene": "日落/日出时的人像逆光、金色阳光下的风景、麦田、海边夕阳，让画面温暖通透"
    },
    "cinematic": {
        "shadow_rgb": [-0.03, -0.02, 0.05],
        "highlight_rgb": [0.05, 0.03, -0.05],
        "strength_default": 0.75,
        "pre_saturation": -10,
        "scene": "城市街道、建筑、电影感叙事画面、夜晚路灯下的场景。人像特写慎用，大远景中人物较小可用"
    }
}
