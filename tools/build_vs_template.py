import argparse
import cv2
import numpy as np
from src.core.config import Config
from src.util.image import crop_at_base_size
from tools.evaluate_timestamps import load_timestamps

# 試合開始から何秒後のコマを見本にするか（ロゴが止まって表示されている間）
SAMPLE_OFFSETS = (4, 6, 8)
# コマごとの色のばらつきがこの値より小さい部分（ロゴの形）だけを比べる
DEFAULT_STD_MAX = 30


def read_frame_at(cap: cv2.VideoCapture, seconds: float) -> np.ndarray | None:
    """
    動画の指定した秒のコマを返す。
    """
    cap.set(cv2.CAP_PROP_POS_MSEC, seconds * 1000)
    ret, frame = cap.read()
    return frame if ret else None


def main() -> None:
    """
    動画と、その動画の正しい試合開始タイムスタンプから、VS 画面の見本とマスクを作る。
    各試合の VS 画面を切り出して重ね、コマごとの中央値を見本にする。
    背景は試合ごとに違うため、コマごとの色のばらつきが小さい部分（ロゴの形）だけをマスクで比べる部分にする。
    """
    parser = argparse.ArgumentParser(description="VS 画面の見本とマスクを作る")
    parser.add_argument("--input", required=True, help="動画ファイルのパス（720p 以上がおすすめ）")
    parser.add_argument("--timestamps", required=True, help="その動画の正しい試合開始タイムスタンプの CSV（match_number,start_time）")
    parser.add_argument("--config", default="config/config.yaml", help="設定ファイルのパス")
    parser.add_argument("--std-max", type=float, default=DEFAULT_STD_MAX,
                        help=f"比べる部分にする色のばらつきの上限（既定 {DEFAULT_STD_MAX}）")
    args = parser.parse_args()

    config = Config(args.config)
    roi_ratio = config.get("roi", "vs")
    base_size = tuple(config.get("template", "vs_base_size", default=[1280, 720]))
    template_path = config.get("template", "vs")
    mask_path = config.get("template", "vs_mask")

    cap = cv2.VideoCapture(args.input)
    if not cap.isOpened():
        raise FileNotFoundError(f"動画ファイルが開けません: {args.input}")
    crops = []
    for start in load_timestamps(args.timestamps):
        for offset in SAMPLE_OFFSETS:
            frame = read_frame_at(cap, start + offset)
            if frame is not None:
                crops.append(crop_at_base_size(frame, roi_ratio, base_size).astype(np.float32))
    cap.release()
    if not crops:
        raise ValueError("VS 画面のコマを読み込めませんでした。")

    stacked = np.stack(crops)
    template = np.median(stacked, axis=0).astype(np.uint8)
    mask = (stacked.std(axis=0).mean(axis=-1) < args.std_max).astype(np.uint8) * 255
    cv2.imwrite(template_path, template)
    cv2.imwrite(mask_path, mask)
    print(f"{len(crops)} コマから見本を {template_path} に、マスク（比べる部分 {np.mean(mask > 0):.0%}）を {mask_path} に保存しました。")


if __name__ == "__main__":
    main()
