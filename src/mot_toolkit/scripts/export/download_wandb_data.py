import argparse
import json
import os
import wandb
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager

from mot_toolkit.vis.scheme.genshin.sigewinne_colors import SIGEWINNEColorScheme

def setup_plot_style():
	"""设置绘图样式 - 使用Times字体"""
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
	plt.rcParams["figure.figsize"] = (12, 8)
	plt.rcParams["figure.dpi"] = 100
	# 字体大小设置
	plt.rcParams["font.size"] = 16
	plt.rcParams["axes.labelsize"] = 18
	plt.rcParams["axes.titlesize"] = 20
	plt.rcParams["xtick.labelsize"] = 15
	plt.rcParams["ytick.labelsize"] = 15
	plt.rcParams["legend.fontsize"] = 15

def diagnose_and_load(run):
	# 1) 尝试流式读取所有 history 点（避免采样限制）
	records = list(run.scan_history())
	if records:
		df = pd.DataFrame(records)
		source = "scan_history"
	else:
		# 2) 回退到 run.history()（可能受默认采样）
		df = run.history()
		source = "run.history()"
	# 3) 若仍为空，尝试从 run.files() 下载 jsonl / wandb-summary 并解析
	if df is None or df.empty:
		collected = []
		for f in run.files():
			name = f.name.lower()
			if name.endswith(".jsonl") or "history" in name:
				local = f.download(replace=True)
				try:
					with open(local, "r", encoding="utf-8") as fh:
						for line in fh:
							line = line.strip()
							if not line: continue
							try:
								collected.append(json.loads(line))
							except Exception:
								continue
				except Exception:
					continue
			# 解析 wandb-summary.json（聚合值）
			if name == "wandb-summary.json":
				local = f.download(replace=True)
				try:
					with open(local, "r", encoding="utf-8") as fh:
						summary = json.load(fh)
						collected.append(summary)
				except Exception:
					continue
		if collected:
			df = pd.DataFrame(collected)
			source = "files(jsonl/summary)"
	# 4) 最后确保 df 不为 None
	if df is None:
		df = pd.DataFrame()
	return df, source

def find_best_keys(df):
	# 自动识别 epoch/step 与 loss 列
	cols = [c.lower() for c in df.columns]
	# epoch/step 候选
	x_candidates = ['epoch','step','global_step','_step','iter','iteration']
	x_key = None
	for k in x_candidates:
		for c in df.columns:
			if k in c.lower():
				x_key = c
				break
		if x_key: break
	# loss 候选
	l_candidates = ['epoch_loss','train/loss','training_loss','loss','val_loss','validation_loss']
	l_key = None
	for k in l_candidates:
		for c in df.columns:
			if k in c.lower():
				l_key = c
				break
		if l_key: break
	return x_key, l_key

def main():
	parser = argparse.ArgumentParser(description="Download and inspect wandb run history")
	parser.add_argument("--run", type=str, default="/a645162/MOTIP/runs/q0jlpxej", help="wandb run path (entity/project/runs/id)")
	args = parser.parse_args()

	api = wandb.Api()
	try:
		run = api.run(args.run)
	except Exception as e:
		print(f"无法获取 run: {e}")
		return

	df, source = diagnose_and_load(run)
	print(f"数据来源: {source}")
	print(f"Run 状态: {getattr(run, 'state', 'unknown')}")
	print(f"创建时间: {getattr(run, 'created_at', 'unknown')}, 更新时间: {getattr(run, 'updated_at', 'unknown')}")
	print(f"历史数据点数量: {len(df)}")
	print(f"列名: {df.columns.tolist()}")

	# 保存 CSV（如果有数据）
	if not df.empty:
		out_csv = "run_history.csv"
		df.to_csv(out_csv, index=False)
		print(f"已保存: {out_csv}")
	else:
		print("未找到历史数据（可能未同步或使用了不同的 metric 名称）。尝试检查 web UI 的 metric 名称或等待 run 同步完成。")

	# 可视化
	if not df.empty:
		x_key, l_key = find_best_keys(df)

		# 强制优先使用 epoch 和 epoch_loss（如果存在）
		if 'epoch' in df.columns:
			x_key = 'epoch'
		if 'epoch_loss' in df.columns:
			l_key = 'epoch_loss'

		if l_key is None:
			print("未能自动识别 loss 列，尝试查找包含 'loss' 的任意列。")
			loss_cols = [c for c in df.columns if 'loss' in c.lower()]
			if loss_cols:
				l_key = loss_cols[0]
		if x_key is None:
			print("未能自动识别 epoch/step 列，使用索引作为横轴。")

		if l_key is not None:
			# 准备 x 与 y：将 x 转为数值（如可能），并按 x 排序
			if x_key in df.columns:
				x_vals = pd.to_numeric(df[x_key], errors='coerce')
			else:
				x_vals = pd.to_numeric(df.index, errors='coerce')
			y_vals = pd.to_numeric(df[l_key], errors='coerce')

			# 清理 NaN 并按 x 排序
			mask = pd.notna(x_vals) & pd.notna(y_vals)
			df_plot = pd.DataFrame({ 'x': x_vals[mask], 'y': y_vals[mask] })
			if not df_plot.empty:
				df_plot = df_plot.sort_values(by='x')
			x_clean = df_plot['x']
			y_clean = df_plot['y']

			print(f"用于绘图的点数量: {len(y_clean)}，列: x={x_key}, y={l_key}")
			if len(y_clean) > 0:
				# 设置绘图样式
				setup_plot_style()
				
				# 获取希格雯配色方案
				color_scheme = SIGEWINNEColorScheme()
				colors = color_scheme.hex_colors()
				
				plt.figure(figsize=(12, 8))
				
				# 使用希格雯配色的第一个颜色，增加线宽和标记大小
				plt.plot(x_clean, y_clean, 
						marker='o', markersize=6, linewidth=2.5, 
						color=colors[0], alpha=0.8)
				
				# 横轴标签首字母大写
				xlabel = x_key if x_key in df.columns else "Index"
				if xlabel.lower() == "epoch":
					xlabel = "Epoch"
				plt.xlabel(xlabel, fontsize=18)
				plt.ylabel("Loss", fontsize=18)
				# plt.title("Loss", fontsize=20)
				# 不显示图例
				# plt.legend(handlelength=2.0, handletextpad=0.8)
				plt.grid(True, linestyle='--', alpha=0.7)
				plt.tight_layout()
				
				# 保存PNG
				plt.savefig("run_visualization.png", dpi=300, bbox_inches='tight')
				print("可视化已保存: run_visualization.png")
				
				# 保存SVG
				plt.savefig("run_visualization.svg", format='svg', bbox_inches='tight')
				print("SVG格式已保存: run_visualization.svg")
				
				# 保存EPS
				plt.savefig("run_visualization.eps", format='eps', bbox_inches='tight')
				print("EPS格式已保存: run_visualization.eps")
				
				plt.show()
			else:
				print("没有可用于绘图的有效 loss 数据点。")
		else:
			print("找不到 loss 列，跳过可视化。")

if __name__ == "__main__":
	main()
