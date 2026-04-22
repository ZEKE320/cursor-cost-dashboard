# Cursor Cost Dashboard

Cursor の利用コスト CSV を再利用しやすい形で可視化するための小さなプロジェクトです。

## できること

- `cost-raster`: コスト帯を段階別に色分けしたラスタープロット
- `model-budget-raster`: 使用モデルと Max Mode の組み合わせで色分けしたラスタープロット
- `total-tokens-raster`: `Total Tokens` を連続値として色付けしたラスタープロット
- `cost-tokens-scatter`: `Total Tokens` と `Cost` の散布図。モデルごとの傾向線と高負荷帯の代表点を重ね表示
- `all`: 上記をまとめて生成

## 使い方

```bash
uv run cursor-cost-dashboard --csv /path/to/team-usage-events.csv --plot all
```

出力先を変える場合:

```bash
uv run cursor-cost-dashboard --csv /path/to/team-usage-events.csv --output-dir outputs/custom --plot cost-tokens-scatter
```

## プロジェクト構成

- `src/cursor_cost_dashboard/config.py`: 既定パスと時刻設定
- `src/cursor_cost_dashboard/data.py`: CSV 読み込みと前処理
- `src/cursor_cost_dashboard/palettes.py`: モデル色とカテゴリ色
- `src/cursor_cost_dashboard/plots.py`: 各プロット関数
- `src/cursor_cost_dashboard/cli.py`: `uv run` 用の実行入口

## 補足

- 時刻は `JST` に揃えて描画します
- `cost-raster` では `0` と欠損を同一扱いにしています
- モデル提供者はモデル名の接頭辞から判別できるものだけを明示し、曖昧なものは `Unspecified` としています
