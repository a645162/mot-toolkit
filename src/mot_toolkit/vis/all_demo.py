"""
多配色方案演示程序

这个脚本可以同时绘制多个配色方案的演示图表，便于比较不同配色方案的效果
"""

import os
import importlib
import inspect

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.gridspec as gridspec
import seaborn as sns

from mot_toolkit.vis.base_colors import BaseColorScheme
from mot_toolkit.vis.sigewinne_colors import SIGEWINNEColorScheme
from mot_toolkit.vis.varesa_colors import VARESAColorScheme


def setup_figure_style():
    """设置全局图表样式"""
    plt.style.use("default")
    # 设置全局字体为微软雅黑
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False  # 正确显示负号
    # 设置其他参数
    plt.rcParams["figure.figsize"] = (10, 8)
    plt.rcParams["figure.dpi"] = 100


def create_color_palette_demo(scheme, output_dir):
    """创建配色方案展示图"""
    colors = scheme.colors
    hex_colors = scheme.hex_colors()
    scheme_name = scheme.__class__.__name__

    fig, axes = plt.subplots(1, 5, figsize=(12, 2))
    fig.suptitle(f"{scheme.name}示例", fontsize=16)

    for i, (color, hex_color) in enumerate(zip(colors, hex_colors)):
        axes[i].add_patch(plt.Rectangle((0, 0), 1, 1, color=hex_color, ec="black"))
        r, g, b = color
        axes[i].text(0.5, -0.2, f"R: {r:03d}", ha="center", transform=axes[i].transAxes)
        axes[i].text(
            0.5, -0.35, f"G: {g:03d}", ha="center", transform=axes[i].transAxes
        )
        axes[i].text(0.5, -0.5, f"B: {b:03d}", ha="center", transform=axes[i].transAxes)
        axes[i].axis("off")

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_colors.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_ridge_plot(scheme, output_dir):
    """创建示波图(Ridge Plot)"""
    scheme_name = scheme.__class__.__name__
    
    # 设置样本名称
    samples = [
        "Samp A",
        "Samp B",
        "Samp C",
        "Samp D",
        "Samp E",
        "Samp F",
        "Samp G",
        "Samp H",
        "Samp I",
        "Samp J",
    ]

    # 生成x轴数据
    x = np.linspace(0, 90, 500)

    # 为每个样本生成模拟数据
    np.random.seed(42)  # 固定随机数生成

    # 创建图形
    fig, ax = plt.subplots(figsize=(10, 8))

    # 创建颜色映射
    colors = scheme.hex_colors()
    # 反向排列以便底部为红色，顶部为蓝色
    colors = colors[::-1]

    # 定义各样本的峰值位置和宽度
    centers = [35, 32, 40, 42, 50, 55, 45, 50, 45, 35]
    widths = [8, 10, 15, 12, 18, 15, 10, 8, 12, 5]
    heights = [0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.15, 0.12, 0.1, 0.1]

    # 绘制每个样本的波形
    for i, sample in enumerate(samples):
        # 使用高斯分布生成波形
        y_base = i * 1.0  # 设置基线位置

        mu = centers[i]
        sigma = widths[i]
        height = heights[i]

        # 创建主波形
        y = y_base + height * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        # 添加次波形（如有）
        if i < 5:  # 只给前几个样本添加次波形
            mu2 = mu + 20
            sigma2 = sigma * 0.7
            height2 = height * 0.7
            y += height2 * np.exp(-0.5 * ((x - mu2) / sigma2) ** 2)

        # 填充区域
        ax.fill_between(x, y_base, y, color=colors[min(i, len(colors) - 1)], alpha=0.8)

        # 绘制波形线条
        ax.plot(x, y, color="black", linewidth=1)

        # 添加样本标签
        ax.text(0, y_base + 0.05, sample, fontsize=9, va="bottom")

    # 设置图表属性
    ax.set_xlim(0, 90)
    ax.set_ylim(-0.5, len(samples))
    ax.set_xticks(np.arange(0, 91, 10))
    ax.set_yticks([])
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)

    ax.set_title(f"{scheme.name}示波图", fontsize=14)

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_ridge_plot.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_bar_chart(scheme, output_dir):
    """创建柱状图示例"""
    scheme_name = scheme.__class__.__name__
    
    categories = ["S1", "S2", "S3", "S4"]
    values = [0.34, 0.49, 0.32, 0.42]

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(categories, values, color=scheme.hex_colors()[:4])
    ax.set_ylim(0, 0.6)
    ax.set_title("样本数据分布")
    ax.set_ylabel("相对频率")
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_bar.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_stacked_area_chart(scheme, output_dir):
    """创建堆叠面积图"""
    scheme_name = scheme.__class__.__name__
    
    x = np.arange(1, 11)
    data1 = np.array([1, 2, 4, 8, 12, 16, 14, 10, 7, 3])
    data2 = np.array([2, 5, 8, 12, 15, 18, 15, 14, 10, 5])
    data3 = np.array([1, 3, 6, 14, 17, 19, 16, 12, 8, 4])
    data4 = np.array([1, 4, 8, 15, 20, 22, 18, 15, 10, 6])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.fill_between(x, 0, data1, alpha=0.8, color=scheme.hex_colors()[0], label="set 1")
    ax.fill_between(
        x, data1, data1 + data2, alpha=0.8, color=scheme.hex_colors()[1], label="set 2"
    )
    ax.fill_between(
        x,
        data1 + data2,
        data1 + data2 + data3,
        alpha=0.8,
        color=scheme.hex_colors()[2],
        label="set 3",
    )
    ax.fill_between(
        x,
        data1 + data2 + data3,
        data1 + data2 + data3 + data4,
        alpha=0.8,
        color=scheme.hex_colors()[3],
        label="set 4",
    )

    ax.set_xlim(1, 10)
    ax.set_ylim(0, 75)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_title("多序列趋势分析")

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_area.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_line_chart(scheme, output_dir):
    """创建多序列折线图"""
    scheme_name = scheme.__class__.__name__
    
    x = np.arange(1, 9)
    y1 = np.array([55, 20, 33, 15, 10, 15, 25, 5])
    y2 = np.array([7, 45, 20, 10, 55, 25, 15, 10])
    y3 = np.array([30, 50, 25, 15, 10, 20, 25, 20])
    y4 = np.array([40, 10, 15, 5, 10, 30, 20, 30])

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(x, y1, "o-", color=scheme.hex_colors()[0], label="samp1")
    ax.plot(x, y2, "s-", color=scheme.hex_colors()[1], label="samp2")
    ax.plot(x, y3, "^-", color=scheme.hex_colors()[3], label="samp3")
    ax.plot(x, y4, "D-", color=scheme.hex_colors()[4], label="samp4")

    ax.set_xlim(0, 8)
    ax.set_ylim(0, 60)
    ax.legend()
    ax.set_title("多序列波动对比")
    ax.grid(True, linestyle="--", alpha=0.3)

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_line.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_pie_chart(scheme, output_dir):
    """创建饼图"""
    scheme_name = scheme.__class__.__name__
    
    labels = ["North", "South", "East", "West"]
    sizes = [25, 25, 19, 31]

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(
        sizes,
        labels=labels,
        colors=scheme.hex_colors()[:4],
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"edgecolor": "w"},
    )
    ax.axis("equal")
    ax.set_title("区域分布")

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_pie.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_heatmap(scheme, output_dir):
    """创建热力图"""
    scheme_name = scheme.__class__.__name__
    
    # 创建连续色彩映射，从浅蓝到深粉
    colors_for_map = [
        scheme.hex_colors()[1],
        scheme.hex_colors()[2],
        scheme.hex_colors()[3],
        scheme.hex_colors()[4],
    ]
    cmap = LinearSegmentedColormap.from_list(f"{scheme_name.lower()}", colors_for_map, N=100)

    # 创建随机数据
    np.random.seed(42)
    data = np.random.rand(11, 17)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(data, cmap=cmap, annot=True, fmt=".2f", linewidths=0.5, ax=ax)
    ax.set_title("相关性分析热力图")
    ax.set_xlabel("K序列")
    ax.set_ylabel("A序列")

    # 修改x轴和y轴刻度标签
    x_labels = [f"K{i+1}" for i in range(data.shape[1])]
    y_labels = [f"A{i+1}" for i in range(data.shape[0])]
    ax.set_xticklabels(x_labels)
    ax.set_yticklabels(y_labels)

    plt.tight_layout()
    output_path = os.path.join(output_dir, f"{scheme_name}_heatmap.png")
    plt.savefig(output_path, dpi=300)
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_dashboard(scheme, output_dir):
    """创建仪表盘演示"""
    scheme_name = scheme.__class__.__name__
    
    setup_figure_style()

    fig = plt.figure(figsize=(16, 12))
    fig.suptitle(f"SCI论文插图 - {scheme.name}演示", fontsize=20, y=0.98)

    # 使用GridSpec来安排子图
    gs = gridspec.GridSpec(3, 3)

    # 添加配色方案展示
    ax_palette = fig.add_subplot(gs[0, :])
    for i, color in enumerate(scheme.hex_colors()):
        ax_palette.add_patch(plt.Rectangle((i, 0), 0.8, 1, color=color, ec="black"))
        r, g, b = scheme.colors[i]
        ax_palette.text(
            i + 0.4,
            0.5,
            f"R:{r:03d}\nG:{g:03d}\nB:{b:03d}",
            ha="center",
            va="center",
            fontsize=9,
        )
    ax_palette.set_xlim(-0.2, 5)
    ax_palette.set_ylim(-0.2, 1.2)
    ax_palette.set_title(f"{scheme.name}色板", fontsize=12)
    ax_palette.axis("off")

    # 添加柱状图
    ax_bar = fig.add_subplot(gs[1, 0])
    categories = ["S1", "S2", "S3", "S4"]
    values = [0.34, 0.49, 0.32, 0.42]
    ax_bar.bar(categories, values, color=scheme.hex_colors()[:4])
    ax_bar.set_ylim(0, 0.6)
    ax_bar.set_title("样本柱状图", fontsize=12)
    ax_bar.grid(True, linestyle="--", alpha=0.3, axis="y")

    # 添加折线图
    ax_line = fig.add_subplot(gs[1, 1])
    x = np.arange(1, 9)
    y1 = np.array([55, 20, 33, 15, 10, 15, 25, 5])
    y2 = np.array([7, 45, 20, 10, 55, 25, 15, 10])
    y3 = np.array([30, 50, 25, 15, 10, 20, 25, 20])
    y4 = np.array([40, 10, 15, 5, 10, 30, 20, 30])

    ax_line.plot(x, y1, "o-", color=scheme.hex_colors()[0], label="A")
    ax_line.plot(x, y2, "s-", color=scheme.hex_colors()[1], label="B")
    ax_line.plot(x, y3, "^-", color=scheme.hex_colors()[3], label="C")
    ax_line.plot(x, y4, "D-", color=scheme.hex_colors()[4], label="D")
    ax_line.set_title("多序列对比", fontsize=12)
    ax_line.grid(True, linestyle="--", alpha=0.3)
    ax_line.legend(fontsize=8)

    # 添加饼图
    ax_pie = fig.add_subplot(gs[1, 2])
    labels = ["北", "南", "东", "西"]
    sizes = [25, 25, 19, 31]
    ax_pie.pie(
        sizes,
        labels=labels,
        colors=scheme.hex_colors()[:4],
        autopct="%1.0f%%",
        startangle=90,
        wedgeprops={"edgecolor": "w"},
    )
    ax_pie.axis("equal")
    ax_pie.set_title("区域分布", fontsize=12)

    # 添加堆叠面积图
    ax_area = fig.add_subplot(gs[2, 0])
    x = np.arange(1, 11)
    data1 = np.array([1, 2, 4, 8, 12, 16, 14, 10, 7, 3])
    data2 = np.array([2, 5, 8, 12, 15, 18, 15, 14, 10, 5])
    data3 = np.array([1, 3, 6, 14, 17, 19, 16, 12, 8, 4])
    data4 = np.array([1, 4, 8, 15, 20, 22, 18, 15, 10, 6])

    ax_area.fill_between(
        x, 0, data1, alpha=0.8, color=scheme.hex_colors()[0], label="S1"
    )
    ax_area.fill_between(
        x, data1, data1 + data2, alpha=0.8, color=scheme.hex_colors()[1], label="S2"
    )
    ax_area.fill_between(
        x,
        data1 + data2,
        data1 + data2 + data3,
        alpha=0.8,
        color=scheme.hex_colors()[2],
        label="S3",
    )
    ax_area.fill_between(
        x,
        data1 + data2 + data3,
        data1 + data2 + data3 + data4,
        alpha=0.8,
        color=scheme.hex_colors()[3],
        label="S4",
    )
    ax_area.set_xlim(1, 10)
    ax_area.set_title("累积趋势", fontsize=12)
    ax_area.legend(fontsize=8)

    # 添加分组柱状图
    ax_grouped = fig.add_subplot(gs[2, 1])
    labels = ["s1", "s2", "s3", "s4"]
    group_a = [0.44, 0.31, 0.45, 0.19]
    group_b = [0.49, 0.35, 0.48, 0.33]
    group_c = [0.47, 0.34, 0.49, 0.26]
    group_d = [0.46, 0.33, 0.44, 0.24]

    x = np.arange(len(labels))
    width = 0.2

    ax_grouped.bar(
        x - 1.5 * width, group_a, width, label="A", color=scheme.hex_colors()[0]
    )
    ax_grouped.bar(
        x - 0.5 * width, group_b, width, label="B", color=scheme.hex_colors()[1]
    )
    ax_grouped.bar(
        x + 0.5 * width, group_c, width, label="C", color=scheme.hex_colors()[3]
    )
    ax_grouped.bar(
        x + 1.5 * width, group_d, width, label="D", color=scheme.hex_colors()[4]
    )

    ax_grouped.set_ylim(0, 0.6)
    ax_grouped.set_xticks(x)
    ax_grouped.set_xticklabels(labels)
    ax_grouped.legend(fontsize=8)
    ax_grouped.set_title("多组对比", fontsize=12)

    # 添加水平堆叠条形图
    ax_hbar = fig.add_subplot(gs[2, 2])
    categories = range(1, 10)
    ax_hbar.barh(1, 0.5, color=scheme.hex_colors()[0], label="S1")
    ax_hbar.barh(2, 1.0, color=scheme.hex_colors()[1], label="S2")
    ax_hbar.barh(3, 1.2, color=scheme.hex_colors()[2], label="S3")
    ax_hbar.barh(4, 1.5, color=scheme.hex_colors()[3], label="S4")
    ax_hbar.barh(5, 1.8, color=scheme.hex_colors()[4], label="S5")
    ax_hbar.barh(6, 2.0, color=scheme.hex_colors()[0], label="S6")

    ax_hbar.set_yticks(range(1, 7))
    ax_hbar.set_title("水平条形图", fontsize=12)
    ax_hbar.legend(fontsize=8)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    output_path = os.path.join(output_dir, f"{scheme_name}_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def create_comparison_dashboard(schemes, output_dir):
    """创建多配色方案对比仪表盘"""
    if len(schemes) < 2:
        print("需要至少两个配色方案进行比较")
        return
    
    setup_figure_style()
    
    fig = plt.figure(figsize=(16, 10 * len(schemes)))
    fig.suptitle("多配色方案对比", fontsize=24, y=0.99)
    
    # 为每个配色方案创建子图
    gs = gridspec.GridSpec(len(schemes), 3)
    
    for i, scheme in enumerate(schemes):
        scheme_name = scheme.__class__.__name__
        
        # 添加配色方案展示
        ax_palette = fig.add_subplot(gs[i, 0])
        for j, color in enumerate(scheme.hex_colors()):
            ax_palette.add_patch(plt.Rectangle((j, 0), 0.8, 1, color=color, ec="black"))
            r, g, b = scheme.colors[j]
            ax_palette.text(
                j + 0.4,
                0.5,
                f"R:{r:03d}\nG:{g:03d}\nB:{b:03d}",
                ha="center",
                va="center",
                fontsize=9,
            )
        ax_palette.set_xlim(-0.2, 5)
        ax_palette.set_ylim(-0.2, 1.2)
        ax_palette.set_title(f"{scheme.name}色板", fontsize=14)
        ax_palette.axis("off")
        
        # 添加折线图
        ax_line = fig.add_subplot(gs[i, 1])
        x = np.arange(1, 9)
        y1 = np.array([55, 20, 33, 15, 10, 15, 25, 5])
        y2 = np.array([7, 45, 20, 10, 55, 25, 15, 10])
        y3 = np.array([30, 50, 25, 15, 10, 20, 25, 20])
        y4 = np.array([40, 10, 15, 5, 10, 30, 20, 30])

        ax_line.plot(x, y1, "o-", color=scheme.hex_colors()[0], label="A")
        ax_line.plot(x, y2, "s-", color=scheme.hex_colors()[1], label="B")
        ax_line.plot(x, y3, "^-", color=scheme.hex_colors()[3], label="C")
        ax_line.plot(x, y4, "D-", color=scheme.hex_colors()[4], label="D")
        ax_line.set_title(f"{scheme.name} - 折线图", fontsize=14)
        ax_line.grid(True, linestyle="--", alpha=0.3)
        ax_line.legend()
        
        # 添加堆叠面积图
        ax_area = fig.add_subplot(gs[i, 2])
        x = np.arange(1, 11)
        data1 = np.array([1, 2, 4, 8, 12, 16, 14, 10, 7, 3])
        data2 = np.array([2, 5, 8, 12, 15, 18, 15, 14, 10, 5])
        data3 = np.array([1, 3, 6, 14, 17, 19, 16, 12, 8, 4])
        data4 = np.array([1, 4, 8, 15, 20, 22, 18, 15, 10, 6])

        ax_area.fill_between(
            x, 0, data1, alpha=0.8, color=scheme.hex_colors()[0], label="S1"
        )
        ax_area.fill_between(
            x, data1, data1 + data2, alpha=0.8, color=scheme.hex_colors()[1], label="S2"
        )
        ax_area.fill_between(
            x,
            data1 + data2,
            data1 + data2 + data3,
            alpha=0.8,
            color=scheme.hex_colors()[2],
            label="S3",
        )
        ax_area.fill_between(
            x,
            data1 + data2 + data3,
            data1 + data2 + data3 + data4,
            alpha=0.8,
            color=scheme.hex_colors()[3],
            label="S4",
        )
        ax_area.set_xlim(1, 10)
        ax_area.set_title(f"{scheme.name} - 面积图", fontsize=14)
        ax_area.legend()
        
    plt.tight_layout(rect=[0, 0, 1, 0.98])
    output_path = os.path.join(output_dir, "comparison_dashboard.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"保存图片: {output_path}")
    plt.close(fig)
    return fig


def auto_discover_color_schemes():
    """自动发现所有继承自BaseColorScheme的配色方案类"""
    color_schemes = []
    
    # 获取当前模块路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 获取所有.py文件
    py_files = [f[:-3] for f in os.listdir(current_dir) if f.endswith('_colors.py')]
    
    for module_name in py_files:
        if module_name == 'base_colors':
            continue
        
        try:
            # 动态导入模块
            module_path = f"mot_toolkit.vis.{module_name}"
            module = importlib.import_module(module_path)
            
            # 获取模块中的所有类
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 检查是否是ColorScheme的子类，但不是BaseColorScheme本身
                if (issubclass(obj, BaseColorScheme) and 
                    obj != BaseColorScheme and 
                    obj.__module__ == module.__name__):
                    color_schemes.append(obj())
                    print(f"发现配色方案: {obj().name}")
        except (ImportError, AttributeError) as e:
            print(f"导入模块 {module_name} 时出错: {e}")
    
    return color_schemes


def main():
    """主函数"""
    setup_figure_style()

    print("正在加载配色方案...")
    
    # 方法1：手动指定配色方案
    schemes = [
        SIGEWINNEColorScheme(),
        VARESAColorScheme()
    ]
    
    # 方法2：自动发现所有配色方案（你可以取消注释此行，替代方法1）
    # schemes = auto_discover_color_schemes()
    
    if not schemes:
        print("未找到配色方案，请检查导入路径")
        return
    
    print(f"找到 {len(schemes)} 个配色方案")
    for i, scheme in enumerate(schemes):
        print(f"{i+1}. {scheme.name}")
    
    # 为每个配色方案创建输出目录
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(output_dir, "demo")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"图片输出目录: {output_dir}")
    
    # 为每个配色方案生成演示图表
    for scheme in schemes:
        scheme_name = scheme.__class__.__name__
        scheme_dir = os.path.join(output_dir, scheme_name)
        if not os.path.exists(scheme_dir):
            os.makedirs(scheme_dir, exist_ok=True)
        
        print(f"\n生成 {scheme.name} 配色方案演示...")
        
        # 创建各种图表
        create_color_palette_demo(scheme, scheme_dir)
        create_ridge_plot(scheme, scheme_dir)
        create_bar_chart(scheme, scheme_dir)
        create_line_chart(scheme, scheme_dir)
        create_pie_chart(scheme, scheme_dir)
        create_stacked_area_chart(scheme, scheme_dir)
        create_heatmap(scheme, scheme_dir)
        create_dashboard(scheme, scheme_dir)
    
    # 创建配色方案对比图
    create_comparison_dashboard(schemes, output_dir)
    
    print("\n所有演示图表已创建完成!")
    print(f"图表已保存到目录: {output_dir}")


if __name__ == "__main__":
    main()
