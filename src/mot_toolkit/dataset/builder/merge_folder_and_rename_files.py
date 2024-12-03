import os


def rename(path, strat_index):
    source_dir = os.path.join(path, "ships")
    file_list = os.listdir(source_dir)
    seq_name_list = []
    for file_name in file_list:
        seq_name_list.append(file_name.split("_")[0])
    seq_name_list = list(set(seq_name_list))
    print(seq_name_list)
    seq_len = 0
    for seq_name in seq_name_list:
        if not os.path.exists(os.path.join(path, seq_name)):
            os.makedirs(os.path.join(path, seq_name))

        frame_name_idx = []
        seq_img_list = []
        for file_name in file_list:
            if seq_name in file_name:
                seq_img_list.append(file_name)
                frame_name_idx.append(int(file_name.split("_")[1].split(".")[0]))
            frame_name_idx.sort()
        seq_len = len(seq_img_list)

        for idx, img in enumerate(seq_img_list):
            ori_img_path = os.path.join(source_dir, img)
            os.rename(
                ori_img_path,
                os.path.join(path, seq_name, "{:06d}.jpg".format(strat_index + idx)),
            )

        strat_index += seq_len


strat_index = 8001
path = r"D:\Dataset\new_label"

rename(path, strat_index)
