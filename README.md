# 日本の車両番号登録地名一覧 / Japanese License Plate Location Names

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)
[![Update Data](https://github.com/kyto64/number-plate-japan.csv/actions/workflows/update-plate-data.yml/badge.svg)](https://github.com/kyto64/number-plate-japan.csv/actions/workflows/update-plate-data.yml)

日本の自動車ナンバープレートに表示される「登録地名」の一覧データをCSV形式で提供するオープンソースプロジェクトです。

Wikipedia「日本のナンバープレート一覧」から自動的にデータを取得し、週次で最新情報に更新されます。

## 📋 概要

このプロジェクトは、日本全国の運輸支局・自動車検査登録事務所で使用されている登録地名を体系的にまとめたデータセットを提供します。MediaWiki APIとpandas.read_htmlを使用したロバストなデータ取得システムにより、高い信頼性を実現しています。

## 📊 提供データ

### `number_plate_japan.csv`

| 列名 | 説明 | 例 |
|------|------|-----|
| 地名 | ナンバープレートに表示される地名 | 品川、なにわ、福岡 |
| 都道府県 | 地名が属する都道府県 | 東京都、大阪府、福岡県 |
| 運輸支局 | 管轄する運輸支局の階層情報 | 関東運輸局 東京運輸支局 |
| 自動車検査登録事務所名 | 具体的な事務所名・庁舎名 | 本庁舎、品川自動車検査登録事務所 |
| 読み仮名 | 地名の読み仮名（ひらがな） | しながわ、なにわ、ふくおか |

### サンプルデータ

```csv
地名,都道府県,運輸支局,自動車検査登録事務所名,読み仮名
札幌,北海道,北海道運輸局 札幌運輸支局,本庁舎,さっぽろ
品川,東京都,関東運輸局 東京運輸支局,品川自動車検査登録事務所,しながわ
練馬,東京都,関東運輸局 東京運輸支局,練馬自動車検査登録事務所,ねりま
なにわ,大阪府,近畿運輸局 大阪運輸支局,なにわ自動車検査登録事務所,なにわ
福岡,福岡県,九州運輸局 福岡運輸支局,本庁舎,ふくおか
```

## 🚀 使用方法

### 直接ダウンロード

```bash
# 最新版をダウンロード
curl -O https://raw.githubusercontent.com/kyto64/number-plate-japan.csv/main/number_plate_japan.csv

# wgetを使用する場合
wget https://raw.githubusercontent.com/kyto64/number-plate-japan.csv/main/number_plate_japan.csv
```

### Python での利用例

```python
import pandas as pd

# GitHubから直接読み込み
url = "https://raw.githubusercontent.com/kyto64/number-plate-japan.csv/main/number_plate_japan.csv"
df = pd.read_csv(url)

# 特定の地名を検索
result = df[df['地名'] == '品川']
print(result)

# 都道府県で絞り込み
tokyo_plates = df[df['都道府県'] == '東京都']
print(tokyo_plates)

# 運輸支局の階層情報で検索
kanto_plates = df[df['運輸支局'].str.contains('関東運輸局', na=False)]
print(kanto_plates)

# 特定の事務所名で検索
honcho_offices = df[df['自動車検査登録事務所名'] == '本庁舎']
print(honcho_offices)
```

### JavaScript での利用例

```javascript
// fetch APIを使用
async function getPlateData() {
    const url = "https://raw.githubusercontent.com/kyto64/number-plate-japan.csv/main/number_plate_japan.csv";
    const response = await fetch(url);
    const csvText = await response.text();

    // CSVをパース（csv-parserライブラリを使用することを推奨）
    const lines = csvText.split('\n');
    const headers = lines[0].split(',');

    return lines.slice(1).map(line => {
        const values = line.split(',');
        return headers.reduce((obj, header, index) => {
            obj[header] = values[index];
            return obj;
        }, {});
    });
}

// 使用例
getPlateData().then(data => {
    const shinagawa = data.find(item => item['地名'] === '品川');
    console.log(shinagawa);
});
```

## 📝 データの特徴

- **最新性**: Wikipedia「日本のナンバープレート一覧」から自動取得される最新データ
- **完全性**: 全国138地名すべての登録地名を網羅（重複地名も適切に保持）
- **詳細性**: 運輸支局の階層構造と具体的な事務所名を分離して提供
- **一貫性**: 統一されたフォーマットでの提供
- **安定性**: MediaWiki APIとpandas.read_htmlによる高信頼性データ取得
- **自動更新**: GitHub Actionsによる週次自動更新システム

## 🤖 自動化システム

このプロジェクトは以下の技術により自動化されています：

### データ取得技術
- **MediaWiki API**: 安定したWikipediaコンテンツ取得
- **pandas.read_html**: 複雑なHTMLテーブル（rowspan/colspan）の自動解析
- **GitHub Actions**: 週次スケジュール実行とプルリクエスト自動作成

### アーキテクチャ
```
scripts/
├── constants.py      # API設定、ファイルパス、都道府県リスト
├── dictionaries.py   # 文字変換辞書、読み仮名マッピング
└── fetch_wiki_data.py # メインデータ取得ロジック
```

## 🔄 更新方針

- **自動更新**: 毎週日曜日午前9時（JST）に自動実行
- **変更検出**: データに差分がある場合のみプルリクエストを自動作成
- **手動実行**: GitHub Actionsから手動実行も可能
- **コミュニティ貢献**: プルリクエストによる修正提案を歓迎

## 📄 ライセンス

このプロジェクトは [CC0 1.0 Universal](LICENSE) ライセンスの下で公開されています。商用・非商用を問わず自由にご利用いただけます。

## 🤝 貢献

データの修正や追加がある場合は、以下の方法で貢献をお願いします：

1. このリポジトリをフォーク
2. 修正ブランチを作成
3. 変更をコミット
4. プルリクエストを作成

### 修正時の注意点

- CSVフォーマットを維持してください（5カラム構造）
- 読み仮名はひらがなで統一してください
- 運輸支局は階層構造を保持してください
- 自動化システムによる更新との競合を避けるため、手動修正は慎重に行ってください

### 開発者向け情報

```bash
# 依存関係のインストール
pip install requests pandas lxml html5lib

# データ取得スクリプトの実行
python -m scripts.fetch_wiki_data

# テスト実行
python -c "
import pandas as pd
df = pd.read_csv('number_plate_japan.csv')
print(f'総レコード数: {len(df)}')
print(f'カラム: {list(df.columns)}')
"
```

## 📞 お問い合わせ

- Issues: [GitHub Issues](https://github.com/kyto64/number-plate-japan.csv/issues)
- データの不備報告や機能要望もIssuesでお知らせください
- 自動更新システムに関する問題や提案も歓迎します

## 🙏 謝辞

本データセットはWikipedia「日本のナンバープレート一覧」の情報を基に作成されています。Wikipediaコミュニティの皆様に感謝いたします。

## 🏗️ 技術仕様

- **データソース**: Wikipedia MediaWiki API
- **実行環境**: GitHub Actions (Ubuntu latest)
- **Python**: 3.11+
- **主要ライブラリ**: requests, pandas, lxml, html5lib
- **更新頻度**: 週次（毎週日曜日 09:00 JST）
- **データ形式**: UTF-8 CSV

---

**注意**: このデータは参考情報として提供されます。公式な手続きには必ず最新の公的資料をご確認ください。
