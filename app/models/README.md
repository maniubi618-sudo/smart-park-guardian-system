# 模型说明文档

## 目录结构

```
app/models/
├── helmet_model.pt          # 安全帽检测模型
├── vest_model.pt            # 反光衣检测模型
├── yolo11s.pt               # 人体/车辆检测模型
├── fire_smoke_seg_model.pt  # 火焰/烟雾检测模型
├── crop_pest.pt             # 作物病虫害检测模型（需添加）
├── crop_growth.pt           # 作物长势异常检测模型（需添加）
├── crop_fruit.pt            # 果实成熟度检测模型（需添加）
└── README.md                # 本文档
```

## 告警类型说明

| 告警类型代码 | 名称 | 说明 | 所需模型 |
|-------------|------|------|---------|
| 0 | 安全规范 | 检测未戴安全帽、未穿反光衣 | helmet_model.pt, vest_model.pt |
| 1 | 区域入侵 | 检测人员、车辆入侵 | yolo11s.pt |
| 2 | 火警 | 检测火焰、烟雾 | fire_smoke_seg_model.pt |
| 3 | 作物病虫害 | 检测作物叶片病虫害 | crop_pest.pt |
| 4 | 作物长势异常 | 检测作物生长状态异常 | crop_growth.pt |
| 5 | 果实成熟度 | 检测果实成熟程度 | crop_fruit.pt |

## 如何添加作物检测模型

### 1. 数据集准备

#### 作物病虫害检测
推荐使用 PlantVillage 数据集：
- GitHub: https://github.com/spMohanty/PlantVillage-Dataset
- 包含 54,306 张图像，14 种作物，26 种病害
- 使用方式：
  ```python
  from datasets import load_dataset
  dataset = load_dataset("mohanty/PlantVillage", "color")
  ```

#### 果实成熟度检测
推荐参考以下项目：
- 咖啡成熟度: https://github.com/share2code99/coffee_ripeness_detection_yolo11
- 芒果成熟度: https://github.com/share2code99/mango_ripeness_segmentation_yolo11

### 2. 模型训练

使用 ultralytics YOLO 训练模型：

```python
from ultralytics import YOLO

# 加载预训练模型
model = YOLO('yolo11s.pt')

# 训练模型
results = model.train(
    data='your_dataset.yaml',  # 你的数据集配置文件
    epochs=100,
    imgsz=640,
    batch=16,
    name='crop_pest'
)

# 导出模型
model.export(format='pt')
```

### 3. 模型部署

将训练好的模型文件重命名并放置到 `app/models/` 目录：

- 病虫害检测模型 → `crop_pest.pt`
- 长势异常检测模型 → `crop_growth.pt`
- 果实成熟度检测模型 → `crop_fruit.pt`

### 4. 验证

重新启动服务，模型会自动加载（如果文件存在）。

## 数据集配置文件示例 (dataset.yaml)

```yaml
path: ./datasets/crop_pest  # 数据集根目录
train: images/train          # 训练集图像目录
val: images/val              # 验证集图像目录
test: images/test            # 测试集图像目录

nc: 26                       # 类别数量
names: ['病害1', '病害2', ...]  # 类别名称列表
```

## 注意事项

1. 如果模型文件不存在，系统会记录警告日志，但不会影响现有功能的正常运行
2. 所有模型使用统一的输入尺寸 640x640 或 320x320（推理时）
3. 模型置信度阈值默认为 0.5
4. 新增模型后，需要在相应的摄像头配置中选择对应的告警类型

## 技术支持

- YOLO 官方文档: https://docs.ultralytics.com/
- PlantVillage 数据集: https://github.com/spMohanty/PlantVillage-Dataset
