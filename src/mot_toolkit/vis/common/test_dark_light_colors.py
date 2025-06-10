"""
测试深色和浅色颜色选择功能
演示如何使用基类中的深色和浅色颜色选择方法
"""

import sys
import os

# 添加项目根目录到路径
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
)

from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def test_dark_light_colors():
    """测试深色和浅色颜色选择功能"""
    print("=" * 60)
    print("🎨 测试希格雯配色方案的深色和浅色颜色选择功能")
    print("=" * 60)

    # 创建配色方案实例
    color_scheme = SIGEWINNEColorScheme()

    print(f"\n🎯 原始配色方案:")
    print(f"   - 配色方案名称: {color_scheme.name}")
    print(f"   - 原始颜色数量: {len(color_scheme.colors)}")
    print(f"   - 原始颜色 (HEX): {color_scheme.hex_colors()}")

    # 测试深色颜色选择
    print(f"\n🌑 测试深色颜色选择:")

    # 使用不同的阈值测试深色
    thresholds = [0.3, 0.5, 0.7]
    for threshold in thresholds:
        dark_colors = color_scheme.get_dark_hex_colors(
            threshold=threshold, expand_if_needed=True
        )
        print(f"   - 亮度阈值 {threshold}: 找到 {len(dark_colors)} 种深色")
        print(f"     颜色: {dark_colors[:8]}")  # 只显示前8种

    # 测试浅色颜色选择
    print(f"\n🌕 测试浅色颜色选择:")

    # 使用不同的阈值测试浅色
    for threshold in thresholds:
        light_colors = color_scheme.get_light_hex_colors(
            threshold=threshold, expand_if_needed=True
        )
        print(f"   - 亮度阈值 {threshold}: 找到 {len(light_colors)} 种浅色")
        print(f"     颜色: {light_colors[:8]}")  # 只显示前8种

    # 测试亮度范围选择
    print(f"\n🎛️ 测试亮度范围选择:")
    brightness_ranges = [(0.2, 0.4), (0.4, 0.6), (0.6, 0.8)]
    for min_b, max_b in brightness_ranges:
        range_colors = color_scheme.get_colors_by_brightness((min_b, max_b))
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in range_colors]
        print(f"   - 亮度范围 {min_b}-{max_b}: 找到 {len(range_colors)} 种颜色")
        print(f"     颜色: {hex_colors[:6]}")

    # 测试饱和度范围选择
    print(f"\n🎨 测试饱和度范围选择:")
    saturation_ranges = [(0.2, 0.5), (0.5, 0.8), (0.8, 1.0)]
    for min_s, max_s in saturation_ranges:
        range_colors = color_scheme.get_colors_by_saturation((min_s, max_s))
        hex_colors = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in range_colors]
        print(f"   - 饱和度范围 {min_s}-{max_s}: 找到 {len(range_colors)} 种颜色")
        print(f"     颜色: {hex_colors[:6]}")

    # 可视化颜色
    visualize_dark_light_colors(color_scheme)


def visualize_dark_light_colors(color_scheme):
    """可视化深色和浅色颜色对比"""
    print(f"\n📊 生成深色/浅色颜色可视化图...")

    # 设置中文字体
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial"]
    plt.rcParams["axes.unicode_minus"] = False

    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle(
        "希格雯配色方案 - 深色/浅色颜色选择测试", fontsize=16, fontweight="bold"
    )

    # 1. 原始颜色
    ax1 = axes[0, 0]
    original_colors = color_scheme.hex_colors()
    show_color_palette(ax1, original_colors, f"原始颜色 ({len(original_colors)} 种)")

    # 2. 扩展后的所有颜色
    ax2 = axes[0, 1]
    expanded_colors = color_scheme.expand_hex_colors(multiplier=3)
    show_color_palette(
        ax2, expanded_colors[:16], f"扩展颜色 (显示前16种，共{len(expanded_colors)}种)"
    )

    # 3. 深色颜色 (阈值0.5)
    ax3 = axes[1, 0]
    dark_colors = color_scheme.get_dark_hex_colors(threshold=0.5, expand_if_needed=True)
    show_color_palette(
        ax3, dark_colors[:12], f"深色颜色 (亮度≤0.5, 共{len(dark_colors)}种)"
    )

    # 4. 浅色颜色 (阈值0.5)
    ax4 = axes[1, 1]
    light_colors = color_scheme.get_light_hex_colors(
        threshold=0.5, expand_if_needed=True
    )
    show_color_palette(
        ax4, light_colors[:12], f"浅色颜色 (亮度≥0.5, 共{len(light_colors)}种)"
    )

    # 5. 中等亮度颜色
    ax5 = axes[2, 0]
    medium_colors = color_scheme.get_colors_by_brightness((0.4, 0.7))
    medium_hex = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in medium_colors]
    show_color_palette(
        ax5, medium_hex[:12], f"中等亮度颜色 (0.4-0.7, 共{len(medium_colors)}种)"
    )

    # 6. 高饱和度颜色
    ax6 = axes[2, 1]
    saturated_colors = color_scheme.get_colors_by_saturation((0.7, 1.0))
    saturated_hex = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in saturated_colors]
    show_color_palette(
        ax6, saturated_hex[:12], f"高饱和度颜色 (0.7-1.0, 共{len(saturated_colors)}种)"
    )

    plt.tight_layout()

    # 保存图片
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_path = os.path.join(output_dir, "sigewinne_dark_light_colors_test.png")
    plt.savefig(save_path, dpi=300, bbox_inches="tight")
    print(f"✓ 深色/浅色颜色可视化图已保存: {save_path}")

    plt.show()


def show_color_palette(ax, colors, title):
    """在指定的轴上显示颜色调色板"""
    ax.set_title(title, fontsize=11, fontweight="bold")
    if not colors:
        ax.text(0.5, 0.5, "无颜色", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        return

    ax.set_xlim(0, len(colors))
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")

    # 绘制颜色块
    for i, color in enumerate(colors):
        rect = patches.Rectangle(
            (i, 0), 1, 1, facecolor=color, edgecolor="white", linewidth=1
        )
        ax.add_patch(rect)

        # 添加颜色代码标签（对于少量颜色）
        if len(colors) <= 8:
            ax.text(
                i + 0.5,
                0.5,
                color,
                ha="center",
                va="center",
                fontsize=7,
                rotation=90,
                color="white",
                fontweight="bold",
            )

    ax.set_xticks(range(len(colors)))
    ax.set_xticklabels([f"{i+1}" for i in range(len(colors))], fontsize=8)
    ax.set_yticks([])
    ax.grid(True, alpha=0.3)


def demo_practical_usage():
    """演示实际使用场景"""
    print(f"\n🚀 实际使用场景演示:")

    color_scheme = SIGEWINNEColorScheme()

    # 场景1: 为夜间模式选择深色
    print(f"\n💡 场景1: 夜间模式图表")
    dark_colors = color_scheme.get_dark_hex_colors(threshold=0.4, expand_if_needed=True)
    print(f"   - 适合夜间模式的深色: {dark_colors[:5]}")

    # 场景2: 为打印材料选择浅色
    print(f"\n💡 场景2: 打印友好的浅色")
    light_colors = color_scheme.get_light_hex_colors(
        threshold=0.6, expand_if_needed=True
    )
    print(f"   - 适合打印的浅色: {light_colors[:5]}")

    # 场景3: 为数据可视化选择中等亮度颜色
    print(f"\n💡 场景3: 数据可视化中等亮度颜色")
    medium_colors = color_scheme.get_colors_by_brightness((0.4, 0.7))
    medium_hex = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in medium_colors]
    print(f"   - 适合数据可视化的中等亮度: {medium_hex[:5]}")

    # 场景4: 为醒目标记选择高饱和度颜色
    print(f"\n💡 场景4: 醒目标记高饱和度颜色")
    vibrant_colors = color_scheme.get_colors_by_saturation((0.8, 1.0))
    vibrant_hex = [f"#{r:02x}{g:02x}{b:02x}".upper() for r, g, b in vibrant_colors]
    print(f"   - 适合醒目标记的高饱和度: {vibrant_hex[:5]}")


if __name__ == "__main__":
    test_dark_light_colors()
    demo_practical_usage()

    print(f"\n✅ 深色/浅色颜色选择测试完成!")
    print(f"现在你可以在任何继承自BaseColorScheme的配色方案中使用以下方法:")
    print(f"   - get_dark_colors(threshold=0.5, expand_if_needed=True)")
    print(f"   - get_light_colors(threshold=0.5, expand_if_needed=True)")
    print(f"   - get_dark_hex_colors(threshold=0.5, expand_if_needed=True)")
    print(f"   - get_light_hex_colors(threshold=0.5, expand_if_needed=True)")
    print(f"   - get_colors_by_brightness(brightness_range=(0.3, 0.7))")
    print(f"   - get_colors_by_saturation(saturation_range=(0.4, 0.8))")
