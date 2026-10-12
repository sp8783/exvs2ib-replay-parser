import os
import cv2
from tqdm import tqdm
from src.core.config import Config
from src.ocr import ocr_on_matching_regions, Matcher
from src.util.timestamp import calculate_timestamp


class MatchExtractor:
    """
    マッチング画面→リザルト画面のペアごとにOCRを実行し、試合結果を抽出するクラス。
    """

    def __init__(self, frame_interval: float, config: Config) -> None:
        self.frame_interval = frame_interval
        self.config = config
        self.matcher = Matcher(config)

    def _get_match_timestamp(self, frame_name: str) -> str:
        """
        フレーム名からタイムスタンプを計算する。
        """
        return calculate_timestamp(frame_name, self.frame_interval)

    def extract_match_results(self, matches: list[dict]) -> list[dict]:
        """
        検出した試合（VS 画面のコマとリザルト画面）ごとにOCRを実行し、
        1試合分の情報を辞書としてまとめてリストで返す。
        """
        results = []
        for match in tqdm(matches, desc="試合情報抽出"):
            match_info = self._extract_single_match(match["matching_frames"], match["result"])
            if match_info:
                results.append(match_info)
        return results

    def _extract_single_match(self, matching_frames: list[dict], result_screen: dict) -> dict | None:
        """
        単一試合の情報を抽出する。
        """
        # OCR処理で最適なフレームを選択
        final_info, used_frame_name = self._find_best_ocr_result(matching_frames)

        # 勝敗情報を設定
        result_info = self._get_result_info(result_screen["type"])

        # タイムスタンプを追加
        match_timestamp = self._get_match_timestamp(used_frame_name)

        # 最終的な試合情報を作成
        return {
            **final_info,
            **result_info,
            "start_time": match_timestamp,
            "ocr_frame_name": used_frame_name
        }

    def _find_best_ocr_result(self, matching_frames: list[dict]) -> tuple[dict | None, str | None]:
        """
        マッチングフレーム群から最適なOCR結果を選択する。
        """
        final_info = None
        used_frame_name = None

        for frame in matching_frames:
            match_img = cv2.imread(frame["path"])
            match_info = ocr_on_matching_regions(match_img, self.config, self.matcher)

            # 欠損がなければ採用して終了
            if all(v is not None for v in match_info.values()):
                final_info = match_info
                used_frame_name = os.path.basename(frame["path"])
                break

            # 欠損がある場合も、より多く埋まったものを優先
            if final_info is None or sum(v is not None for v in match_info.values()) > sum(v is not None for v in final_info.values()):
                final_info = match_info
                used_frame_name = os.path.basename(frame["path"])

        return final_info, used_frame_name

    def _get_result_info(self, result_type: str) -> dict:
        """
        勝敗情報を取得する。
        """
        if result_type == "result_win":
            return {
                "player1_result": "WIN",
                "player2_result": "WIN",
                "player3_result": "LOSE",
                "player4_result": "LOSE"
            }
        else:
            return {
                "player1_result": "LOSE",
                "player2_result": "LOSE",
                "player3_result": "WIN",
                "player4_result": "WIN"
            }
