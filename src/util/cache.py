import os
from src.util.io import save_pickle, load_pickle, ensure_dir


class CacheManager:
    """
    フレーム抽出・画面検出結果のキャッシュ管理を行うクラス。
    """

    def __init__(self, cache_dir: str, video_basename: str) -> None:
        self.cache_dir = cache_dir
        self.video_basename = video_basename
        self.frames_cache_file = os.path.join(cache_dir, f"frame_cache_{video_basename}.pkl")
        # 画面判定の結果の形が変わったら番号を上げ、古いキャッシュを使わないようにする
        self.screens_cache_file = os.path.join(cache_dir, f"screen_cache_v2_{video_basename}.pkl")
        ensure_dir(cache_dir)

    def has_frames_cache(self) -> bool:
        """
        フレーム抽出のキャッシュファイルが存在するかどうかを判定する。
        """
        return os.path.exists(self.frames_cache_file)

    def has_screens_cache(self) -> bool:
        """
        画面判定のキャッシュファイルが存在するかどうかを判定する。
        """
        return os.path.exists(self.screens_cache_file)

    def load_frames_cache(self) -> list:
        """
        フレーム抽出結果をキャッシュから読み込む。
        """
        print(f"フレーム抽出キャッシュを {self.frames_cache_file} から読み込みました。")
        return load_pickle(self.frames_cache_file)

    def save_frames_cache(self, frame_paths: list) -> None:
        """
        フレーム抽出結果をキャッシュに保存する。
        """
        save_pickle(frame_paths, self.frames_cache_file)
        print(f"フレーム抽出結果を {self.frames_cache_file} に保存しました。")

    def load_screens_cache(self) -> tuple:
        """
        画面判定結果をキャッシュから読み込む。
        """
        print(f"画面判定キャッシュを {self.screens_cache_file} から読み込みました。")
        return load_pickle(self.screens_cache_file)

    def save_screens_cache(self, screens: list, match_count: int) -> None:
        """
        画面判定結果をキャッシュに保存する。
        """
        result = (screens, match_count)
        save_pickle(result, self.screens_cache_file)
        print(f"画面判定結果を {self.screens_cache_file} に保存しました。")
