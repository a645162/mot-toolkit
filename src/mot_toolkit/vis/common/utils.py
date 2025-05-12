"""颜色方案工具函数
提供实用工具和示例代码
"""

from .sigewinne_colors import SIGEWINNEColorScheme


def apply_to_matplotlib():
    """将希格雯配色应用到matplotlib的默认设置"""
    try:
        import matplotlib.pyplot as plt

        scheme = SIGEWINNEColorScheme()
        plt.rcParams["axes.prop_cycle"] = plt.cycler(color=scheme.hex_colors())
        plt.rcParams["axes.facecolor"] = "white"
        plt.rcParams["figure.facecolor"] = "white"
        return True
    except ImportError:
        print("matplotlib 未安装，无法应用配色方案")
        return False


def example_usage():
    """示例：如何使用希格雯配色方案"""
    try:
        import matplotlib.pyplot as plt
        import numpy as np

        scheme = SIGEWINNEColorScheme()

        # 柱状图示例
        fig, ax = plt.subplots(figsize=(8, 5))
        categories = ["类别A", "类别B", "类别C", "类别D"]
        values = [23, 45, 56, 78]

        bars = ax.bar(categories, values, color=scheme.hex_colors()[:4])
        ax.set_title("希格雯配色示例 - 柱状图", fontsize=14)
        ax.set_ylabel("数值")
        ax.grid(True, linestyle="--", alpha=0.7, color=scheme.hex_colors()[2])

        # 添加数据标签
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height}",
                ha="center",
                va="bottom",
            )

        plt.show()

        # 折线图示例
        fig, ax = plt.subplots(figsize=(10, 6))
        x = np.arange(10)
        ax.plot(
            x,
            [i**1.5 for i in x],
            color=scheme.hex_colors()[0],
            linewidth=2,
            label="主要趋势",
        )
        ax.plot(
            x,
            [i**0.5 * 10 for i in x],
            color=scheme.hex_colors()[4],
            linestyle="--",
            linewidth=2,
            label="次要趋势",
        )
        ax.legend()
        ax.set_title("希格雯配色示例 - 折线图", fontsize=14)
        ax.grid(True, linestyle="--", alpha=0.7, color=scheme.hex_colors()[2])

        plt.show()

        return True
    except ImportError:
        print("matplotlib 未安装，无法运行示例")
        return False
