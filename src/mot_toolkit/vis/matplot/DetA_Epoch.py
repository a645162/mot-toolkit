import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Import Sigewinne color scheme
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme


def setup_figure_style():
    """Setup figure style with Times New Roman font"""
    plt.style.use("default")
    # Set Times New Roman font
    plt.rcParams["font.family"] = "serif"
    plt.rcParams["font.serif"] = ["Times New Roman", "Times", "serif"]
    plt.rcParams["mathtext.fontset"] = "stix"  # For math text
    plt.rcParams["axes.unicode_minus"] = False
    plt.rcParams["figure.figsize"] = (8, 6)
    plt.rcParams["figure.dpi"] = 100


def create_deta_epoch_plot():
    """Create DetA vs Epoch line plot with markers"""
    # Setup style
    setup_figure_style()

    # Initialize color scheme
    color_scheme = SIGEWINNEColorScheme()

    # Get the directory of current script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(current_dir, "DetA.csv")

    # Create output directory
    output_dir = os.path.join(current_dir, "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Read data from CSV
    df = pd.read_csv(csv_path)

    # Print dataframe info for debugging
    print("DataFrame shape:", df.shape)
    print("DataFrame columns:", df.columns.tolist())
    print("DataFrame head:")
    print(df.head())

    # Extract epoch data from column headers (skip first column which contains line names)
    epochs = df.columns[1:].astype(int)  # Skip first column

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(10, 6))

    # Get colors for the two lines
    line_colors = [color_scheme.hex_colors()[0], color_scheme.hex_colors()[-1]]

    # Plot each line (row) from the dataframe
    for i, (index, row) in enumerate(df.iterrows()):
        line_name = row.iloc[0]  # First column contains line name
        values = row.iloc[1:].values  # Get values from second column onwards

        # Clean and convert data - remove spaces and convert to float
        values = np.array([float(str(val).strip()) for val in values])

        # Plot line
        ax.plot(
            epochs,
            values,
            "-",
            color=line_colors[i],
            linewidth=2.5,
            label=line_name,
        )

        # Plot individual points with same color as line
        for j, (epoch, value) in enumerate(zip(epochs, values)):
            ax.plot(
                epoch,
                value,
                "o",
                color=line_colors[i],
                markersize=8,
                markerfacecolor=line_colors[i],
                markeredgecolor="white",
                markeredgewidth=1.5,
            )

    # Customize the plot
    ax.set_xlabel("Epoch", fontsize=14, fontweight="bold")
    ax.set_ylabel("DetA", fontsize=14, fontweight="bold")

    # Set axis limits with some padding
    ax.set_xlim(-0.5, 10.5)
    ax.set_ylim(37, 47)

    # Add grid
    ax.grid(True, linestyle="--", alpha=0.3, color="gray")

    # Customize ticks
    ax.set_xticks(epochs)
    ax.tick_params(axis="both", which="major", labelsize=12)

    # Add legend
    ax.legend(fontsize=12, loc="lower right")

    # Add value annotations on data points for both lines
    for i, (index, row) in enumerate(df.iterrows()):
        values = np.array([float(str(val).strip()) for val in row.iloc[1:].values])

        for j, (epoch, value) in enumerate(zip(epochs, values)):
            # Determine annotation position to avoid overlapping
            if j == 0:
                xytext = (0, 15) if i == 0 else (0, -20)
            elif j == len(epochs) - 1:
                xytext = (0, 15) if i == 0 else (0, -20)
            else:
                # For middle points, alternate positions for different lines
                if i == 0:  # First line (Baseline)
                    xytext = (0, 15) if j % 2 == 0 else (15, 5)
                else:  # Second line (Ours)
                    xytext = (0, -20) if j % 2 == 0 else (-15, -5)

            ax.annotate(
                f"{value:.3f}",
                (epoch, value),
                textcoords="offset points",
                xytext=xytext,
                ha="center",
                fontsize=8,
                color="black",
            )

    # Remove top and right spines for cleaner look
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Make left and bottom spines more prominent
    ax.spines["left"].set_linewidth(1.2)
    ax.spines["bottom"].set_linewidth(1.2)

    # Tight layout
    plt.tight_layout()

    # Save the figure in multiple formats
    base_filename = "DetA_Epoch_comparison"
    formats = ["png", "svg", "eps"]

    for fmt in formats:
        output_path = os.path.join(output_dir, f"{base_filename}.{fmt}")
        plt.savefig(
            output_path, dpi=300, bbox_inches="tight", facecolor="white", format=fmt
        )
        print(f"Plot saved to: {output_path}")

    # Show the plot
    plt.show()

    return fig, ax


def main():
    """Main function"""
    print("Creating DetA vs Epoch plot with Sigewinne color scheme...")
    create_deta_epoch_plot()
    print("Plot creation completed!")


if __name__ == "__main__":
    main()
