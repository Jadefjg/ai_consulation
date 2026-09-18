# 患者端（微信小程序 + H5）

与现有 PC 三角色 Web（`client/`）并行，**只服务患者**。医生 / 管理员继续用电脑端。

当前已覆盖：登录、首页、AI 问诊（含转人工）、资讯、公告、预约挂号、在线咨询、健康档案、健康管理（随访 / 慢病指标 / 风险评估）、个人资料。症状图谱推理仍依赖 Neo4j，暂留在电脑端。医生创建随访计划仍在电脑端「随访管理」。

## 本地调试

后端先按仓库原方式启动（默认 `http://127.0.0.1:8000`）。

```bash
cd mobile
npm install

# H5：http://localhost:5174  （代理到后端 /api）
npm run dev:h5

# 微信小程序：用微信开发者工具导入 **mobile/dist/build/mp-weixin**（或 `npm run dev:mp-weixin` 后的 `mobile/dist/dev/mp-weixin`）
# 必须在开发者工具右上角扫码登录，并使用与 manifest 中相同的 AppID，否则会一直停在「游客模式」
# 开发阶段勾选「不校验合法域名」
npm run dev:mp-weixin
```

H5 用已有患者账号密码登录。小程序走 `wx.login` → `POST /api/v1/auth/wechat`，也可用同一套账号密码。未配置 AppID 时，后端开发环境可用 `dev_<openid>` 模拟登录。

微信开发者工具本地联调可在 `mobile/.env.local` 写入：

```
VITE_API_BASE=http://192.168.x.x:8000/api/v1
```

## 生产构建

```bash
npm run build:h5          # 产物 dist/build/h5 ，拷到 Nginx html-h5，访问 /h5/
npm run build:mp-weixin   # 产物 dist/build/mp-weixin ，上传微信后台
```

生产必须配置 `WECHAT_MINI_APPID` / `WECHAT_MINI_SECRET`，并设 `WECHAT_DEV_LOGIN=false`。request 合法域名为 `https://www.wfrz.fun`。正式上架步骤见仓库根目录 [微信小程序上架指南.md](../微信小程序上架指南.md)。
