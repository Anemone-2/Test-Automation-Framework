# Snipe-IT 自动化测试用例清单

## 1. 文档说明

本文档依据当前仓库 `testcase/snipeit` 下的自动化测试代码整理，覆盖 Jenkins 第 16 次全量构建中实际执行的 38 个测试实例。

- 被测系统：Snipe-IT 企业 IT 资产管理系统
- 测试层次：REST API、Web UI、API 与 Web 组合、API 与 MySQL 数据一致性
- 自动化框架：Python、Pytest、Requests、Selenium、MySQL Connector/Python、Allure
- 最近一次全量结果：`38 passed in 35.98s`
- Jenkins 构建：`#16 SUCCESS`
- 流水线总耗时：80.41 秒

### 1.1 编号规则

| 示例 | 含义 |
|---|---|
| `AUTH-001` | 稳定的业务测试用例编号，对应鉴权模块第 1 条规则 |
| `USER-002-01` | `USER-002` 参数化用例的第 1 个执行实例 |
| Allure `#1` | 当前报告分组中的显示顺序，不是固定用例编号 |
| Jenkins `#16` | Jenkins 任务的第 16 次流水线构建 |

参数化用例在代码中共享一个业务编号，但会由 Pytest 按不同数据生成多个独立测试实例。本文档增加 `-01`、`-02` 等实例后缀，以便与 38 次实际执行一一对应。

### 1.2 优先级规则

| 标记 | 说明 |
|---|---|
| `smoke` | 核心冒烟场景，用于快速验证主要功能和环境可用性，共 16 条 |
| `regression` | 完整回归场景，覆盖边界、异常和补充业务规则，共 22 条 |

## 2. 公共前置条件

1. Docker Desktop 正常运行。
2. Snipe-IT 与 MySQL 容器已经启动并通过健康检查。
3. Snipe-IT 地址为 `http://localhost:8090`。
4. 系统已完成初始化，并存在管理员账号、API Token 及必要状态标签。
5. `Ready to Deploy` 状态类型为 `deployable`，`Pending` 状态类型为 `pending`。
6. Web 测试使用 Edge 或 Chrome；Jenkins 默认采用 Edge 无头模式。
7. 测试数据名称使用 `autotest_<类型>_<随机值>` 动态生成，避免并发或重复执行时冲突。
8. API 请求和响应自动附加到 Allure，Token、密码、Cookie 等敏感信息会被脱敏。
9. 每条用例结束后，Fixture 按依赖关系的反向顺序清理用户、资产、型号、位置、厂商和分类。
10. 如果资产仍处于领用状态，先执行归还，再删除资产及其依赖数据。

## 3. 用例数量汇总

| 模块 | 前缀 | 测试实例数 | 冒烟 | 回归 |
|---|---:|---:|---:|---:|
| API 接口鉴权 | AUTH | 3 | 2 | 1 |
| 用户管理 | USER | 9 | 2 | 7 |
| 资产基础数据与硬件资产 | ASSET | 12 | 4 | 8 |
| 资产领用、归还与数据库一致性 | FLOW | 10 | 4 | 6 |
| Web 与跨层组合场景 | WEB | 4 | 4 | 0 |
| **合计** |  | **38** | **16** | **22** |

## 4. API 接口鉴权

### 模块前置

- 已配置有效的管理员 API Token。
- 系统存在与环境配置一致的管理员用户名和邮箱。

| 实例编号 | 优先级 | 用例名称 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| AUTH-001 | smoke | 有效 Token 可以查询当前管理员 | 1. 携带有效 Bearer Token 请求 `GET /api/v1/users/me`。<br>2. 读取当前用户信息。 | HTTP 200；用户名、邮箱与环境配置一致；`activated=true`。 |
| AUTH-002 | smoke | 缺少 Token 访问用户列表时被拒绝 | 1. 创建不携带 Authorization 头的客户端。<br>2. 请求 `GET /api/v1/users?limit=1`。 | HTTP 401；响应类型为 JSON；不返回用户列表。 |
| AUTH-003 | regression | 无效 Token 访问用户列表时被拒绝 | 1. 使用固定无效 Token 创建客户端。<br>2. 请求 `GET /api/v1/users?limit=1`。 | HTTP 401；响应类型为 JSON；无效 Token 不能访问受保护资源。 |

## 5. 用户管理

### 模块前置

- 使用唯一用户名和邮箱构造已启用员工账号。
- 标准用户数据包含姓名、用户名、邮箱、密码、确认密码、启用状态和职位。

| 实例编号 | 原业务编号 | 优先级 | 用例名称 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| USER-001 | USER-001 | smoke | 创建可领用资产的已启用用户 | 1. 调用 `POST /api/v1/users` 创建员工。<br>2. 调用 `GET /api/v1/users/{id}` 查询详情。 | 创建成功并返回用户 ID；用户名、姓名、邮箱一致；用户处于启用状态。 |
| USER-002-01 | USER-002 | regression | 缺少姓名时拒绝创建用户 | 1. 从标准用户数据中删除 `first_name`。<br>2. 调用创建用户接口。 | HTTP 200 但业务状态为 `error`；`messages` 包含 `first_name`；没有产生有效用户。 |
| USER-002-02 | USER-002 | regression | 缺少用户名时拒绝创建用户 | 1. 从标准用户数据中删除 `username`。<br>2. 调用创建用户接口。 | HTTP 200 但业务状态为 `error`；`messages` 包含 `username`；没有产生有效用户。 |
| USER-002-03 | USER-002 | regression | 缺少密码时拒绝创建用户 | 1. 删除 `password` 和 `password_confirmation`。<br>2. 调用创建用户接口。 | HTTP 200 但业务状态为 `error`；`messages` 包含 `password`；没有产生有效用户。 |
| USER-003 | USER-003 | regression | 重复用户名时拒绝创建用户 | 1. 创建一个用户。<br>2. 使用相同用户名、不同邮箱再次创建。<br>3. 按用户名查询用户列表。 | 第二次创建返回业务错误；错误字段包含 `username`；系统中该用户名精确匹配记录只有 1 条。 |
| USER-004 | USER-004 | smoke | 按用户名精确查询用户 | 1. 创建唯一用户。<br>2. 调用 `GET /api/v1/users` 并通过 `search` 查询用户名。<br>3. 对结果进行精确匹配。 | HTTP 200；精确匹配记录只有 1 条；返回 ID 与创建结果一致。 |
| USER-005 | USER-005 | regression | 修改用户姓名和职位 | 1. 创建用户。<br>2. 调用 `PATCH /api/v1/users/{id}` 修改姓名与职位。<br>3. 重新查询用户详情。 | 修改接口业务状态为 `success`；姓名和 `jobtitle` 均更新为目标值。 |
| USER-006 | USER-006 | regression | 查询不存在的用户时返回业务错误 | 1. 请求不存在的用户 ID `999999999`。<br>2. 检查业务响应。 | HTTP 200；业务状态为 `error`；`payload=null`；错误消息为非空字符串。 |
| USER-007 | USER-007 | regression | 删除未领用资产的用户 | 1. 创建未关联资产的用户。<br>2. 调用删除用户接口。<br>3. 按 ID 和用户名再次查询。 | 删除成功；详情接口返回业务错误；用户列表中不存在该用户名。 |

## 6. 资产基础数据与硬件资产管理

### 模块前置

- 创建硬件资产前动态准备分类、厂商、位置和资产型号。
- 使用系统中类型为 `deployable` 的状态作为可领用状态。
- 资产标签和序列号均动态生成且保持唯一。

| 实例编号 | 原业务编号 | 优先级 | 用例名称 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| ASSET-001 | ASSET-001 | smoke | 创建资产所需的分类、厂商、位置和型号 | 1. 查询并校验 Pending、Ready to Deploy、Archived 状态。<br>2. 创建资产分类。<br>3. 创建厂商和位置。<br>4. 创建并关联分类、厂商的资产型号。 | 状态类型正确；四类基础数据均创建成功；型号返回的分类 ID 和厂商 ID 与请求一致。 |
| ASSET-002 | ASSET-002 | smoke | 创建可领用状态的硬件资产 | 1. 准备基础数据。<br>2. 调用 `POST /api/v1/hardware` 创建资产。<br>3. 按资产 ID 查询详情。 | 创建成功；资产标签、序列号、型号 ID 和状态 ID 与请求一致。 |
| ASSET-003-01 | ASSET-003 | regression | 缺少资产型号时拒绝创建资产 | 1. 构造资产请求。<br>2. 删除 `model_id`。<br>3. 调用创建资产接口。 | HTTP 200 但业务状态为 `error`；错误字段包含 `model_id`。 |
| ASSET-003-02 | ASSET-003 | regression | 缺少资产状态时拒绝创建资产 | 1. 构造资产请求。<br>2. 删除 `status_id`。<br>3. 调用创建资产接口。 | HTTP 200 但业务状态为 `error`；错误字段包含 `status_id`。 |
| ASSET-004-01 | ASSET-004 | regression | 型号不存在时拒绝创建资产 | 1. 构造合法资产请求。<br>2. 将 `model_id` 替换为 `999999999`。<br>3. 调用创建接口。 | 业务状态为 `error`；错误字段包含 `model_id`；无有效资产产生。 |
| ASSET-004-02 | ASSET-004 | regression | 状态不存在时拒绝创建资产 | 1. 构造合法资产请求。<br>2. 将 `status_id` 替换为 `999999999`。<br>3. 调用创建接口。 | 业务状态为 `error`；错误字段包含 `status_id`；无有效资产产生。 |
| ASSET-005 | ASSET-005 | regression | 重复资产标签时拒绝创建资产 | 1. 创建一个硬件资产。<br>2. 使用相同 `asset_tag` 和不同序列号再次创建。<br>3. 按标签查询资产列表。 | 第二次创建返回业务错误；错误字段包含 `asset_tag`；系统中该标签精确匹配资产只有 1 条。 |
| ASSET-006 | ASSET-006 | smoke | 按资产 ID 查询设备详情 | 1. 创建资产。<br>2. 请求 `GET /api/v1/hardware/{id}`。 | HTTP 200；ID、资产标签、名称和备注与创建请求一致。 |
| ASSET-007 | ASSET-007 | smoke | 按唯一资产标签查询设备 | 1. 创建资产。<br>2. 请求 `GET /api/v1/hardware/bytag/{asset_tag}`。 | HTTP 200；返回 ID 和资产标签与创建结果一致。 |
| ASSET-008 | ASSET-008 | regression | 按关键字、状态和型号组合筛选资产 | 1. 创建目标资产。<br>2. 使用 `search`、`status_id`、`model_id` 组合查询。<br>3. 对标签进行精确匹配。 | 精确匹配结果只有 1 条；资产 ID、状态 ID 和型号 ID 全部正确。 |
| ASSET-009 | ASSET-009 | regression | 修改资产名称和备注 | 1. 创建资产。<br>2. 调用 `PATCH /api/v1/hardware/{id}` 修改名称和备注。<br>3. 再次查询详情。 | 修改业务状态为 `success`；资产名称和备注均为更新值。 |
| ASSET-010 | ASSET-010 | regression | 删除未领用的硬件资产 | 1. 创建未领用资产。<br>2. 删除该资产。<br>3. 按资产标签查询列表。 | 删除成功；查询结果中不再存在该资产标签。 |

## 7. 资产领用、归还与数据一致性

### 模块前置

- 动态创建一个已启用员工。
- 动态创建分类、厂商、位置、型号和硬件资产。
- 正常场景使用 `Ready to Deploy` 状态；禁领用场景使用 `Pending` 状态。
- 领用接口：`POST /api/v1/hardware/{id}/checkout`。
- 归还接口：`POST /api/v1/hardware/{id}/checkin`。

| 实例编号 | 优先级 | 用例名称 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| FLOW-001 | smoke | 将可领用设备分配给用户 | 1. 创建可领用资产。<br>2. 将资产领用给测试用户。<br>3. 查询资产详情。 | 领用业务状态为 `success`；`assigned_to.id` 为目标用户 ID；分配类型为 `user`。 |
| FLOW-002 | regression | 拒绝重复领用同一设备 | 1. 首次领用资产并确认成功。<br>2. 对同一资产再次执行领用。<br>3. 查询资产详情。 | 第二次领用返回业务错误；资产仍只分配给第一次的用户。 |
| FLOW-003 | regression | Pending 状态设备禁止领用 | 1. 创建 Pending 状态资产。<br>2. 尝试领用给用户。<br>3. 查询资产详情。 | 领用返回业务错误；`assigned_to` 仍为 `null`。 |
| FLOW-004 | regression | 不存在的用户不能领用设备 | 1. 创建可领用资产。<br>2. 将目标用户 ID 设置为 `999999999`。<br>3. 执行领用并查询资产。 | 领用返回业务错误；资产未分配给任何用户。 |
| FLOW-005 | smoke | 查询用户已领用的资产 | 1. 创建并领用资产。<br>2. 请求 `GET /api/v1/users/{user_id}/assets`。<br>3. 按资产标签精确匹配。 | HTTP 200；匹配结果只有 1 条；资产 ID 与领用资产一致。 |
| FLOW-006 | smoke | 正常归还已领用设备 | 1. 创建并领用资产。<br>2. 调用归还接口。<br>3. 查询资产详情。 | 归还业务状态为 `success`；`assigned_to=null`；资产恢复为可领用状态。 |
| FLOW-007 | regression | 拒绝重复归还同一设备 | 1. 创建并领用资产。<br>2. 第一次归还并确认成功。<br>3. 再次归还并查询资产。 | 第二次归还返回业务错误；资产保持未分配状态。 |
| FLOW-008 | regression | 操作历史包含领用和归还记录 | 1. 创建资产。<br>2. 执行领用和归还。<br>3. 查询 `GET /api/v1/hardware/{id}/history`。 | 历史中同时存在领用和归还备注；目标用户和类型正确；操作来源为 `api`。 |
| FLOW-009 | smoke | MySQL 资产领用状态与 API 一致 | 1. 创建并领用资产。<br>2. 查询资产 API。<br>3. 查询 MySQL `assets` 表。<br>4. 对比两个数据源。 | 资产标签一致；`assigned_to` 为用户 ID；`assigned_type` 为用户模型；状态 ID 正确；领用计数为 1；未被软删除；API 与数据库用户 ID 一致。 |
| FLOW-010 | regression | MySQL 包含完整的领用和归还审计日志 | 1. 创建资产。<br>2. 执行领用和归还。<br>3. 查询 MySQL `action_logs` 表。 | 日志包含 `checkout` 和 `checkin from`；领用日志目标类型为用户模型；目标 ID 为测试用户 ID。 |

## 8. Web UI 与跨层组合场景

### 模块前置

- 管理员 Web 账号可以登录。
- Selenium 浏览器驱动可用。
- 页面加载超时和浏览器类型从 `.env` 中读取。
- 除 WEB-001 外，其他用例通过登录 Fixture 自动完成管理员登录。
- Web 用例失败时自动附加页面截图和 HTML 源码到 Allure。

| 实例编号 | 优先级 | 用例名称 | 测试步骤 | 预期结果 |
|---|---|---|---|---|
| WEB-001 | smoke | 管理员登录后可以打开资产列表 | 1. 打开 Snipe-IT 登录页。<br>2. 输入管理员用户名和密码。<br>3. 登录后打开资产列表。 | 登录成功；资产列表标题正确；页面搜索功能可用。 |
| WEB-002 | smoke | API 创建资产后可在 Web 列表和详情中查询 | 1. 通过 API 创建分类、厂商、位置、型号和资产。<br>2. 在 Web 资产列表按资产标签搜索。<br>3. 打开资产详情。 | 列表包含资产标签和序列号；详情包含资产标签、名称和序列号；API 与 Web 展示一致。 |
| WEB-003 | smoke | API 创建用户后可在 Web 列表和详情中查询 | 1. 通过 API 创建已启用员工。<br>2. 在 Web 用户列表按用户名搜索。<br>3. 打开用户详情。 | 列表包含用户名和邮箱；详情包含姓名、用户名和邮箱；API 与 Web 展示一致。 |
| WEB-004 | smoke | 资产领用与归还状态在 API、Web 和 MySQL 中一致 | 1. 通过 API 创建资产并领用给员工。<br>2. 查询 MySQL 领用关系。<br>3. 在 Web 详情验证领用员工和归还入口。<br>4. 通过 API 归还资产。<br>5. 校验 API、MySQL 和刷新后的 Web 页面。 | 领用后数据库用户关系正确，Web 显示领用员工且提供归还入口；归还后 API 和数据库分配字段为空，Web 重新显示领用入口。 |

## 9. 测试证据与报告内容

每个测试实例在 Allure 中至少可以查看以下内容：

1. 固定业务编号和中文用例标题。
2. `snipeit`、`api`、`web`、`smoke` 或 `regression` 标签。
3. 接口请求方法、地址、请求参数和脱敏后的请求体。
4. HTTP 状态码和脱敏后的响应体。
5. MySQL 一致性用例使用的 SQL、查询参数和查询结果。
6. 测试数据创建与清理结果。
7. Web 测试的业务步骤；失败时包含截图和页面源码。
8. 用例执行时间、失败堆栈、历史结果和重试记录。

## 10. 执行命令

### 完整回归（38条）

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\testcase\snipeit -m "snipeit"
```

### 核心冒烟（16条）

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\testcase\snipeit -m "snipeit and smoke"
```

### 仅执行 API

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\testcase\snipeit -m "snipeit and api"
```

### 仅执行 Web

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\testcase\snipeit -m "snipeit and web"
```

### 生成 Allure 和 JUnit 结果

```powershell
.\.venv\Scripts\python.exe -m pytest -q .\testcase\snipeit -m "snipeit" `
  --alluredir=.\report\temp --clean-alluredir `
  --junitxml=.\report\junit.xml
```

## 11. 最近一次验证结果

```text
Jenkins 任务：Test-Automation-Framework
构建编号：#16
构建参数：TEST_SCOPE=all, BROWSER=edge, HEADLESS=true
构建结果：SUCCESS
测试结果：38 passed, 0 failed, 0 skipped
测试耗时：35.98 秒
流水线总耗时：80.41 秒
Allure 报告：发布成功
JUnit 报告：发布成功
```
