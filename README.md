# Cutlery Survey

这是一个可部署到 Vercel 的调研小站，用来抽样展示 `diff >= 5` 的订单，并让用户选择“这个订单合理需要多少个中式餐具包”。

## 功能

- 随机展示 10 个订单
- 展示每个订单的商品明细：`商品名称 + 商品数量 + 三级财务类别`
- 为每个订单提供 6 个选项：
  - 仿真中式餐具包数量
  - 仿真中式餐具包数量 + 1
  - 仿真中式餐具包数量 + 2
  - 仿真中式餐具包数量 + 3
  - 仿真中式餐具包数量 + 4
  - 仿真中式餐具包数量 + 5
- 提交 10 个订单的选择结果
- 刷新重新抽取 10 个订单
- 在 `/submissions.html` 查看所有已提交结果

## 目录

- `public/index.html`：调研主页面
- `public/submissions.html`：查看提交结果
- `api/orders.py`：随机返回 10 个订单
- `api/submissions.py`：提交和查看结果
- `scripts/build_dataset.py`：从原始 `v4` 数据生成题库
- `data/orders.json`：146 个 `diff >= 5` 订单题库

## 存储方式

- 默认优先使用 `Vercel KV`
- 如果没有配置 KV，则回退到本地 `SQLite`

### 推荐的 Vercel 线上配置

为了让“其他人也可以访问并提交，且你能持续看到提交结果”，建议在 Vercel 项目里加上 `Vercel KV`，并配置：

- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`

没有 KV 时，站点仍然可以运行，但线上提交结果可能不会长期持久保存。

## 重建题库

如果你更新了规则或数据源，可以在本地运行：

```bash
python3 /Users/junc/Documents/PUPU2026/cutlery-survey/scripts/build_dataset.py
```
