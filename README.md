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
├── templates/                       # テンプレートマッチング用画像（vs/win/lose）
└── tools/                           # デバッグ・可視化ツール
```

---

## バージョン情報

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
