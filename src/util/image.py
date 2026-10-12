import cv2
import numpy as np


def get_player_unit_roi_from_ratio(img: np.ndarray, roi_config: dict) -> dict[str, tuple[int, int, int, int]]:
    """
    画像サイズに応じて割合から領域座標を計算して返す関数。
    プレイヤー名・機体名の領域座標を辞書で返す。
    """
    h, w = img.shape[:2]
    regions = {}
    for key, (x1r, y1r, x2r, y2r) in roi_config.items():
        x1 = int(w * x1r)
        y1 = int(h * y1r)
        x2 = int(w * x2r)
        y2 = int(h * y2r)
        regions[key] = (x1, y1, x2, y2)
    return regions


def get_roi(img: np.ndarray, roi: tuple[int, int, int, int]) -> np.ndarray:
    """
    指定したROI座標から画像領域を切り出して返す関数。
    """
    x1, y1, x2, y2 = roi
    return img[y1:y2, x1:x2]


def resize_to_template(region: np.ndarray, template: np.ndarray) -> np.ndarray:
    """
    regionをテンプレート画像のサイズにリサイズする関数。
    """
    if template is None:
        raise FileNotFoundError(f"テンプレート画像が見つかりません。")
    h, w = template.shape[:2]
    region_resized = cv2.resize(region, (w, h), interpolation=cv2.INTER_AREA)
    return region_resized


def roi_ratio_to_absolute(img: np.ndarray, roi_ratio: list | tuple) -> tuple[int, int, int, int]:
    """
    ROIの割合指定を絶対座標に変換する汎用関数。
    """
    h, w = img.shape[:2]
    x1 = int(w * roi_ratio[0])
    y1 = int(h * roi_ratio[1])
    x2 = int(w * roi_ratio[2])
    y2 = int(h * roi_ratio[3])
    return (x1, y1, x2, y2)


def crop_at_base_size(img: np.ndarray, roi_ratio: list | tuple, base_size: tuple[int, int], margin: int = 0) -> np.ndarray:
    """
    画像を基準の大きさ（base_size）にそろえたときのROI（周りに margin px 広げる）を切り出して返す関数。
    画像全体ではなく、ROIだけを基準の大きさに拡大・縮小する。
    """
    base_w, base_h = base_size
    x1, y1, x2, y2 = (int(base_w * roi_ratio[0]) - margin, int(base_h * roi_ratio[1]) - margin,
                      int(base_w * roi_ratio[2]) + margin, int(base_h * roi_ratio[3]) + margin)
    h, w = img.shape[:2]
    region = img[round(y1 * h / base_h):round(y2 * h / base_h), round(x1 * w / base_w):round(x2 * w / base_w)]
    return cv2.resize(region, (x2 - x1, y2 - y1), interpolation=cv2.INTER_LINEAR)
