def detect_matches(screens: list[dict], vs_threshold: float, vs_min_frames: int) -> list[dict]:
    """
    画面判定結果から試合を検出し、試合ごとに
    {"matching_frames": VS 画面のコマのリスト（先頭が試合開始）, "result": リザルト画面のコマ} を返す。

    - 連続する matching のコマ（VS 画面の候補）を 1 つの区間とし、vs_threshold 以上のコマが
      vs_min_frames コマ以上続く区間だけを VS 画面とみなす（機体選択画面などの一瞬の見間違いを除く）
    - VS 画面のあと、次の VS 画面までにリザルト画面があれば 1 試合とする
    """
    runs = _matching_runs(screens)
    vs_runs = [run for run in runs if _longest_streak(run, vs_threshold) >= vs_min_frames]

    matches = []
    for i, run in enumerate(vs_runs):
        run_end = run[-1]["index"]
        next_start = vs_runs[i + 1][0]["index"] if i + 1 < len(vs_runs) else float("inf")
        result = next(
            (screen for screen in screens
             if screen["type"] in ("result_win", "result_lose") and run_end < screen["index"] < next_start),
            None,
        )
        if result:
            matches.append({"matching_frames": run, "result": result})
    return matches


def _matching_runs(screens: list[dict]) -> list[list[dict]]:
    """
    フレーム番号が連続する matching のコマをまとめた区間のリストを返す。
    """
    runs = []
    for screen in screens:
        if screen["type"] != "matching":
            continue
        if runs and runs[-1][-1]["index"] == screen["index"] - 1:
            runs[-1].append(screen)
        else:
            runs.append([screen])
    return runs


def _longest_streak(run: list[dict], threshold: float) -> int:
    """
    区間の中で、類似度が threshold 以上のコマが続く最長のコマ数を返す。
    """
    longest = current = 0
    for screen in run:
        current = current + 1 if screen["vs_score"] >= threshold else 0
        longest = max(longest, current)
    return longest
