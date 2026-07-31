# packages/ax_dataflows

A 股 / 国内数据 adapter（**AX 内实现**）。

## 能力

| 模块 | 说明 |
|------|------|
| `symbols.py` | `.SS`/`.SZ`/6 位代码识别 + EM / 腾讯交易所前缀 |
| `inject.py` | 对 A 股自动设置 `data_vendors`: `akshare,yfinance` |
| `vendors/stock.py` | `get_stock_data`：腾讯 `stock_zh_a_hist_tx` 优先，东财 `stock_zh_a_hist` 回退 (qfq) |
| `vendors/indicators.py` | `get_indicators` via 同上 OHLCV + stockstats |
| `vendors/fundamentals.py` | `get_fundamentals` / 三表 via 东方财富 + 新浪摘要 |
| `vendors/news.py` | `get_news` 个股新闻 + `get_global_news` 新闻联播宏观 |
| `register.py` | 注册到 ai_server `VENDOR_METHODS` |

## 安装

```bash
pip install -e ".[cn,dev]"
```

## 验证

```bash
pytest tests/test_ax_dataflows.py -q
python scripts/smoke_a_share.py --ticker 600519.SS --no-save
python scripts/smoke_a_share.py --ticker 600519.SS --analysts news,fundamentals --no-save
```

Worker/API 经 `ax_engine.build_config` 自动注入，无需手动改 config。
