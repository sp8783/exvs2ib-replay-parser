import cv2
import numpy as np
from src.core.config import Config
from src.util.image import crop_at_base_size, resize_to_template, roi_ratio_to_absolute


class ScreenClassifier:
    """
    画面種別（vs, win, lose, unknown）をテンプレートマッチングで判定するクラス。
    設定ファイルからテンプレート画像とROI情報を取得し、初期化時にテンプレート画像を読み込む。
    """

    def __init__(self, config_path: str = "config/config.yaml") -> None:
        """
        設定ファイルからテンプレート画像パス・ROI情報を取得し、テンプレート画像を事前に読み込む。
        """
        config = Config(config_path)
        self.threshold = config.get("template", "threshold", default=0.3)
        self.template_config = config.get("template", default={})
        self.roi_config = config.get("roi", default={})
        self.vs_start_threshold = self.template_config.get("vs_start_threshold", 0.65)
        self.vs_base_size = tuple(self.template_config.get("vs_base_size", [1280, 720]))
        self.vs_search_margin = self.template_config.get("vs_search_margin", 16)
        self.vs_template = self._load_template(self.template_config.get("vs"), cv2.IMREAD_COLOR)
        self.vs_mask = self._load_vs_mask(self.template_config.get("vs_mask"))
        self.win_template = self._load_template(self.template_config.get("win"))
        self.lose_template = self._load_template(self.template_config.get("lose"))

    def _load_template(self, template_path: str | None, flags: int = cv2.IMREAD_GRAYSCALE) -> np.ndarray | None:
        """
        指定パスのテンプレート画像を読み込む（既定はグレースケール）。
        """
        if template_path:
            return cv2.imread(template_path, flags)
        return None

    def _load_vs_mask(self, mask_path: str | None) -> np.ndarray | None:
        """
        VS テンプレートのマスク（比べる部分が白）を、カラーのテンプレートに合わせた 3 チャンネルで読み込む。
        """
        mask = self._load_template(mask_path)
        if mask is None:
            return None
        return cv2.merge([(mask > 127).astype(np.uint8)] * 3)

    def match_template(self, img: np.ndarray, template: np.ndarray, roi: tuple | None = None) -> bool:
        """
        指定したROI領域でテンプレートマッチングを行い、類似度が閾値以上ならTrueを返す。
        """
        threshold = self.threshold
        if roi:
            x1, y1, x2, y2 = roi
            img = img[y1:y2, x1:x2]
        region_resized = resize_to_template(img, template)
        region_gray = cv2.cvtColor(region_resized, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(region_gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return max_val >= threshold

    def vs_score(self, img: np.ndarray) -> float:
        """
        VS ロゴとの類似度を返す。
        フレームを基準の大きさ（vs_base_size）にそろえたときの ROI の周りを少しずつずらしながら、
        マスクの部分（毎回同じ見た目になるロゴの形）だけをカラーで比べ、いちばん高い点数を返す。
        """
        vs_roi = self.roi_config.get("vs")
        if self.vs_template is None or self.vs_mask is None or not vs_roi:
            return 0.0

        region = crop_at_base_size(img, vs_roi, self.vs_base_size, self.vs_search_margin)
        res = cv2.matchTemplate(region, self.vs_template, cv2.TM_CCOEFF_NORMED, mask=self.vs_mask)
        # 単色の画面などで分母が 0 になると NaN になるため、一致しないものとして扱う
        res = np.nan_to_num(res, nan=-1.0, posinf=-1.0, neginf=-1.0)
        return float(res.max())

    def classify(self, img: np.ndarray) -> tuple[str, float]:
        """
        画面種別（matching, result_win, result_lose, other）と VS ロゴの類似度を返す。
        matching は VS 画面の候補（ロゴが飛び込んでくる途中のコマを含む）で、
        本当に VS 画面かどうかは前後のコマとあわせて判定する（src/processing/match_detector.py）。
        """
        win_roi = self.roi_config.get("win")
        lose_roi = self.roi_config.get("lose")

        score = self.vs_score(img)
        if score >= self.vs_start_threshold:
            return "matching", score
        if self.win_template is not None and win_roi and self.match_template(img, self.win_template, roi_ratio_to_absolute(img, win_roi)):
            return "result_win", score
        if self.lose_template is not None and lose_roi and self.match_template(img, self.lose_template, roi_ratio_to_absolute(img, lose_roi)):
            return "result_lose", score
        return "other", score
