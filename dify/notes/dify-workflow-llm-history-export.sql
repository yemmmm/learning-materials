/*
 * Dify Workflow 历史 LLM 数据导出
 *
 * 适用环境：
 * - Dify Enterprise 3.9.5
 * - PostgreSQL
 * - DBeaver
 *
 * 目标数据：
 * 1. 工作流原始输入：workflow_runs.inputs
 * 2. LLM 实际输入：workflow_node_executions.process_data.prompts
 * 3. LLM 节点输出：workflow_node_executions.outputs
 *
 * 使用方法：
 * 1. 先执行步骤一找到目标 APP_ID。
 * 2. 将后续 SQL 中的 YOUR_APP_ID 替换为实际 APP_ID。
 * 3. 执行步骤三检查 offload；若返回 process_data 或 outputs，
 *    数据库字段可能是截断值，不能只靠 DBeaver 完整导出。
 * 4. 执行步骤四，在结果表格右键选择 Export Data -> JSON。
 * 5. JSON 导出选项中将 “Export JSON values as” 设置为 “JSON”。
 */


-- =====================================================================
-- 步骤一：查找目标应用 ID
-- =====================================================================

SELECT
    id,
    name,
    mode,
    created_at
FROM apps
WHERE name ILIKE '%YOUR_WORKFLOW_NAME%'
ORDER BY created_at DESC;


-- =====================================================================
-- 步骤二：查看应用中的 LLM 节点及历史执行数量
-- =====================================================================

SELECT
    ne.node_id,
    ne.title,
    COUNT(*) AS execution_count,
    MIN(ne.created_at) AS first_execution_at,
    MAX(ne.created_at) AS last_execution_at
FROM workflow_node_executions AS ne
WHERE ne.app_id = 'YOUR_APP_ID'
  AND ne.node_type = 'llm'
  AND ne.triggered_from = 'workflow-run'
GROUP BY ne.node_id, ne.title
ORDER BY ne.title;


-- =====================================================================
-- 步骤三：检查是否存在 offload 大字段
--
-- 返回 0 行：
--   可以直接执行步骤四。
--
-- 返回 process_data 或 outputs：
--   相应完整内容位于 Dify 文件存储中，数据库字段可能只是截断版本，
--   需要通过 Dify repository/storage 还原后再导出。
-- =====================================================================

SELECT
    offload.type,
    COUNT(*) AS record_count
FROM workflow_node_execution_offload AS offload
JOIN workflow_node_executions AS ne
  ON ne.id = offload.node_execution_id
WHERE ne.app_id = 'YOUR_APP_ID'
GROUP BY offload.type
ORDER BY offload.type;


-- =====================================================================
-- 步骤四：导出生产运行中成功执行的 LLM 节点数据
--
-- 一行代表一个 LLM 节点执行。
-- 同一次工作流运行包含多个 LLM 节点时，会产生多行。
-- =====================================================================

SELECT
    wr.id AS workflow_run_id,
    wr.workflow_id,
    wr.version AS workflow_version,
    wr.created_at AS workflow_created_at,
    wr.finished_at AS workflow_finished_at,

    COALESCE(NULLIF(wr.inputs, ''), '{}')::jsonb
        AS raw_workflow_inputs,

    ne.id AS node_execution_id,
    ne.node_id,
    ne.title AS node_title,
    ne."index" AS node_execution_index,
    ne.created_at AS node_created_at,
    ne.finished_at AS node_finished_at,

    COALESCE(NULLIF(ne.process_data, ''), '{}')::jsonb -> 'prompts'
        AS llm_prompt_messages,

    COALESCE(NULLIF(ne.outputs, ''), '{}')::jsonb
        AS llm_outputs,

    COALESCE(NULLIF(ne.outputs, ''), '{}')::jsonb ->> 'text'
        AS llm_output_text,

    COALESCE(NULLIF(ne.process_data, ''), '{}')::jsonb ->> 'model_provider'
        AS model_provider,

    COALESCE(NULLIF(ne.process_data, ''), '{}')::jsonb ->> 'model_name'
        AS model_name,

    COALESCE(NULLIF(ne.execution_metadata, ''), '{}')::jsonb
        AS execution_metadata

FROM workflow_runs AS wr
JOIN workflow_node_executions AS ne
  ON ne.workflow_run_id = wr.id

WHERE wr.app_id = 'YOUR_APP_ID'
  AND wr.triggered_from = 'app-run'
  AND wr.status = 'succeeded'
  AND ne.triggered_from = 'workflow-run'
  AND ne.node_type = 'llm'
  AND ne.status = 'succeeded'

-- 只导出指定 LLM 节点时，取消下一行注释并填写步骤二查到的 node_id。
-- AND ne.node_id = 'YOUR_NODE_ID'

-- 限定时间范围时，可取消下面两行注释。
-- AND wr.created_at >= TIMESTAMP '2026-01-01 00:00:00'
-- AND wr.created_at <  TIMESTAMP '2027-01-01 00:00:00'

ORDER BY wr.created_at, wr.id, ne."index";


-- =====================================================================
-- 可选：同时导出调试运行
--
-- 如需同时包含画布调试数据，从步骤四 WHERE 条件中删除：
--   AND wr.triggered_from = 'app-run'
-- =====================================================================
