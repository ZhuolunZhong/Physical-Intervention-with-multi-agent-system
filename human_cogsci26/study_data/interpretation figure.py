import matplotlib.pyplot as plt
import numpy as np
import os

# 获取当前脚本文件所在路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(8, 10))

# 设置网格大小：4行3列
rows, cols = 4, 3

# 绘制网格线（只绘制外边框）
ax.plot([0, cols], [0, 0], color='black', linewidth=2)  # 上边框
ax.plot([0, cols], [rows, rows], color='black', linewidth=2)  # 下边框
ax.plot([0, 0], [0, rows], color='black', linewidth=2)  # 左边框
ax.plot([cols, cols], [0, rows], color='black', linewidth=2)  # 右边框

# 绘制内部网格线（不绘制单个单元格内部的线条）
for i in range(1, rows):
    ax.plot([0, cols], [i, i], color='black', linewidth=2)
for j in range(1, cols):
    ax.plot([j, j], [0, rows], color='black', linewidth=2)

# 设置坐标轴范围
ax.set_xlim(0, cols)
ax.set_ylim(0, rows)

# 反转y轴，使左上角为(0,0)
ax.invert_yaxis()

# 绘制黑色单元格 (1,1)
black_cell = plt.Rectangle((1, 1), 1, 1, color='black', alpha=0.7)
ax.add_patch(black_cell)

# 在黑色单元格(1,1)的8个方向绘制箭头
center_x, center_y = 1.5, 1.5  # 单元格中心坐标

# 定义8个方向的箭头
arrows = [
    (0, -1, 'red'),      # 向上（红色）
    (1, -1, 'white'),    # 右上
    (1, 0, 'white'),     # 向右
    (1, 1, 'blue'),     # 右下
    (0, 1, 'white'),     # 向下
    (-1, 1, 'white'),     # 左下（蓝色）
    (-1, 0, 'white'),    # 向左
    (-1, -1, 'white')    # 左上
]

# 绘制箭头
for dx, dy, color in arrows:
    ax.arrow(center_x, center_y, dx*0.3, dy*0.3, 
             head_width=0.1, head_length=0.1, 
             fc=color, ec=color, linewidth=2)

# 绘制红色单元格 (0,1)
red_cell = plt.Rectangle((1, 0), 1, 1, color='red', alpha=0.7)
ax.add_patch(red_cell)

# 绘制蓝色单元格 (2,3) - 注意网格只有3列，所以这里改为(2,2)
blue_cell = plt.Rectangle((2, 3), 1, 1, color='blue', alpha=0.7)
ax.add_patch(blue_cell)

# 移除标题和刻度
ax.set_xticks([])
ax.set_yticks([])
ax.set_title('')

# 设置网格样式
ax.set_aspect('equal')

# 保存图像到当前脚本所在目录
output_path = os.path.join(current_dir, 'interpretation.png')
plt.savefig(output_path, bbox_inches='tight', dpi=300)


print(f"图像已保存到: {output_path}")