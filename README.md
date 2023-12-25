# Image Cropper

**图像剪裁工具**
代码基于![isat](https://github.com/yatengLG/ISAT_with_segment_anything)实现
![demo](demo.png)


## Installation

```shell
conda create -n isat_env python=3.8
conda activate isat_env

git clone https://github.com/lchen1019/Image_Cropper.git
cd Image_Cropper
pip install -r requirements.txt

python main.py
```

## Usage
### 1. 基本功能
**Menu**
- Files: 打开图像文件夹，标签文件夹
- View: 预览剪裁结果
- Convert: 剪裁（需要选择保存至的文件夹）

**Toolbar**
- 矩形图标: 进入选款模式
- 对号: 确定这个选框
- 保存图标：保存这个选款
- 垃圾桶图标:  清空当前剪裁结果

### 2. 快捷键
- e 保存当前矩形
- q 选择正方形
- s 保存当前剪裁结果
- space 预览结果
