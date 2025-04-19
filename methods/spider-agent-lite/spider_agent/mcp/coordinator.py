from typing import Dict, Any, Optional
from spider_agent.agent.agents import PromptAgent
from spider_agent.envs.spider_agent import Spider_Agent_Env
from spider_agent.agent.models import call_llm
from .agents.analyzer import ProblemAnalyzerAgent
from .agents.db_expert import DatabaseExpertAgent
from .agents.sql_generator import SQLGeneratorAgent
from .agents.validator import SQLValidatorAgent

class MCPCoordinator:
    def __init__(self, model="gpt-4", max_tokens=2500, temperature=0.5):
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
            "problem_analysis": {},
            "db_insights": {},
            "sql_strategy": {}
        }
    
    def set_env_and_task(self, env: Spider_Agent_Env):
        self.env = env
        self.executor = PromptAgent(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        self.executor.set_env_and_task(env)
        self.instruction = env.task_config['question']
    
    def run(self):
        # 1. 问题分析
        analysis_result = self.analyzer.analyze(self.instruction)
        self.shared_memory["problem_analysis"] = analysis_result
        
        # 2. 数据库分析
        db_type = self.env.task_config['type']
        db_insights = self.db_expert.analyze_database(
            analysis_result["entities"],
            analysis_result["relationships"],
            db_type
        )
        self.shared_memory["db_insights"] = db_insights
        
        # 3. SQL策略设计
        sql_strategy = self.sql_generator.design_strategy(
            analysis_result,
            db_insights,
            db_type
        )
        self.shared_memory["sql_strategy"] = sql_strategy
        
        # 4. 执行准备
        enhanced_prompt = self._create_enhanced_prompt()
        self.executor.system_message = enhanced_prompt
        
        # 5. 执行任务
        done, result = self.executor.run()
        
        # 6. 验证结果
        if done and isinstance(result, str) and len(result) > 0:
            self.validator.validate_result(result, sql_strategy)
        
        return done, result
    
    def _create_enhanced_prompt(self):
        analysis = self.shared_memory["problem_analysis"]
        db_insights = self.shared_memory["db_insights"]
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
