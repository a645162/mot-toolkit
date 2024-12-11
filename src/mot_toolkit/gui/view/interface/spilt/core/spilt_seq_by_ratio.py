import multiprocessing
import os
import shutil

from mot_toolkit.dataset.utils.dataset_dir import get_dataset_dir_list
from mot_toolkit.datatype.xanylabeling import XAnyLabelingAnnotationDirectory
from mot_toolkit.gui.view.interface.spilt.core.ratio_handler import get_annotation_directory_by_ratio
from mot_toolkit.utils.logs import get_logger

logger = get_logger()


class SpiltSeqByRatio:
    train_ratio: float = 0.7
    val_ratio: float = 0.3
    test_ratio: float = 0

    name_depth = 2

    file_name_start = 1
    file_name_length = 8

    train_dir_path: str = ""
    val_dir_path: str = ""
    test_dir_path: str = ""

    def handle_sequence_output(
            self,
            output_dir: str,
            annotation_directory: XAnyLabelingAnnotationDirectory
    ):
        def get_prefix() -> str:
            current_level = self.name_depth - 1
            current_dir = annotation_directory.dir_path

            prefix_name = os.path.basename(current_dir)
            current_dir = os.path.dirname(current_dir)

            while current_level > 0:
                prefix_name = os.path.basename(current_dir) + "_" + prefix_name
                current_dir = os.path.dirname(current_dir)
                current_level -= 1

            return prefix_name

        prefix_name = get_prefix()

        target_dir = os.path.join(output_dir, prefix_name)
        os.makedirs(target_dir, exist_ok=True)

        path_img1 = os.path.join(target_dir, "img1")
        path_gt = os.path.join(target_dir, "gt")
        if not os.path.exists(path_img1):
            os.makedirs(path_img1, exist_ok=True)
        if not os.path.exists(path_gt):
            os.makedirs(path_gt, exist_ok=True)
        path_gt_txt = os.path.join(path_gt, "gt.txt")
        path_seq_info_ini = os.path.join(target_dir, "seqinfo.ini")

        for i, file_obj in enumerate(annotation_directory.annotation_file_list):
            current_index = i + self.file_name_start

            source_path_jpeg = file_obj.file_path.replace(".json", ".jpg")
            target_path_jpeg = os.path.join(
                path_img1,
                format(current_index, f"0{self.file_name_length}") + ".jpg"
            )

            if os.path.exists(target_path_jpeg):
                # Remove if already exists
                os.remove(target_path_jpeg)

            shutil.copyfile(source_path_jpeg, target_path_jpeg)

            yolo_text_list = []
            for rect_obj in file_obj.rect_annotation_list:
                group_id = rect_obj.group_id.strip()

                if group_id == "":
                    logger.error(f"Object({rect_obj.label}) Group ID is Empty! {file_obj.file_path}")
                    continue

                x_ratio = rect_obj.center_x_ratio
                y_ratio = rect_obj.center_y_ratio
                w_ratio = rect_obj.width_ratio
                h_ratio = rect_obj.height_ratio

                round_count = 6
                x_ratio = round(x_ratio, round_count)
                y_ratio = round(y_ratio, round_count)
                w_ratio = round(w_ratio, round_count)
                h_ratio = round(h_ratio, round_count)

                line = (f"{group_id} "
                        f"{x_ratio} "
                        f"{y_ratio} "
                        f"{w_ratio} "
                        f"{h_ratio}")
                yolo_text_list.append(line)

            yolo_text = "\n".join(yolo_text_list)
            target_path_txt = target_path_jpeg.replace(".jpg", ".txt")
            with open(target_path_txt, "w") as f:
                f.write(yolo_text)

        # gt.txt
        with open(path_gt_txt, "w") as f:
            f.write(annotation_directory.to_mot_gt_txt(
                start_index=self.file_name_start
            ))

        # seqinfo.ini
        with open(path_seq_info_ini, "w") as f:
            f.write(annotation_directory.to_mot_seq_info_ini())

    def handle_sequence_dir(
            self,
            seq_dir: str
    ):
        logger.info(f"Processing: {seq_dir}")
        (
            train_dir_obj,
            val_dir_obj,
            test_dir_obj
        ) = get_annotation_directory_by_ratio(
            seq_dir,
            train_ratio=self.train_ratio,
            val_ratio=self.val_ratio,
            test_ratio=self.test_ratio
        )

        # Train
        self.handle_sequence_output(
            output_dir=self.train_dir_path,
            annotation_directory=train_dir_obj
        )

        # Val
        self.handle_sequence_output(
            output_dir=self.val_dir_path,
            annotation_directory=val_dir_obj
        )

        if len(test_dir_obj.file_list) > 0:
            # Test
            self.handle_sequence_output(
                output_dir=self.test_dir_path,
                annotation_directory=test_dir_obj
            )

    def output_dataset_by_ratio(
            self,
            base_dir: str,
            output_dir: str,
    ):
        dance_track_dir = os.path.join(output_dir, "DanceTrack")

        train_dir = os.path.join(dance_track_dir, "train")
        val_dir = os.path.join(dance_track_dir, "val")
        test_dir = os.path.join(dance_track_dir, "test")

        os.makedirs(train_dir, exist_ok=True)
        os.makedirs(val_dir, exist_ok=True)
        os.makedirs(test_dir, exist_ok=True)

        self.train_dir_path = train_dir
        self.val_dir_path = val_dir
        self.test_dir_path = test_dir

        black_keywords = []
        black_txt_path = "black_keywords.txt"
        if os.path.exists(black_txt_path):
            with open(black_txt_path, "r") as f:
                black_keywords = f.readlines()
                black_keywords = [
                    keyword.strip()
                    for keyword in black_keywords
                    if keyword.strip() != ""
                ]

        print(f"Black Keywords({len(black_keywords)}):")
        for keyword in black_keywords:
            print(f"  {keyword}")

        seq_list = get_dataset_dir_list(
            dataset_dir_path=base_dir,
            depth=1
        )

        final_seq_list = []
        for seq_dir in seq_list:
            found = False
            for keyword in black_keywords:
                if keyword in seq_dir:
                    found = True
                    break

            if not found:
                final_seq_list.append(seq_dir)
        seq_list = final_seq_list

        input("Press Enter to Continue...")

        # Multi-Process
        logger.info("Multi-Processing")
        logger.info(f"Total sequences: {len(seq_list)}")

        with multiprocessing.Pool(processes=8) as pool:
            pool.map(self.handle_sequence_dir, seq_list)

        print("Done!")


def main():
    # 在 Windows 上这是默认值，但为了明确起见可以显式设置
    multiprocessing.set_start_method('spawn')

    spilt_seq_by_ratio = SpiltSeqByRatio()

    spilt_seq_by_ratio.output_dataset_by_ratio(
        base_dir=r"H:\Datasets\MaritimeTrackAllData\LabelMe",
        output_dir=r"H:\Datasets\MaritimeTrackAllData\Spilt\MaritimeTrack_Full_Same",
    )


if __name__ == "__main__":
    main()
