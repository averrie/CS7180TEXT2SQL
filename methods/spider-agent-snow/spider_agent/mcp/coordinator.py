from typing import Dict, Any, Optional
from spider_agent.agent.agents import PromptAgent
from spider_agent.envs.spider_agent import Spider_Agent_Env
from spider_agent.agent.models import call_llm
from spider_agent.mcp.agents.analyzer import ProblemAnalyzerAgent
from spider_agent.mcp.agents.db_expert import DatabaseExpertAgent
from spider_agent.mcp.agents.sql_generator import SQLGeneratorAgent
from spider_agent.mcp.agents.validator import SQLValidatorAgent
import logging

logger = logging.getLogger(__name__)

class MCPCoordinator:
    def __init__(self, env, model="gpt-4", max_tokens=2500, temperature=0.5):
        self.env = env
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        
        # 初始化专家代理
        self.analyzer = ProblemAnalyzerAgent(model)
        self.db_expert = DatabaseExpertAgent(model)
        self.sql_generator = SQLGeneratorAgent(model)
        self.validator = SQLValidatorAgent(model)
        
        # 原始执行代理
        self.executor = None
        
        # 共享内存
        self.shared_memory = {
            "problem_analysis": None,
            "database_insights": None,
            "sql_strategy": None
        }
        
        # 步骤记录
        self.steps = []
    
    def set_env_and_task(self, env: Spider_Agent_Env):
        self.env = env
        self.executor = PromptAgent(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        self.executor.set_env_and_task(env)
        self.instruction = env.task_config['instruction']
    
    def run(self):
        try:
            # 1. 问题分析
            logger.info("Step 1: Analyzing problem...")
            self.shared_memory["problem_analysis"] = self.analyzer.analyze(self.env.task_config['instruction'])
            self.steps.append({
                "step": "problem_analysis",
                "result": self.shared_memory["problem_analysis"]
            })
            
            # 2. 数据库分析
            logger.info("Step 2: Analyzing database...")
            db_type = self.env.task_config.get('type', 'snowflake')  # 默认使用 snowflake
            entities = self.shared_memory["problem_analysis"].get("entities", ["N/A"])
            relationships = self.shared_memory["problem_analysis"].get("relationships", ["N/A"])
            self.shared_memory["database_insights"] = self.db_expert.analyze_database(
                entities=entities,
                relationships=relationships,
                db_type=db_type
            )
            self.steps.append({
                "step": "database_analysis",
                "result": self.shared_memory["database_insights"]
            })
            
            # 3. SQL策略设计
            logger.info("Step 3: Designing SQL strategy...")
            self.shared_memory["sql_strategy"] = self.sql_generator.design_strategy(
                problem_analysis=self.shared_memory["problem_analysis"],
                db_insights=self.shared_memory["database_insights"],
                db_type=db_type
            )
            self.steps.append({
                "step": "sql_strategy",
                "result": self.shared_memory["sql_strategy"]
            })
            
            # 4. 生成 SQL 查询
            logger.info("Step 4: Generating SQL query...")
            sql_query = self._generate_sql_query()
            self.steps.append({
                "step": "sql_generation",
                "result": sql_query
            })
            
            # 5. 执行 SQL 查询
            logger.info("Step 5: Executing SQL query...")
            result = self._execute_sql_query(sql_query)
            self.steps.append({
                "step": "sql_execution",
                "result": result
            })
            
            # 6. 验证结果
            logger.info("Step 6: Validating results...")
            validation_result = self.validator.validate_result(
                result=result,
                sql_strategy=self.shared_memory["sql_strategy"]
            )
            self.steps.append({
                "step": "validation",
                "result": validation_result
            })
            
            # 7. 如果验证失败，尝试优化查询
            if not validation_result.get("is_valid", False):
                logger.info("Step 7: Optimizing query...")
                sql_query = self._optimize_sql_query(sql_query, validation_result.get("suggestions", []))
                result = self._execute_sql_query(sql_query)
                self.steps.append({
                    "step": "query_optimization",
                    "result": {
                        "optimized_query": sql_query,
                        "final_result": result
                    }
                })
            
            return True, {
                "steps": self.steps,
                "final_result": result
            }
            
        except Exception as e:
            logger.error(f"Error in MCP execution: {str(e)}")
            return False, {
                "error": str(e),
                "steps": self.steps
            }
    
    def _generate_sql_query(self):
        system_prompt = f"""You are a {self.env.task_config.get('type', 'snowflake')} SQL expert. Generate a SQL query based on:
1. Problem analysis: {self.shared_memory['problem_analysis']}
2. Database insights: {self.shared_memory['database_insights']}
3. SQL strategy: {self.shared_memory['sql_strategy']}

Please provide ONLY the SQL query without any explanation."""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": "Generate the SQL query."}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        })
        
        return response.strip()
    
    def _execute_sql_query(self, sql_query):
        # 这里应该调用实际的数据库执行函数
        # 暂时返回模拟结果
        return f"Query executed: {sql_query}\nResult: [Actual query result would be here]"
    
    def _optimize_sql_query(self, sql_query, suggestions):
        system_prompt = f"""You are a {self.env.task_config.get('type', 'snowflake')} SQL optimization expert. 
Optimize the following query based on these suggestions: {suggestions}

Please provide ONLY the optimized SQL query without any explanation."""

        messages = [
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {"role": "user", "content": [{"type": "text", "text": f"Original query: {sql_query}"}]}
        ]
        
        status, response = call_llm({
            "model": self.model,
            "messages": messages,
            "temperature": 0.3
        })
        
        return response.strip()
    
    def _create_enhanced_prompt(self):
        analysis = self.shared_memory["problem_analysis"]
        db_insights = self.shared_memory["database_insights"]
        sql_strategy = self.shared_memory["sql_strategy"]
        
        # 保持原始系统提示
        original_prompt = self.executor.system_message
        
        # 添加专家洞察
        expert_insights = f"""
## Expert Insights

### Problem Analysis
- Query Objective: {analysis.get('query_objective', 'N/A')}
- Main Entities: {', '.join(analysis.get('entities', ['N/A']))}

### Database Structure
- Recommended Tables: {', '.join(db_insights.get('relevant_tables', ['N/A']))}
- Key Fields: {', '.join(db_insights.get('key_fields', ['N/A']))}

### SQL Strategy
- Recommended Query Approach: {sql_strategy.get('approach', 'N/A')}
- Query Steps: {sql_strategy.get('steps_summary', 'N/A')}
"""
        
        # 在动作空间后添加专家洞察
        action_space_start = original_prompt.find("# ACTION SPACE #")
        action_space_end = original_prompt.find("#", action_space_start + 1)
        
        return (
            original_prompt[:action_space_end] +
            expert_insights +
            original_prompt[action_space_end:]
        )
