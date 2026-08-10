# Snipe-IT 资产领用管理自动化测试方案

## 1. 项目定位

本项目以本地部署的 Snipe-IT v8.6.3 为被测系统，围绕企业测试设备的
建档、查询、领用、归还和历史追踪，建设接口、Web UI 与 MySQL 数据一致性
自动化测试。Snipe-IT 应用本身不是本仓库开发的产品，本仓库负责测试分析、
自动化框架适配、测试数据治理、持续集成和结果报告。

## 2. 第一版范围

### 纳入范围

- Personal Access Token 鉴权
- 用户创建、查询、修改和删除
- 资产分类、制造商、型号、地点等基础数据
- 设备资产创建、查询、筛选、修改和删除
- 设备领用、重复领用、归还和重复归还
- 资产状态、使用人和操作历史校验
- API 响应、Web 页面与 MySQL 最终状态一致性
- 自动创建、唯一命名和清理测试数据

### 暂不纳入

- 许可证、配件、组件和耗材
- LDAP、SCIM、双因素认证和邮件发送
- CSV 批量导入与导出
- 资产盘点、折旧、审计标签打印
- 非 Snipe-IT 使用的数据存储
- 性能、渗透与破坏性测试

## 3. 核心业务流程

```text
创建普通用户
    ↓
创建分类、制造商、型号和地点
    ↓
创建“Ready to Deploy”设备资产
    ↓
将设备领用给用户
    ↓
查询设备和用户的领用关系
    ↓
归还设备并恢复可领用状态
    ↓
校验操作历史并清理测试数据
```

### 业务状态

| 状态标签 | 元状态 | 是否允许领用 | 第一版用途 |
| --- | --- | --- | --- |
| Pending | pending | 否 | 验证不可领用场景 |
| Ready to Deploy | deployable | 是 | 正常领用与归还 |
| Archived | archived | 否 | 验证归档资产不可领用 |
| Deployed | 系统派生状态 | 已领用 | 领用后的查询断言 |

## 4. API 契约与用途

所有 API 请求必须携带以下请求头：

```text
Authorization: Bearer <personal-access-token>
Accept: application/json
Content-Type: application/json
User-Agent: Test-Automation-Framework/0.1
```

Snipe-IT 的部分业务校验失败仍可能返回 HTTP 200，因此断言必须同时检查
HTTP 状态码和 JSON 中的 `status`、`messages`、`payload` 等业务字段。

| 模块 | 方法与路径 | 用途 |
| --- | --- | --- |
| 鉴权 | `GET /api/v1/users/me` | 校验 Token 及当前用户 |
| 用户 | `GET /api/v1/users` | 查询、筛选和分页 |
| 用户 | `POST /api/v1/users` | 创建领用人 |
| 用户 | `GET/PATCH/DELETE /api/v1/users/{id}` | 用户详情、修改和清理 |
| 状态 | `GET /api/v1/statuslabels` | 获取可领用与不可领用状态 |
| 分类 | `POST /api/v1/categories` | 创建资产分类 |
| 制造商 | `POST /api/v1/manufacturers` | 创建制造商 |
| 型号 | `POST /api/v1/models` | 创建关联分类和制造商的设备型号 |
| 地点 | `POST /api/v1/locations` | 创建设备默认地点 |
| 资产 | `GET /api/v1/hardware` | 查询、筛选、排序和分页 |
| 资产 | `POST /api/v1/hardware` | 创建设备资产 |
| 资产 | `GET/PATCH/DELETE /api/v1/hardware/{id}` | 详情、修改和清理 |
| 资产 | `GET /api/v1/hardware/bytag/{tag}` | 按资产标签精确查询 |
| 领用 | `POST /api/v1/hardware/{id}/checkout` | 将设备领用给用户 |
| 归还 | `POST /api/v1/hardware/{id}/checkin` | 归还设备 |
| 历史 | `GET /api/v1/hardware/{id}/history` | 验证领用和归还操作记录 |

## 5. 测试数据策略

- 每轮执行使用 `autotest_<时间戳>_<随机串>` 作为数据前缀。
- 用户名、邮箱、资产标签、序列号、分类和型号名称必须唯一。
- 测试通过 API 创建前置数据，不依赖人工预置业务数据。
- 环境自带的三个状态标签作为只读基础数据，不在用例中删除。
- 清理顺序为：归还资产 → 删除资产 → 删除用户 → 删除型号 → 删除地点 →
  删除制造商 → 删除分类。
- 即使用例失败，也必须在 fixture teardown 中尝试清理已创建的数据。
- 测试账号、数据库密码和 API Token 只从本地 `.env` 或 Jenkins Secret file
  读取，不写入日志、Allure 附件或 Git 仓库。

## 6. 第一版接口测试清单

### 鉴权

| ID | 优先级 | 场景 | 预期 |
| --- | --- | --- | --- |
| AUTH-001 | P0 | 使用有效 Token 查询当前用户 | 返回管理员用户，业务成功 |
| AUTH-002 | P0 | 不携带 Token 请求用户列表 | HTTP 401 |
| AUTH-003 | P1 | 使用无效 Token 请求用户列表 | HTTP 401 |

### 用户管理

| ID | 优先级 | 场景 | 预期 |
| --- | --- | --- | --- |
| USER-001 | P0 | 创建字段完整的普通用户 | 创建成功并返回用户 ID |
| USER-002 | P1 | 缺少名字、用户名或密码 | 返回字段级校验错误 |
| USER-003 | P1 | 两次创建相同用户名 | 第二次失败且不生成重复记录 |
| USER-004 | P0 | 按用户名精确查询 | 只返回目标用户 |
| USER-005 | P1 | 修改用户姓名和职位 | 查询结果与修改值一致 |
| USER-006 | P1 | 查询不存在的用户 ID | 返回明确的业务错误 |
| USER-007 | P1 | 删除未领用资产的测试用户 | 删除成功，列表中不可见 |

### 基础数据与资产

| ID | 优先级 | 场景 | 预期 |
| --- | --- | --- | --- |
| ASSET-001 | P0 | 创建分类、制造商、型号和地点 | 四类依赖数据创建成功 |
| ASSET-002 | P0 | 使用可领用状态创建设备 | 返回资产 ID 和唯一资产标签 |
| ASSET-003 | P1 | 缺少型号或状态创建设备 | 返回字段级校验错误 |
| ASSET-004 | P1 | 使用不存在的型号或状态 | 返回关联数据校验错误 |
| ASSET-005 | P1 | 创建重复资产标签 | 第二次失败且记录数不增加 |
| ASSET-006 | P0 | 按 ID 查询设备详情 | 字段与创建请求一致 |
| ASSET-007 | P0 | 按资产标签查询设备 | 返回唯一目标设备 |
| ASSET-008 | P1 | 使用关键词、状态和型号筛选 | 返回结果满足筛选条件 |
| ASSET-009 | P1 | 修改设备名称和备注 | 查询结果与修改值一致 |
| ASSET-010 | P1 | 删除未领用设备 | 删除成功且活动列表不可见 |

### 领用、归还和一致性

| ID | 优先级 | 场景 | 预期 |
| --- | --- | --- | --- |
| FLOW-001 | P0 | 将可领用设备分配给普通用户 | 设备变为 Deployed 并关联用户 |
| FLOW-002 | P1 | 重复领用同一设备 | 第二次领用失败，原领用关系不变 |
| FLOW-003 | P1 | 领用 Pending 状态设备 | 领用失败且设备保持未分配 |
| FLOW-004 | P1 | 领用给不存在的用户 | 失败且不产生领用记录 |
| FLOW-005 | P0 | 查询用户已领用资产 | 列表包含目标设备 |
| FLOW-006 | P0 | 正常归还已领用设备 | 使用人清空并恢复可领用状态 |
| FLOW-007 | P1 | 重复归还同一设备 | 第二次归还失败且状态不被破坏 |
| FLOW-008 | P1 | 查询设备操作历史 | 包含 checkout 与 checkin 记录 |
| FLOW-009 | P0 | 校验 MySQL 资产领用状态 | `assets.assigned_to`、状态和计数正确 |
| FLOW-010 | P1 | 校验 MySQL 操作日志 | `action_logs` 中领用和归还记录完整 |

第一版共 30 条接口场景，其中 P0 冒烟场景 12 条，P1 回归场景 18 条。

## 7. 后续 Web 与组合场景

接口层稳定后增加以下组合场景：

1. API 创建用户和设备 → Web 页面执行领用 → API 与 MySQL 验证。
2. API 准备已领用设备 → Web 页面执行归还 → API 与 MySQL 验证。
3. Web 页面新增设备 → API 按标签查询 → MySQL 验证字段一致性。
4. Web 页面筛选已领用设备 → API 返回集合与页面结果对比。

## 8. 通过标准

- P0 冒烟用例必须全部通过。
- P1 用例不存在阻断性失败。
- 用例可独立执行且执行顺序不影响结果。
- 连续执行 10 轮后统计稳定性，目标不低于 95%。
- 失败用例的请求、响应、测试步骤和清理结果进入 Allure 报告。
- API Token、密码和数据库连接凭据不得出现在报告或构建日志中。

## 9. 参考资料

- Snipe-IT API Overview: https://snipe-it.readme.io/reference/api-overview
- API Authentication: https://snipe-it.readme.io/reference/authenticating-with-the-api
- Create Asset: https://snipe-it.readme.io/reference/hardware-create
- Asset Checkout: https://snipe-it.readme.io/reference/hardware-checkout
- Asset Checkin: https://snipe-it.readme.io/reference/hardware-checkin
