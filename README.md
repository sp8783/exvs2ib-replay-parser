# EXVS2IB Replay Parser

**機動戦士ガンダム エクストリームバーサス2 インフィニットブースト（EXVS2IB）** の対戦動画から、試合開始タイムスタンプを自動抽出するツールです。

---

## 概要

YouTubeなどに投稿された対戦動画を対象に、テンプレートマッチングで画面種別（マッチング画面・リザルト画面）を識別し、試合ごとの開始タイムスタンプをCSVに記録します。

---

## 機能

- **動画処理**: 動画からフレームを抽出（デフォルトは2秒間隔）
- **画面判定**: マッチング画面・リザルト画面をテンプレートマッチングで識別
- **タイムスタンプ抽出**: 試合開始時刻をHH:MM:SS形式でCSV出力（メイン機能）
- **キャッシュ機能**: 2回目以降の実行を高速化
- **GitHub Actions**: 動画DL → 解析 → vsmobile-kgy へタイムスタンプ自動送信（`analyze.yml`）
- **[実験的] OCR解析**: `--with-ocr` フラグでプレイヤー名・機体名・勝敗も抽出（精度は保証されない）

---

## 技術スタック

- 言語: Python 3.13.5
- OCRエンジン: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- 主要ライブラリ: OpenCV, pytesseract, NumPy, pandas, RapidFuzz, tqdm

---

## 導入方法

### 1. リポジトリを取得

```bash
git clone https://github.com/sp8783/exvs2ib-replay-parser.git
```

### 2. 必要なライブラリをインストール

```bash
pip install -r requirements.txt
```

### 3. Tesseractをインストール

- macOS: `brew install tesseract`
- Ubuntu: `sudo apt-get install tesseract-ocr tesseract-ocr-jpn`
- Windows: [Tesseract公式ページ](https://github.com/UB-Mannheim/tesseract/wiki) からインストーラを利用

---

## 使用方法

### タイムスタンプ抽出（デフォルト）

```bash
python main.py --input data/video.mp4
```

処理結果は `output/results/timestamps_{動画名}.csv` に保存されます。

### 設定ファイルを指定する場合

```bash
python main.py --input data/video.mp4 --config config/config.yaml
```

### [実験的] プレイヤー名・機体名・勝敗も抽出

```bash
python main.py --input data/video.mp4 --with-ocr
```

> **注意**: OCR精度は保証されません。プレイヤー名・機体名の誤認識が発生することがあります。

### 試合開始の判定のしかた

- VS 画面は、実際の VS 画面から作った見本（`templates/vs.png`）と、ロゴの形の部分だけを比べるマスク（`templates/vs_mask.png`）で判定します。背景は試合ごとに違うため、比べません。
- VS ロゴとの類似度が `vs_threshold` 以上のコマが `vs_min_frames` コマ以上続く区間を VS 画面とみなし、そのあと次の VS 画面までにリザルト画面があれば 1 試合と数えます。
- 試合開始の時刻は、類似度が `vs_start_threshold` 以上のコマ（ロゴが飛び込んでくる途中のコマ）までさかのぼった時刻です。

### 精度の確認

正しいタイムスタンプの CSV（`match_number,start_time`）と比べて、試合数と時刻の違いを表示します。

```bash
# ファイルどうしを比べる
python -m tools.evaluate_timestamps --expected 正解.csv --actual output/results/timestamps_video.csv

# ディレクトリを渡すと、同じ名前の timestamps_{動画名}.csv どうしを比べる
python -m tools.evaluate_timestamps --expected 正解のディレクトリ --actual output/results
```

### VS 画面の見本を作り直す

ゲームの更新で VS 画面の見た目が変わったときは、動画とその動画の正しいタイムスタンプから見本とマスクを作り直します（720p 以上の動画がおすすめ）。

```bash
python -m tools.build_vs_template --input data/video.mp4 --timestamps 正解.csv
```

---

## GitHub Actions による自動解析

`analyze.yml` ワークフローを使うと、YouTube配信アーカイブのURLを指定するだけで、動画DL → 解析 → vsmobile-kgy へのタイムスタンプ自動送信が実行されます。

**必要なシークレット:**
- `VSMOBILE_FOR_KGY_API_URL` — vsmobile-kgy のベースURL
- `VSMOBILE_FOR_KGY_API_TOKEN` — 認証トークン
- `YOUTUBE_COOKIES` — YouTube認証が必要な場合のクッキー（任意）

---

## ファイル構成

```plaintext
exvs2ib-replay-parser/
├── main.py                          # メインエントリーポイント
├── requirements.txt
├── config/
│   └── config.yaml                  # OCR設定・ROI座標など
├── data/
│   ├── player_names.csv             # プレイヤー名候補DB
│   └── unit_names.csv               # 機体名候補DB
├── output/
│   ├── cache/                       # キャッシュ
│   ├── frames/                      # 抽出フレーム（matching/result のみ保存）
│   └── results/                     # CSV出力
├── src/
│   ├── core/                        # パイプライン統括・設定管理
│   ├── video/                       # 動画フレーム抽出
│   ├── screen/                      # 画面種別分類
│   ├── processing/                  # 試合結果抽出
│   ├── ocr/                         # OCR処理（実験的）
│   └── util/                        # キャッシュ・I/O・画像処理
├── templates/                       # テンプレートマッチング用画像（vs/vs_mask/win/lose）
└── tools/                           # デバッグ・可視化・精度確認・見本作成のツール
```

---

## バージョン情報

### v1.2.0

- VS 画面の判定を作り直し、試合数が実際より多く検出される問題を修正（実際の VS 画面から作った見本で、ロゴの形の部分だけを比べる）
- 精度を確かめるツール（`tools/evaluate_timestamps.py`）と、VS 画面の見本を作り直すツール（`tools/build_vs_template.py`）を追加
- 画面判定のキャッシュの形式を変更（前のバージョンのキャッシュは使わず、判定し直す）

### v1.1.0

- GitHub Actions ワークフロー失敗時に vsmobile-kgy API へ通知する機能を追加

### v1.0.0

- タイムスタンプ抽出をメイン機能として整理（`--with-ocr` なしがデフォルト）
- コードリファクタリング: グローバル依存解消・デッドコード削除・型ヒント追加
- GitHub Actions ワークフロー: YouTube DL → 解析 → vsmobile-kgy 自動送信

### v0.1.0（初期実装）

- 動画フレーム抽出（デフォルトは2秒間隔）
- 画面判定（マッチング/リザルト画面）
- OCRによるプレイヤー名・機体名の抽出
- CSV出力とキャッシュ機能
- デバッグツール（画面判定・OCR結果・ROI選択）
