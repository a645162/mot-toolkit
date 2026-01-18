import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from typing import Optional, Tuple
import warnings

# 新增导入
from matplotlib import font_manager
import matplotlib.patches as mpatches

warnings.filterwarnings("ignore")

# 导入配色方案
from mot_toolkit.vis.common.base_colors import BaseColorScheme

# 配色方案-希格雯
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme

# 配色方案-神里绫华
from mot_toolkit.vis.scheme.genshin.ayaka_colors import AyakaColorScheme

# 配色方案-枫原万叶
from mot_toolkit.vis.scheme.genshin.kazuha_colors import KazuhaColorScheme

# 配色方案-三月七
from mot_toolkit.vis.scheme.genshin.march_seventh_colors import (
    MarchSeventhColorScheme,
)


# =============================================================================
# 全局参数设置
# =============================================================================
EXPANSION_ITERATIONS = 2  # 设置扩大迭代次数，可调整此值来控制差异程度

# Current py directory
py_dir_path = os.path.dirname(os.path.abspath(__file__))

csv_path = "metrics.ocean.local.csv"
csv_path = os.path.join(py_dir_path, csv_path)


def recursive_expand_differences(
    normalized_values: np.ndarray, iterations: int = 1
) -> np.ndarray:
    """
    递归扩大数值差异的函数

    Args:
        normalized_values: 归一化的数值数组 (0-1范围)
        iterations: 扩大迭代次数

    Returns:
        扩大差异后的数值数组 (仍在0-1范围内)
    """
    if iterations <= 0:
        return normalized_values

    # 使用指数函数来扩大差异 (小值变更小，大值变得更大)
    # 使用 x^2 会让差异更明显，而不是 x^0.5
    expanded_values = normalized_values**2

    # 递归调用，继续扩大差异
    return recursive_expand_differences(expanded_values, iterations - 1)


def setup_plot_style():
    """设置绘图样式"""
    plt.style.use("default")
    custom_font_path = os.path.expanduser("./Resources/Fonts/Times New Roman.ttf")
    if os.path.exists(custom_font_path):
        font_manager.fontManager.addfont(custom_font_path)
        plt.rc("font", family="Times New Roman")
        print(f"✓ 已注册自定义字体: {custom_font_path}")
    else:
        plt.rc("font", family="Times New Roman")
        print(f"✗ 未找到自定义字体文件: {custom_font_path}，尝试系统字体")
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.figsize"] = (10, 8)
    plt.rcParams["figure.dpi"] = 100
    # ==== 放大字体 ====
    plt.rcParams["font.size"] = 16
    plt.rcParams["axes.labelsize"] = 18
    plt.rcParams["axes.titlesize"] = 20
    plt.rcParams["xtick.labelsize"] = 15
    plt.rcParams["ytick.labelsize"] = 15
    plt.rcParams["legend.fontsize"] = 15


def load_metrics_data(csv_file_path: str) -> Optional[pd.DataFrame]:
    """
    加载指标数据

    Args:
        csv_file_path: CSV文件路径

    Returns:
        pandas DataFrame包含指标数据，如果加载失败返回None
    """
    try:
        df = pd.read_csv(csv_file_path)
        print(f"✓ 成功加载数据: {df.shape[0]}行, {df.shape[1]}列")
        print(f"✓ 列名: {list(df.columns)}")

        # 检查必需的列是否存在
        required_columns = ["Method", "HOTA", "DetA", "AssA", "MOTA", "IDF1"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print(f"⚠ 警告: 缺少以下列 {missing_columns}")

        return df
    except FileNotFoundError:
        print(f"✗ 错误: 找不到文件 {csv_file_path}")
        return None
    except Exception as e:
        print(f"✗ 错误: 加载数据时出现问题 - {e}")
        return None


# 新增：根据可用列自动选择 x/y 列的辅助函数
def select_xy_columns(
    data: pd.DataFrame,
    preferred_pairs=None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    从 data 中选择合适的 x 和 y 列。
    优先使用 preferred_pairs 中的组合（按顺序），否则从数值列中选择前两列。
    返回实际选择的列名（或 (None, None) 如果无法选择）。
    """
    if preferred_pairs is None:
        preferred_pairs = [
            ("MOTA", "IDF1"),
            ("DetA", "AssA"),
            ("HOTA", "MOTA"),
            ("HOTA", "IDF1"),
            ("DetA", "MOTA"),
            ("AssA", "IDF1"),
        ]

    # 建立小写列名->实际列名映射，方便不区分大小写的匹配
    col_map = {c.lower(): c for c in data.columns}

    # 首先尝试首选组合（不区分大小写）
    for a, b in preferred_pairs:
        if a.lower() in col_map and b.lower() in col_map:
            return col_map[a.lower()], col_map[b.lower()]

    # 否则，找出数值列（int/float）
    numeric_cols = [
        c for c in data.columns if pd.api.types.is_numeric_dtype(data[c].dtype)
    ]
    if len(numeric_cols) >= 2:
        return numeric_cols[0], numeric_cols[1]

    # 如果只找到一列数值列或找不到可用列，返回None
    if len(numeric_cols) == 1:
        return numeric_cols[0], None

    return None, None


# 新增：列可选项展示函数，帮助用户明确可用列
def list_selectable_columns(data: pd.DataFrame):
    """
    返回可用列信息，便于用户手动指定 x/y/size 列。
    打印所有列及数值列（可用于 x/y/size 的候选）。
    """
    all_cols = list(data.columns)
    numeric_cols = [c for c in data.columns if pd.api.types.is_numeric_dtype(data[c].dtype)]
    print("可用列（全部）：", all_cols)
    print("可用数值列（适合用于 x/y/size）：", numeric_cols)
    return {"all": all_cols, "numeric": numeric_cols}


def create_bubble_chart(
    data: pd.DataFrame,
    x_column: Optional[str] = None,
    y_column: Optional[str] = None,
    size_column: str = "HOTA",
    method_column: str = "Method",
    highlight_method: Optional[str] = "P-MOTIP",  # 仅为此方法绘制指引线，None表示不高亮任何点
    title: Optional[str] = None,
    save_prefix: Optional[str] = None,
    output_dir: Optional[str] = None,
    figsize: Tuple[float, float] = (12, 8),
    size_scale: float = 2500.0,
    alpha: float = 0.7,
    show_labels: bool = True,
    grid: bool = True,
    prefer_dark_colors: Optional[bool] = True,
    bubble_radius_scale: float = 2.0,  # 新增：气泡半径缩放因子
) -> Optional[plt.Figure]:
    """
    创建气泡图

    Args:
        data: 包含指标数据的DataFrame
        x_column: x轴列名
        y_column: y轴列名
        size_column: 气泡大小列名（固定为HOTA）
        method_column: 方法名称列名
        highlight_method: 仅为此方法绘制指引线，None表示不高亮任何点
        title: 图表标题
        save_prefix: 保存文件名前缀
        output_dir: 输出目录
        figsize: 图片尺寸
        size_scale: 气泡大小缩放因子
        alpha: 透明度
        show_labels: 是否显示方法名标签
        grid: 是否显示网格
        prefer_dark_colors: 颜色偏好设置
            - True: 偏好深色
            - False: 偏好浅色
            - None: 无偏好（默认）
        bubble_radius_scale: 气泡半径缩放因子（等比例缩放所有气泡半径，默认1.0）

    Returns:
        matplotlib Figure对象"""
    if data is None or data.empty:
        print("✗ 错误: 数据为空")
        return None

    # 强制要求用户显式指定 x/y/size（size 默认 HOTA）。
    # 如果用户传入的列不存在，则直接提示可用列并返回 None（不做自动配对/回退）。
    def _validate_col(name: str) -> bool:
        return name in data.columns

    # 列存在性校验（大小写严格匹配）
    if x_column is None or y_column is None:
        print("✗ 错误: 必须明确指定 x_column 和 y_column（不能依赖自动配对）。")
        list_selectable_columns(data)
        return None

    missing = [c for c in (x_column, y_column, size_column, method_column) if c not in data.columns]
    if missing:
        print(f"✗ 错误: 下列列不存在: {missing}")
        list_selectable_columns(data)
        return None

    print(f"ℹ 使用列 -> x: {x_column}, y: {y_column}, size: {size_column}, method: {method_column}")

    # 检查必需的列是否存在
    # required_columns = [x_column, y_column, size_column, method_column]
    # missing_columns = [col for col in required_columns if col not in data.columns]
    # if missing_columns:
    #     print(f"✗ 错误: 缺少列 {missing_columns}")
    #     return None

    setup_plot_style()

    # 创建多个配色方案实例列表，方便扩展
    color_schemes = [
        SIGEWINNEColorScheme(),
        AyakaColorScheme(),
        KazuhaColorScheme(),
        MarchSeventhColorScheme(),
        # 您可以在这里添加更多配色方案
    ]

    # 获取唯一的方法
    methods = data[method_column].unique()
    n_methods = len(methods)  # 使用基类的智能取色函数
    colors = BaseColorScheme.get_smart_colors_from_schemes(
        count=n_methods,
        color_schemes=color_schemes,
        seed=42,  # 固定随机数种子确保可重现
        prefer_dark=prefer_dark_colors,  # 使用传入的颜色偏好参数
    )

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)

    # 为每个方法分配颜色
    color_map = {}
    for i, method in enumerate(methods):
        if method == "SA-MOTIP":
            color_map[method] = "#FF0000"  # 红色
        else:
            color_map[method] = colors[i % len(colors)]

    # 计算气泡大小的归一化参数
    size_values = data[size_column].dropna()
    min_size = size_values.min()
    max_size = size_values.max()
    size_range = max_size - min_size

    # 设置最小和最大气泡半径 - 总体放大
    min_bubble_size = 200 * bubble_radius_scale
    max_bubble_size = size_scale * bubble_radius_scale

    print(f"📏 HOTA Range: {min_size:.3f} - {max_size:.3f}")
    print(f"📏 Bubble Size Range: {min_bubble_size} - {max_bubble_size}")
    print(f"🔄 Expansion Iterations: {EXPANSION_ITERATIONS}")
    print(f"🔧 Bubble Radius Scale: {bubble_radius_scale}")

    # 创建scatter plot数据
    scatter_data = []

    # 绘制气泡
    for i, row in data.iterrows():
        x_val = row[x_column]
        y_val = row[y_column]
        size_val = row[size_column]  # HOTA值作为气泡大小
        method = row[method_column]

        # 确保数值有效
        if pd.isna(x_val) or pd.isna(y_val) or pd.isna(size_val):
            continue

        # 计算归一化的气泡大小 - 使用递归扩大函数
        if size_range > 0:
            normalized_size = (size_val - min_size) / size_range
            expanded_normalized_size = recursive_expand_differences(
                np.array([normalized_size]), iterations=EXPANSION_ITERATIONS
            )[0]
            bubble_size = min_bubble_size + expanded_normalized_size * (
                max_bubble_size - min_bubble_size
            )
        else:
            bubble_size = min_bubble_size  # 如果所有HOTA值相同，使用最小值

        # 绘制气泡
        # ==== Method为SA-MOTIP时红色边框，否则白色 ====
        if method == "SA-MOTIP":
            edge_color = "#FF0000"
        else:
            edge_color = "white"

        scatter = ax.scatter(
            x_val,
            y_val,
            s=bubble_size,
            c=color_map[method],
            alpha=alpha,
            edgecolors=edge_color,
            linewidth=2.5 if method == "SA-MOTIP" else 1.5,
            label=None,  # 不使用每点label，改用自定义图例以避免重复/重叠
        )

        scatter_data.append(
            {
                "method": method,
                "x": x_val,
                "y": y_val,
                "size": size_val,
                "bubble_size": bubble_size,
                "color": color_map[method],
            }
        )

        # ==== 只为 highlight_method 添加注释箭头，其他方法仅通过图例展示 ====
        if show_labels and highlight_method is not None and method == highlight_method:
            label_color = "#FF0000" if "MOTIP" in method or method == "SA-MOTIP" else "black"
            radius = np.sqrt(bubble_size / np.pi)
            # 简单左右偏移，避免复杂自动布局导致截断
            offset_y = int(radius * 0.8) + 24
            offset_x = 40 if i % 2 == 0 else -40
            ax.annotate(
                method,
                xy=(x_val, y_val),
                xytext=(offset_x, offset_y),
                textcoords="offset points",
                fontsize=20,
                ha="center",
                va="bottom",
                color=label_color,
                bbox=dict(
                    boxstyle="round,pad=0.35",
                    facecolor="white",
                    edgecolor=label_color,
                    linewidth=2,
                    alpha=0.95,
                ),
                arrowprops=dict(
                    arrowstyle="->",
                    color=label_color,
                    lw=2,
                    shrinkA=5,
                    shrinkB=6,
                    connectionstyle="arc3,rad=0.2" if i % 2 == 0 else "arc3,rad=-0.2",
                ),
            )

    # ==== 自动扩展坐标轴范围，保证大气泡不被裁切 ====
    if scatter_data:
        # 取所有气泡的圆心和半径
        xs = np.array([d["x"] for d in scatter_data])
        ys = np.array([d["y"] for d in scatter_data])
        radii = np.array([np.sqrt(d["bubble_size"] / np.pi) for d in scatter_data])

        # 计算坐标轴范围
        x_min, x_max = xs.min(), xs.max()
        y_min, y_max = ys.min(), ys.max()
        r_max = radii.max()

        # 扩展比例（由1.1调整为0.6倍最大半径，更紧凑）
        pad_x = r_max * 0.6 / fig.dpi * (fig.get_figwidth() / ax.get_position().width)
        pad_y = r_max * 0.6 / fig.dpi * (fig.get_figheight() / ax.get_position().height)

        ax.set_xlim(x_min - pad_x, x_max + pad_x)
        ax.set_ylim(y_min - pad_y, y_max + pad_y)

    # 设置轴标签 - 移除标题设置
    ax.set_xlabel(f"{x_column}", fontsize=18, fontweight="bold")
    ax.set_ylabel(f"{y_column}", fontsize=18, fontweight="bold")

    # 添加网格
    if grid:
        ax.grid(True, linestyle="--", alpha=0.3)

    # 移除所有图例
    # handles, labels = ax.get_legend_handles_labels()
    # unique_labels = []
    # unique_handles = []
    # seen_methods = set()

    # for handle, label in zip(handles, labels):
    #     if label not in seen_methods:
    #         unique_labels.append(label)
    #         unique_handles.append(handle)
    #         seen_methods.add(label)

    # if unique_handles:
    #     legend1 = ax.legend(
    #         unique_handles,
    #         unique_labels,
    #         loc="center left",
    #         bbox_to_anchor=(1.02, 0.7),
    #         title="Methods",
    #         title_fontsize=11,
    #         fontsize=10,
    #         frameon=True,
    #         fancybox=True,
    #         shadow=False,
    #         borderaxespad=0,  # 减少边框填充
    #         columnspacing=1.0,  # 列间距
    #         handletextpad=0.5,  # 图例标记和文本间距
    #         handlelength=1.5,  # 图例标记长度
    #     )

    # 构建方法颜色图例（所有方法），放在右侧
    method_handles = []
    for m in methods:
        method_handles.append(mpatches.Patch(facecolor=color_map[m], edgecolor="black", label=str(m)))
    if method_handles:
        legend1 = ax.legend(
            handles=method_handles,
            loc="center left",
            bbox_to_anchor=(1.02, 0.6),
            title="Methods",
            frameon=True,
            fancybox=True,
        )
        ax.add_artist(legend1)

    # 添加气泡大小说明 - 使用实际的HOTA值范围（右侧下方）
    if data[size_column].nunique() > 1:
        # 选择有代表性的HOTA值来展示大小
        legend_hota_values = [min_size, (min_size + max_size) / 2, max_size]
        size_legend_elements = []

        for hota_val in legend_hota_values:
            # 计算对应的气泡大小
            if size_range > 0:
                normalized_size = (hota_val - min_size) / size_range
                legend_bubble_size = min_bubble_size + normalized_size * (
                    max_bubble_size - min_bubble_size
                )
            else:
                legend_bubble_size = min_bubble_size

            size_legend_elements.append(
                plt.scatter(
                    [],
                    [],
                    s=legend_bubble_size,
                    c="gray",
                    alpha=0.6,
                    edgecolors="white",
                    label=f"HOTA = {hota_val:.3f}",
                )
            )

        # 直接创建图例，不将结果赋值给未使用变量，避免 Pylance 警告
        ax.legend(
            handles=size_legend_elements,
            loc="center left",
            bbox_to_anchor=(1.02, 0.25),
            title="Bubble Size (HOTA)",
            frameon=True,
            fancybox=True,
        )

    # 美化坐标轴
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)

    # 调整布局
    # plt.tight_layout()
    plt.tight_layout(rect=[0, 0, 1, 0.97])  # 留出标题空间

    # 移除数据统计信息
    # stats_text = (
    #     f"Data Points: {len(scatter_data)}\nHOTA Range: {min_size:.3f}-{max_size:.3f}"
    # )
    # ax.text(
    #     0.02,
    #     0.98,
    #     stats_text,
    #     transform=ax.transAxes,
    #     verticalalignment="top",
    #     fontsize=9,
    #     bbox=dict(boxstyle="round,pad=0.3", facecolor="lightgray", alpha=0.7),
    # )

    # 保存图片
    if save_prefix and output_dir:
        save_bubble_chart(fig, save_prefix, output_dir, x_column, y_column)

    return fig


def save_bubble_chart(
    fig: plt.Figure, prefix: str, output_dir: str, x_col: str, y_col: str
):
    """
    保存气泡图为多种格式

    Args:
        fig: matplotlib图形对象
        prefix: 文件名前缀
        output_dir: 输出目录
        x_col: x轴列名
        y_col: y轴列名
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # 生成文件名
    filename_base = f"{prefix}_{x_col}_vs_{y_col}"

    # 保存多种格式
    formats = ["png", "eps", "svg"]
    saved_files = []

    for fmt in formats:
        filepath = os.path.join(output_dir, f"{filename_base}.{fmt}")
        try:
            if fmt == "eps":
                fig.savefig(filepath, format="eps", dpi=300, bbox_inches="tight")
            elif fmt == "svg":
                fig.savefig(filepath, format="svg", bbox_inches="tight")
            else:  # png
                fig.savefig(filepath, format="png", dpi=300, bbox_inches="tight")

            saved_files.append(filepath)
            print(f"✓ 已保存: {filepath}")
        except Exception as e:
            print(f"✗ 保存 {fmt} 格式失败: {e}")

    return saved_files


def create_multiple_bubble_charts(data: pd.DataFrame, output_dir: Optional[str] = None):
    """
    创建多个不同轴组合的气泡图

    Args:
        data: 数据DataFrame
        output_dir: 输出目录
    """
    if output_dir is None:
        output_dir = os.path.join(py_dir_path, "output", "bubble")

    # 数值列（排除Method列）
    numeric_columns = [
        col
        for col in data.columns
        if col != "Method" and data[col].dtype in ["float64", "int64"]
    ]

    # 预定义的轴组合
    axis_combinations = [
        ("DetA", "AssA", "Detection vs Association Performance"),
        ("MOTA", "IDF1", "MOTA vs IDF1 Performance"),
        ("DetA", "MOTA", "Detection Accuracy vs MOTA"),
        ("AssA", "IDF1", "Association vs Identity Performance"),
        ("HOTA", "MOTA", "HOTA vs MOTA Comparison"),
        ("HOTA", "IDF1", "HOTA vs IDF1 Comparison"),
        ("DetA", "IDF1", "Detection vs Identity Performance"),
        ("AssA", "MOTA", "Association vs MOTA Performance"),
    ]

    created_charts = []

    for x_col, y_col, chart_title in axis_combinations:
        if x_col in numeric_columns and y_col in numeric_columns and x_col != y_col:
            print(f"\n📊 创建气泡图: {x_col} vs {y_col}")

            fig = create_bubble_chart(
                data=data,
                x_column=x_col,
                y_column=y_col,
                title=chart_title,
                save_prefix="bubble_chart",
                output_dir=output_dir,
            )

            if fig:
                created_charts.append((x_col, y_col, fig))
                plt.close(fig)  # 关闭图形以节省内存

    return created_charts


def create_custom_bubble_chart(
    data: pd.DataFrame,
    x_column: str,
    y_column: str,
    output_dir: Optional[str] = None,
    show_plot: bool = True,
) -> Optional[plt.Figure]:
    """
    创建自定义的气泡图（方便用户指定x和y轴）

    Args:
        data: 数据DataFrame
        x_column: x轴指标名
        y_column: y轴指标名
        output_dir: 输出目录
        show_plot: 是否显示图表

    Returns:
        matplotlib Figure对象
    """
    if output_dir is None:
        output_dir = os.path.join(py_dir_path, "output", "bubble")

    print(f"\n🎨 创建自定义气泡图: {x_column} vs {y_column}")

    title = f"MOT方法性能对比: {x_column} vs {y_column}"

    fig = create_bubble_chart(
        data=data,
        x_column=x_column,
        y_column=y_column,
        title=title,
        save_prefix="custom_bubble",
        output_dir=output_dir,
    )

    if fig and show_plot:
        plt.show()

    return fig


def main():
    """主函数 - 演示气泡图功能"""
    print("=" * 60)
    print("🎯 MOT Metrics Bubble Chart Tool (Sigewinne Color Scheme)")
    print("=" * 60)

    # 加载数据
    print(f"\n📁 Loading data: {csv_path}")
    data = load_metrics_data(csv_path)
    if data is None:
        print("❌ Data loading failed, program exits")
        return

    # 显示数据概览
    print(f"\n📊 Data Overview:")
    print(f"   - Data shape: {data.shape}")
    print(f"   - Columns: {list(data.columns)}")
    print(
        f"   - Number of methods: {data['Method'].nunique() if 'Method' in data.columns else 'N/A'}"
    )

    if "Method" in data.columns:
        print(f"   - Method list: {list(data['Method'].unique())}")

    # 创建输出目录
    output_dir = os.path.join(py_dir_path, "output", "bubble")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    print(f"\n📂 Output directory: {output_dir}")

    # 创建默认气泡图 (DetA vs AssA)
    print(f"\n🎨 Creating default bubble chart (DetA vs AssA)...")
    fig_default = create_bubble_chart(
        data=data,
        x_column="MOTA",
        y_column="IDF1",
        title="MOT Method Performance Comparison: Detection vs Association",
        save_prefix="default_bubble",
        output_dir=output_dir,
    )

    # # 创建多种组合的气泡图
    # print(f"\n🎨 Creating bubble charts with multiple axis combinations...")
    # created_charts = create_multiple_bubble_charts(data, output_dir)

    # print(f"\n✅ Bubble chart generation completed!")
    # print(
    #     f"   - Number of charts generated: {len(created_charts) + (1 if fig_default else 0)}"
    # )
    # print(f"   - Output directory: {output_dir}")
    # print(f"   - Supported formats: PNG, EPS, SVG")

    # 显示第一个图（如果存在）
    if fig_default:
        print(f"\n👀 显示默认气泡图...")
        plt.show()


def demo_custom_chart():
    """演示如何创建自定义气泡图"""
    print("\n" + "=" * 50)
    print("🎨 Custom Bubble Chart Demo")
    print("=" * 50)

    # 加载数据
    data = load_metrics_data(csv_path)
    if data is None:
        return

    # 示例：创建HOTA vs MOTA的气泡图
    fig = create_custom_bubble_chart(
        data=data, x_column="HOTA", y_column="MOTA", show_plot=True
    )

    print("✅ Custom bubble chart creation completed!")


if __name__ == "__main__":
    main()

    # 取消注释下面这行来运行自定义图表演示
    # demo_custom_chart()
    # demo_custom_chart()
