import argparse
import csv
import os
import sys

# 正解と検出のずれがこの秒数以内なら同じ試合とみなす
DEFAULT_TOLERANCE = 30


def load_timestamps(csv_path: str) -> list[int]:
    """
    match_number,start_time（HH:MM:SS）形式の CSV を読み込み、開始時刻を秒のリストで返す。
    """
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        return [to_seconds(row["start_time"]) for row in csv.DictReader(f)]


def to_seconds(text: str) -> int:
    hours, minutes, seconds = (int(part) for part in text.split(":"))
    return hours * 3600 + minutes * 60 + seconds


def to_hms(seconds: int) -> str:
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"


def align(expected: list[int], actual: list[int], tolerance: int) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """
    正解と検出を時刻の順に対応付ける（ずれの合計が最小になるように）。
    対応した組（正解の添字, 検出の添字）、余分な検出の添字、足りない正解の添字を返す。
    """
    n, m = len(expected), len(actual)
    inf = float("inf")
    cost = [[inf] * (m + 1) for _ in range(n + 1)]
    back = {}
    cost[0][0] = 0
    for i in range(n + 1):
        for j in range(m + 1):
            current = cost[i][j]
            if current == inf:
                continue
            steps = []
            if i < n and j < m and abs(expected[i] - actual[j]) <= tolerance:
                steps.append((i + 1, j + 1, abs(expected[i] - actual[j])))
            if i < n:
                steps.append((i + 1, j, tolerance + 1))
            if j < m:
                steps.append((i, j + 1, tolerance + 1))
            for ni, nj, step_cost in steps:
                if current + step_cost < cost[ni][nj]:
                    cost[ni][nj] = current + step_cost
                    back[(ni, nj)] = (i, j)

    pairs, extra, missing = [], [], []
    i, j = n, m
    while (i, j) != (0, 0):
        pi, pj = back[(i, j)]
        if pi < i and pj < j:
            pairs.append((pi, pj))
        elif pj < j:
            extra.append(pj)
        else:
            missing.append(pi)
        i, j = pi, pj
    return pairs[::-1], extra[::-1], missing[::-1]


def evaluate(name: str, expected_path: str, actual_path: str, tolerance: int) -> bool:
    """
    1 つの動画の検出結果を正解と比べて表示する。試合数・時刻がすべて正解と同じなら True を返す。
    """
    expected = load_timestamps(expected_path)
    actual = load_timestamps(actual_path)
    pairs, extra, missing = align(expected, actual, tolerance)
    shifted = [(e, a) for e, a in pairs if expected[e] != actual[a]]
    exact = not extra and not missing and not shifted

    print(f"[{name}] {'ぴったり' if exact else '違いあり'}: 正解 {len(expected)} 試合 / 検出 {len(actual)} 試合"
          f"（余分 {len(extra)}・足りない {len(missing)}・時刻のずれ {len(shifted)}）")
    for a in extra:
        gap = f"、前の検出から {actual[a] - actual[a - 1]} 秒" if a > 0 else ""
        print(f"  余分: 検出 {a + 1} 試合目 {to_hms(actual[a])}{gap}")
    for e in missing:
        print(f"  足りない: 正解 {e + 1} 試合目 {to_hms(expected[e])}")
    for e, a in shifted:
        print(f"  ずれ: 正解 {e + 1} 試合目 {to_hms(expected[e])} → 検出 {to_hms(actual[a])}（{actual[a] - expected[e]:+d} 秒）")
    return exact


def main() -> None:
    """
    検出したタイムスタンプを正解と比べ、試合数と時刻の違いを表示する。
    ディレクトリを渡したときは、正解の timestamps_<名前>.csv と同じ名前の検出結果どうしを比べる。
    違いが 1 つでもあれば終了コード 1 で終わる。
    """
    parser = argparse.ArgumentParser(description="検出したタイムスタンプを正解と比べる")
    parser.add_argument("--expected", required=True, help="正解の CSV、またはそれを置いたディレクトリ")
    parser.add_argument("--actual", default="output/results", help="検出結果の CSV、またはそれを置いたディレクトリ")
    parser.add_argument("--tolerance", type=int, default=DEFAULT_TOLERANCE,
                        help=f"同じ試合とみなす時刻のずれの上限（秒、既定 {DEFAULT_TOLERANCE}）")
    args = parser.parse_args()

    if os.path.isdir(args.expected):
        targets = []
        for file in sorted(os.listdir(args.expected)):
            if not (file.startswith("timestamps_") and file.endswith(".csv")):
                continue
            actual_path = os.path.join(args.actual, file)
            if os.path.exists(actual_path):
                targets.append((file[len("timestamps_"):-len(".csv")], os.path.join(args.expected, file), actual_path))
            else:
                print(f"[{file}] 検出結果がないため飛ばします: {actual_path}")
    else:
        targets = [(os.path.basename(args.actual), args.expected, args.actual)]

    results = [evaluate(name, expected, actual, args.tolerance) for name, expected, actual in targets]
    print(f"\n{sum(results)} / {len(results)} 本がぴったり")
    sys.exit(0 if results and all(results) else 1)


if __name__ == "__main__":
    main()
