#!/usr/bin/env python3
"""
pandas.read_htmlを使用してWikipedia「日本のナンバープレート一覧」からデータを取得し、
既存のCSVファイルと比較して差分があればPRを作成するスクリプト
"""

import os
import requests
from datetime import datetime
from typing import List, Dict, Tuple
import pandas as pd
import re

# 定数と辞書をインポート
from scripts.constants import (
    WIKIPEDIA_API_URL, PAGE_TITLE, CSV_FILE_PATH, CHANGES_FILE_PATH,
    PREFECTURES, CSV_COLUMNS
)
from scripts.dictionaries import KATAKANA_TO_HIRAGANA, PLATE_NAME_READINGS


class PlateDataFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; PlateDataBot/1.0; +https://github.com/kyto64/number-plate-japan.csv)'
        })

    def fetch_wikipedia_data(self) -> List[Dict[str, str]]:
        """MediaWiki APIとpandasを使用してWikipediaからナンバープレートデータを取得"""
        print(f"Wikipedia APIからデータを取得中: {PAGE_TITLE}")

        try:
            # MediaWiki APIでページの内容を取得
            params = {
                'action': 'parse',
                'page': PAGE_TITLE,
                'format': 'json',
                'prop': 'text',
                'disableeditsection': True,
                'wrapoutputclass': ''
            }

            response = self.session.get(WIKIPEDIA_API_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if 'parse' not in data or 'text' not in data['parse']:
                print("APIレスポンスが期待した形式ではありません")
                return []

            html_content = data['parse']['text']['*']

            # 一時的にHTMLファイルを作成してpandasで読み込む
            temp_html_file = "temp_wikipedia_table.html"
            with open(temp_html_file, 'w', encoding='utf-8') as f:
                f.write(html_content)

            try:
                # pandas.read_htmlでテーブルを抽出
                tables = pd.read_html(temp_html_file, encoding='utf-8')
                print(f"テーブル検出: 総数={len(tables)}")

                if not tables:
                    print("テーブルが見つかりませんでした")
                    return []

                # メインテーブル（最大のテーブル）を選択
                main_table = max(tables, key=lambda t: t.shape[0])
                print(f"メインテーブル形状: {main_table.shape}")

                # データを抽出
                plate_data = self._extract_from_dataframe(main_table)

                print(f"取得したレコード数: {len(plate_data)}")
                return plate_data

            finally:
                # 一時ファイルを削除
                if os.path.exists(temp_html_file):
                    os.remove(temp_html_file)

        except requests.exceptions.RequestException as e:
            print(f"ネットワークエラー: {e}")
            return []
        except KeyError as e:
            print(f"APIレスポンス解析エラー: {e}")
            return []
        except Exception as e:
            print(f"データ取得エラー: {e}")
            return []

    def _extract_from_dataframe(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """pandasのDataFrameからナンバープレートデータを抽出"""
        plate_data = []
        current_prefecture = ""

        print(f"DataFrame列名: {list(df.columns)}")

        for idx, row in df.iterrows():
            try:
                # NaNを空文字に変換
                row_values = [str(val) if pd.notna(val) else "" for val in row]

                # 都道府県の検出（通常1列目）
                if len(row_values) > 1 and self._is_prefecture(row_values[1]):
                    current_prefecture = row_values[1]
                    # 新しい都道府県行の場合、地名は3列目
                    if len(row_values) > 3:
                        plate_name = self._clean_plate_name(row_values[3])
                        if plate_name and self._is_valid_plate_name(plate_name):
                            transport_bureau, office_name = self._extract_transport_info(row_values, 4)
                            plate_info = {
                                '地名': plate_name,
                                '都道府県': current_prefecture,
                                '運輸支局': transport_bureau,
                                '自動車検査登録事務所名': office_name,
                                '読み仮名': self._generate_reading(plate_name)
                            }
                            plate_data.append(plate_info)

                else:
                    # 同一都道府県の追加行の場合
                    if current_prefecture and len(row_values) > 1:
                        plate_name = self._clean_plate_name(row_values[3] if len(row_values) > 3 else row_values[1])
                        if plate_name and self._is_valid_plate_name(plate_name):
                            transport_bureau, office_name = self._extract_transport_info(row_values, 4 if len(row_values) > 4 else 2)
                            plate_info = {
                                '地名': plate_name,
                                '都道府県': current_prefecture,
                                '運輸支局': transport_bureau,
                                '自動車検査登録事務所名': office_name,
                                '読み仮名': self._generate_reading(plate_name)
                            }
                            plate_data.append(plate_info)

            except Exception as e:
                print(f"行 {idx} の処理でエラー: {e}")
                continue

        return plate_data

    def _extract_transport_info(self, row_values: List[str], start_index: int) -> Tuple[str, str]:
        """運輸支局と自動車検査登録事務所名を抽出"""
        try:
            transport_bureau = ""
            office_name = ""

            # 運輸局（列4）
            if len(row_values) > start_index:
                bureau_value = row_values[start_index].strip()
                if bureau_value and bureau_value != "nan" and not bureau_value.isdigit():
                    transport_bureau = bureau_value

            # 運輸支局（列5）
            if len(row_values) > start_index + 1:
                bureau_value = row_values[start_index + 1].strip()
                if bureau_value and bureau_value != "nan" and not bureau_value.isdigit():
                    if transport_bureau and transport_bureau != bureau_value:
                        transport_bureau = f"{transport_bureau} {bureau_value}"
                    elif not transport_bureau:
                        transport_bureau = bureau_value

            # 自動車検査登録事務所名（列6）
            if len(row_values) > start_index + 2:
                office_value = row_values[start_index + 2].strip()
                if office_value and office_value != "nan" and not office_value.isdigit():
                    office_name = office_value

            return transport_bureau, office_name
        except Exception:
            return "", ""

    def _clean_plate_name(self, text: str) -> str:
        """地名をクリーンアップ"""
        if not text or text == "nan" or text == "NaN":
            return ""

        # *記号や注釈記号を除去
        cleaned = text.replace('*', '').strip()
        cleaned = re.sub(r'\[注\s*\d+\]', '', cleaned).strip()
        return cleaned

    def _is_valid_plate_name(self, text: str) -> bool:
        """有効な地名かどうか判定"""
        if not text or len(text) > 10:
            return False

        # フィルタリング実行
        return not text.isdigit()

    def _is_prefecture(self, text: str) -> bool:
        """都道府県名かどうかを判定"""
        return text in PREFECTURES

    def _generate_reading(self, plate_name: str) -> str:
        """地名の読み仮名を生成（簡易版）"""
        # 注釈記号を除去してから処理
        clean_name = re.sub(r'\[注\s*\d+\]', '', plate_name).strip()

        # カタカナをひらがなに変換
        hiragana_name = clean_name.translate(KATAKANA_TO_HIRAGANA)

        return PLATE_NAME_READINGS.get(clean_name, hiragana_name.lower())

    def get_page_info(self) -> Dict[str, str]:
        """ページの情報を取得（最終更新日時など）"""
        try:
            params = {
                'action': 'query',
                'titles': PAGE_TITLE,
                'format': 'json',
                'prop': 'info|revisions',
                'rvprop': 'timestamp|user',
                'rvlimit': 1
            }

            response = self.session.get(WIKIPEDIA_API_URL, params=params)
            response.raise_for_status()

            data = response.json()

            if 'query' in data and 'pages' in data['query']:
                page_data = list(data['query']['pages'].values())[0]
                if 'revisions' in page_data:
                    revision = page_data['revisions'][0]
                    return {
                        'last_modified': revision.get('timestamp', ''),
                        'last_user': revision.get('user', ''),
                        'page_id': str(page_data.get('pageid', ''))
                    }

            return {}

        except Exception as e:
            print(f"ページ情報取得エラー: {e}")
            return {}


def load_existing_csv() -> pd.DataFrame:
    """既存のCSVファイルを読み込み"""
    if os.path.exists(CSV_FILE_PATH):
        try:
            return pd.read_csv(CSV_FILE_PATH)
        except Exception as e:
            print(f"既存CSVファイルの読み込みエラー: {e}")
            return pd.DataFrame(columns=CSV_COLUMNS)
    else:
        print("既存のCSVファイルが見つかりません。新規作成します。")
        return pd.DataFrame(columns=CSV_COLUMNS)


def compare_data(existing_df: pd.DataFrame, new_data: List[Dict[str, str]]) -> Tuple[bool, List[str]]:
    """データを比較して差分を検出"""
    if new_data:
        new_df = pd.DataFrame(new_data)

        # 既存データと比較
        if existing_df.empty:
            changes = [f"新規作成: {len(new_df)}件のデータを追加"]
            return True, changes

        changes = []

        # 新しい地名の検出（地名+都道府県の組み合わせで比較）
        existing_plates = set(zip(existing_df['地名'], existing_df['都道府県']))
        new_plates = set(zip(new_df['地名'], new_df['都道府県']))

        added_plates = new_plates - existing_plates
        removed_plates = existing_plates - new_plates

        if added_plates:
            changes.append(f"追加された地名: {len(added_plates)}件")
            for plate, pref in added_plates:
                changes.append(f"  + {plate} ({pref})")

        if removed_plates:
            changes.append(f"削除された地名: {len(removed_plates)}件")
            for plate, pref in removed_plates:
                changes.append(f"  - {plate} ({pref})")

        # 変更内容の検出
        common_plates = existing_plates & new_plates
        for plate, pref in common_plates:
            existing_row = existing_df[(existing_df['地名'] == plate) & (existing_df['都道府県'] == pref)]
            new_row = new_df[(new_df['地名'] == plate) & (new_df['都道府県'] == pref)]

            if not existing_row.empty and not new_row.empty:
                existing_record = existing_row.iloc[0]
                new_record = new_row.iloc[0]

                for col in ['運輸支局', '自動車検査登録事務所名', '読み仮名']:
                    if str(existing_record[col]) != str(new_record[col]):
                        changes.append(f"変更: {plate} ({pref}) の{col}: '{existing_record[col]}' → '{new_record[col]}'")

        return len(changes) > 0, changes

    return False, []


def save_updated_csv(new_data: List[Dict[str, str]]):
    """更新されたCSVファイルを保存"""
    if new_data:
        df = pd.DataFrame(new_data)

        # HTMLテーブル順序を保持（重複除去なし）
        df.to_csv(CSV_FILE_PATH, index=False, encoding='utf-8')
        print(f"CSVファイルを更新しました: {CSV_FILE_PATH}")


def save_changes_summary(changes: List[str]):
    """変更内容をファイルに保存"""
    with open(CHANGES_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write('\n'.join(changes))


def set_github_output(key: str, value: str):
    """GitHub Actionsのoutputをセット"""
    if 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
            f.write(f"{key}={value}\n")


def main():
    """メイン処理"""
    fetcher = PlateDataFetcher()

    # 既存データを読み込み
    existing_df = load_existing_csv()

    # Wikipediaから新しいデータを取得
    new_data = fetcher.fetch_wikipedia_data()

    if not new_data:
        print("新しいデータを取得できませんでした。")
        set_github_output('changes', 'false')
        return

    # ページ情報を取得
    page_info = fetcher.get_page_info()

    # データを比較
    has_changes, changes = compare_data(existing_df, new_data)

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S JST')

    # ページ情報をGitHub Actionsに出力
    if page_info:
        set_github_output('wiki-last-modified', page_info.get('last_modified', ''))
        set_github_output('wiki-last-user', page_info.get('last_user', ''))

    if has_changes:
        print("変更が検出されました:")
        for change in changes:
            print(f"  {change}")

        # CSVファイルを更新
        save_updated_csv(new_data)

        # 変更内容を保存
        save_changes_summary(changes)

        # GitHub Actionsに結果を通知
        set_github_output('changes', 'true')
        set_github_output('changes-summary', '\\n'.join(changes))
        set_github_output('fetch-time', current_time)

    else:
        print("変更は検出されませんでした。")
        set_github_output('changes', 'false')
        set_github_output('fetch-time', current_time)


if __name__ == "__main__":
    main()
