import numpy as np
import pandas as pd
from typing import List, Tuple, Dict
import os

gt_txt_path="~/gt.txt"

other_result_txt_list=[
	""
]

my_model_result_txt=""

def parse_mot_file(filepath: str) -> pd.DataFrame:
    """解析MOT格式文件"""
    if not os.path.exists(os.path.expanduser(filepath)):
        return pd.DataFrame()
    
    columns = ['frame', 'id', 'bb_left', 'bb_top', 'bb_width', 'bb_height', 'conf', 'x', 'y', 'z']
    df = pd.read_csv(os.path.expanduser(filepath), header=None, names=columns)
    return df

def calculate_segment_metrics(gt_df: pd.DataFrame, pred_df: pd.DataFrame, 
                            start_frame: int, end_frame: int) -> Dict[str, float]:
    """计算指定帧段的跟踪指标"""
    gt_segment = gt_df[(gt_df['frame'] >= start_frame) & (gt_df['frame'] <= end_frame)]
    pred_segment = pred_df[(pred_df['frame'] >= start_frame) & (pred_df['frame'] <= end_frame)]
    
    if len(gt_segment) == 0 or len(pred_segment) == 0:
        return {'mota': 0.0, 'idf1': 0.0, 'precision': 0.0, 'recall': 0.0}
    
    # 简化指标计算 - 基于ID匹配
    gt_ids = set(gt_segment['id'].unique())
    pred_ids = set(pred_segment['id'].unique())
    
    matched_ids = len(gt_ids.intersection(pred_ids))
    precision = matched_ids / len(pred_ids) if len(pred_ids) > 0 else 0
    recall = matched_ids / len(gt_ids) if len(gt_ids) > 0 else 0
    
    mota = max(0, 1 - (len(gt_ids) + len(pred_ids) - 2 * matched_ids) / len(gt_ids))
    idf1 = 2 * matched_ids / (len(gt_ids) + len(pred_ids)) if (len(gt_ids) + len(pred_ids)) > 0 else 0
    
    return {
        'mota': mota,
        'idf1': idf1, 
        'precision': precision,
        'recall': recall
    }

def find_best_segments(gt_path: str, my_result_path: str, other_results: List[str], 
                      segment_length: int = 100) -> List[Tuple[int, int, Dict[str, float]]]:
    """找出我的模型表现最好的片段"""
    
    # 解析文件
    gt_df = parse_mot_file(gt_path)
    my_df = parse_mot_file(my_result_path)
    other_dfs = [parse_mot_file(path) for path in other_results if path.strip()]
    
    if gt_df.empty or my_df.empty:
        print("警告: GT文件或我的模型结果文件为空")
        return []
    
    # 获取帧范围
    max_frame = min(gt_df['frame'].max(), my_df['frame'].max())
    min_frame = max(gt_df['frame'].min(), my_df['frame'].min())
    
    best_segments = []
    
    # 滑动窗口分析
    for start_frame in range(min_frame, max_frame - segment_length + 1, segment_length // 2):
        end_frame = start_frame + segment_length
        
        # 计算我的模型在此片段的指标
        my_metrics = calculate_segment_metrics(gt_df, my_df, start_frame, end_frame)
        
        # 计算其他模型的平均指标
        other_metrics_list = []
        for other_df in other_dfs:
            if not other_df.empty:
                other_metrics = calculate_segment_metrics(gt_df, other_df, start_frame, end_frame)
                other_metrics_list.append(other_metrics)
        
        if not other_metrics_list:
            continue
            
        # 计算平均指标
        avg_other_metrics = {
            metric: np.mean([m[metric] for m in other_metrics_list])
            for metric in ['mota', 'idf1', 'precision', 'recall']
        }
        
        # 判断是否我的模型更优
        my_score = my_metrics['mota'] * 0.4 + my_metrics['idf1'] * 0.4 + my_metrics['precision'] * 0.2
        other_score = avg_other_metrics['mota'] * 0.4 + avg_other_metrics['idf1'] * 0.4 + avg_other_metrics['precision'] * 0.2
        
        if my_score > other_score:
            advantage = {
                'my_score': my_score,
                'other_score': other_score,
                'advantage': my_score - other_score,
                'my_metrics': my_metrics,
                'other_metrics': avg_other_metrics
            }
            best_segments.append((start_frame, end_frame, advantage))
    
    # 按优势排序
    best_segments.sort(key=lambda x: x[2]['advantage'], reverse=True)
    return best_segments

def analyze_and_report():
    """分析并报告最有利片段"""
    if not my_model_result_txt.strip():
        print("请先设置my_model_result_txt路径")
        return
    
    best_segments = find_best_segments(
        gt_txt_path, 
        my_model_result_txt, 
        [path for path in other_result_txt_list if path.strip()]
    )
    
    print(f"找到 {len(best_segments)} 个有利片段:")
    print("=" * 80)
    
    for i, (start, end, advantage) in enumerate(best_segments[:10]):  # 显示前10个
        print(f"\n片段 {i+1}: 帧 {start}-{end}")
        print(f"优势得分: {advantage['advantage']:.4f}")
        print(f"我的模型 - MOTA: {advantage['my_metrics']['mota']:.3f}, "
              f"IDF1: {advantage['my_metrics']['idf1']:.3f}")
        print(f"其他模型 - MOTA: {advantage['other_metrics']['mota']:.3f}, "
              f"IDF1: {advantage['other_metrics']['idf1']:.3f}")
    
    return best_segments

# 如果直接运行此文件，执行分析
if __name__ == "__main__":
    analyze_and_report()
