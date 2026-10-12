import cv2
import os
from src.screen.classifier import ScreenClassifier
from src.core.config import Config
from tools.util import draw_roi, show_image

def get_logo_rois(img, config):
    """
    画像サイズに応じてVS/WIN/LOSEロゴのROI座標を計算して返す。
    """
    h, w = img.shape[:2]
    roi_conf = config.get("roi", default={})
    rois = {}
    for key in ["vs", "win", "lose"]:
        x1r, y1r, x2r, y2r = roi_conf.get(key, [0,0,0,0])
        x1 = int(w * x1r)
        y1 = int(h * y1r)
        x2 = int(w * x2r)
        y2 = int(h * y2r)
        rois[key.upper()] = (x1, y1, x2, y2)
    return rois

def main():
    """
    サンプル画像群に対して画面種別判定を実行し、判定結果と共にVS/WIN/LOSEロゴのROIを可視化する。
    """
    config = Config("config/config.yaml")
    base_folder = config.get("tools", "screen_classifier_visualizer", "sample_frames_dir")
    classifier = ScreenClassifier("config/config.yaml")
    img_paths = []
    for root, _, files in os.walk(base_folder):
        for file in files:
            if file.lower().endswith(".png"):
                img_paths.append(os.path.join(root, file))
    if not img_paths:
        print(f"No images found in {base_folder}")
        return

    for img_path in img_paths:
        img = cv2.imread(img_path)
        screen_type, vs_score = classifier.classify(img)
        print(f"{img_path}: {screen_type} (VS: {vs_score:.3f})")

        rois = get_logo_rois(img, config)
        preview = img.copy()
        preview = draw_roi(preview, rois["VS"], (255,0,0), "VS")
        preview = draw_roi(preview, rois["WIN"], (0,255,0), "WIN")
        preview = draw_roi(preview, rois["LOSE"], (0,0,255), "LOSE")
        show_image(preview, f"Preview: {img_path}")

if __name__ == "__main__":
    main()
