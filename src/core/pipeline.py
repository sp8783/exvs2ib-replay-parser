import os
import pandas as pd
from src.core.config import Config
from src.processing.match_detector import detect_matches
from src.processing.match_extractor import MatchExtractor
from src.util.io import ensure_dir, save_dataframe_csv, save_screen_log
from src.util.cache import CacheManager
from src.util.timestamp import calculate_timestamp
from src.video.handler import extract_and_classify_frames


class Pipeline:
    """
    動画解析パイプライン全体を統括するメインクラス。
    各処理は専用クラスに委譲し、全体のフローを管理する。
    """

    def __init__(self, video_path: str, config_path: str, with_ocr: bool = False) -> None:
        self.config = Config(config_path)
        self.config_path = config_path
        self.video_path = video_path
        self.video_basename = os.path.splitext(os.path.basename(video_path))[0]
        self.with_ocr = with_ocr

        # ディレクトリ設定
        self.frames_dir = os.path.join(self.config.get("output", "frames", default="output/frames"), self.video_basename)
        self.cache_dir = os.path.join(self.config.get("output", "cache", default="output/cache"))
        self.results_dir = os.path.join(self.config.get("output", "results", default="output/results"))

        # 各種マネージャー・プロセッサーの初期化
        self.cache_manager = CacheManager(self.cache_dir, self.video_basename)
        self.frame_interval = self.config.get("video", "frame_interval")
        self.vs_threshold = self.config.get("template", "vs_threshold", default=0.8)
        self.vs_min_frames = self.config.get("template", "vs_min_frames", default=2)
        if self.with_ocr:
            self.match_extractor = MatchExtractor(self.frame_interval, self.config)

        self._prepare_output_dirs()

    def _prepare_output_dirs(self) -> None:
        """
        必要なディレクトリを作成する。
        """
        ensure_dir(self.frames_dir)
        ensure_dir(self.results_dir)

    def run_pipeline(self) -> None:
        """
        パイプライン全体を実行する。
        """
        # 1. フレーム抽出＋画面判定（統合フロー、キャッシュ対応）
        screens, _ = self._extract_and_classify_with_cache()

        # 2. VS 画面 → リザルト画面の並びから試合を検出
        matches = detect_matches(screens, self.vs_threshold, self.vs_min_frames)

        if self.with_ocr:
            # 試合結果抽出（実験的）
            results = self.match_extractor.extract_match_results(matches)
            self._save_results_to_csv(results)
        else:
            # タイムスタンプのみ出力（デフォルト）
            timestamps = self._extract_timestamps(matches)
            self._save_timestamps_to_csv(timestamps)

    def _extract_and_classify_with_cache(self) -> tuple:
        """
        フレーム抽出＋画面判定の統合フロー（キャッシュ対応）。
        screens_cache があればそのまま使い、なければ統合処理を実行する。
        """
        if self.cache_manager.has_screens_cache():
            return self.cache_manager.load_screens_cache()

        screens, match_count, log_rows = extract_and_classify_frames(
            self.video_path,
            self.config.get("video", "frame_interval"),
            self.frames_dir,
            self.config_path,
        )
        save_screen_log(log_rows, self.results_dir)
        self.cache_manager.save_screens_cache(screens, match_count)
        return screens, match_count

    def _extract_timestamps(self, matches: list[dict]) -> list[dict]:
        """
        検出した試合ごとに、最初の VS 画面のコマのタイムスタンプを返す。
        """
        return [
            {
                "match_number": match_number,
                "start_time": calculate_timestamp(os.path.basename(match["matching_frames"][0]["path"]), self.frame_interval),
            }
            for match_number, match in enumerate(matches, 1)
        ]

    def _save_timestamps_to_csv(self, timestamps: list[dict]) -> None:
        """
        試合開始タイムスタンプをCSVファイルに保存する。
        """
        output_path = os.path.join(self.results_dir, f"timestamps_{self.video_basename}.csv")
        dataframe = pd.DataFrame(timestamps)
        save_dataframe_csv(dataframe, output_path)
        print(f"タイムスタンプを {output_path} に保存しました。")

    def _save_results_to_csv(self, results: list[dict]) -> None:
        """
        試合結果をCSVファイルに保存する。
        """
        output_path = os.path.join(self.results_dir, f"result_{self.video_basename}.csv")
        dataframe = pd.DataFrame(results)
        save_dataframe_csv(dataframe, output_path)
        print(f"結果を {output_path} に保存しました。")
