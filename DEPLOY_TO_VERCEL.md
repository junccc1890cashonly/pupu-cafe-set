# 部署到 Vercel

下面这套步骤是按“第一次用 Vercel”设计的，尽量简单、稳。

## 你现在已经有的东西

项目目录：

`/Users/junc/Documents/PUPU2026/cutlery-survey`

关键文件：

- `public/index.html`：调研首页
- `public/submissions.html`：查看提交结果
- `api/orders.py`：随机抽 10 个订单
- `api/submissions.py`：提交和读取调研结果
- `data/orders.json`：146 个 `diff >= 5` 的订单题库

## 最推荐的发布方式

推荐你用：

1. GitHub 托管代码
2. Vercel 导入 GitHub 仓库
3. Vercel KV 保存提交结果

这样有几个好处：

- 别人可以直接访问网址
- 你后面改代码后，推送 GitHub 就能自动重新部署
- 用户提交结果能持续保留，不会丢

## 第一步：把项目上传到 GitHub

建议你新建一个 GitHub 仓库，比如：

`cutlery-survey`

然后把这个目录上传上去：

`/Users/junc/Documents/PUPU2026/cutlery-survey`

如果你熟悉 Git，可以直接在这个目录里初始化仓库并推送。

如果你不熟悉 Git，也可以：

1. 打开 GitHub
2. 新建一个空仓库
3. 把 `cutlery-survey` 整个目录拖进去上传

## 第二步：在 Vercel 创建项目

1. 打开 [Vercel](https://vercel.com/)
2. 点击 `Sign Up` 或 `Log In`
3. 直接选择 `Continue with GitHub`
4. 登录后点击 `Add New...`
5. 选择 `Project`
6. 选择你刚才上传的 GitHub 仓库

## 第三步：导入时这样配

导入页面里重点看这几个配置：

- `Framework Preset`：选 `Other`
- `Root Directory`：如果你的仓库根目录就是 `cutlery-survey`，就保持默认
- `Build Command`：留空
- `Output Directory`：留空
- `Install Command`：留空

这个项目是“静态页面 + Python Functions”，不需要前端构建。

根据 Vercel 官方文档：

- Python Functions 放在项目根目录的 `api` 目录即可
- `vercel.json` 可以自定义路由
- 静态项目如果不需要构建，可以选 `Other` 并让 Build Command 为空

## 第四步：先部署一次

点击 `Deploy`。

首次部署成功后，你会拿到一个类似下面的网址：

`https://your-project-name.vercel.app`

你可以先验证两个页面：

- 首页：`https://你的域名.vercel.app/`
- 提交结果页：`https://你的域名.vercel.app/submissions`

## 第五步：给项目加 Vercel KV

为了让“别人提交的结果”在线上长期保存，建议你接上 `Vercel KV`。

操作方法：

1. 进入这个 Vercel 项目
2. 找到 `Storage`
3. 选择 `KV`
4. 创建一个新的 KV 数据库
5. 把这个 KV 连接到当前项目

连接后，Vercel 会把 KV 相关环境变量注入到项目里。这个站点已经优先读取：

- `KV_REST_API_URL`
- `KV_REST_API_TOKEN`

然后你只需要重新部署一次。

## 第六步：重新部署

加完 KV 后，重新部署项目。

因为 Vercel 的环境变量变更只会应用到新的 Deployment，所以要重新发布一次，新的环境变量才会生效。

## 第七步：验证是否正常

你可以这样测试：

1. 打开首页
2. 随机选 10 个订单的答案
3. 点击 `提交`
4. 再打开 `/submissions`
5. 确认能看到刚才的提交结果

如果能看到，说明线上存储已经正常。

## 你最需要记住的两点

1. 没接 `Vercel KV` 时，项目也能跑，但线上提交结果不适合当正式数据源
2. 接好 `Vercel KV` 之后，这个调研站才真正适合给别人公开访问和持续收集数据

## 官方文档

- Vercel Python Functions:
  https://vercel.com/docs/functions/runtimes/python
- vercel.json 配置:
  https://vercel.com/docs/project-configuration/vercel-json
- 静态项目不需要 Build 的说明:
  https://vercel.com/docs/deployments/configure-a-build
- 环境变量:
  https://vercel.com/docs/environment-variables
