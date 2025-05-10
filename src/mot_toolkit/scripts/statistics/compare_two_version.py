"""
比较同一数据集的两个版本

用于人工优化标注后，与旧版进行对比

工作原理：
1. 同时读取两个版本的数据集，得到两个版本的数据集的文件列表
2. 对应帧的每一个ID的BBox进行比较
        对于相同的ID，每帧的BBox进行比较
                如果old版本存在，new版本不存在，则为旧版标注错误，记录为旧版标注错误
                如果old版本不存在，new版本存在，则为旧版漏标注，记录为补充标注
                如果old版本和new版本都存在，则进行BBox的比较
                        如果old版本和new版本的BBox的IoU大于0.9，则为未修改
                        如果old版本和new版本的BBox的IoU小于阈值，则为修改标注，记录为修改标注
    对于不同的ID
            如果old版本存在这个ID，new版本不存在这个ID，则为旧版标注错误，记录为旧版标注错误
        如果old版本不存在这个ID，new版本存在这个ID，则为新增标注，记录为新增标注
"""

old_version_path = r"H:\Datasets\SMD\SMD_LabelMe_Ori"
new_version_path = r"H:\Datasets\SMD\SMD_LabelMe_20250509"
