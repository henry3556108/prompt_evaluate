from claude import ClaudeAPI
import json
import os
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class PromptManager:
    def __init__(self, prompt_file: str):
        """初始化 Prompt 管理器"""
        with open(prompt_file, 'r', encoding='utf-8') as f:
            self.prompts = json.load(f)
    
    def get_system_prompt(self, category: str, prompt_type: str = None, style: str = "comprehensive") -> str:
        """
        獲取系統提示詞
        :param category: 提示詞類別 (如 content_generation)
        :param prompt_type: 提示詞類型 (如 enrich_task)
        :param style: 提示詞風格 (comprehensive 或 concise)
        """
        if category == "content_generation":
            return self.prompts[category]["system_prompts"][prompt_type][style]
        return self.prompts[category]["system_prompt"]
    
    def get_user_prompt(self, category: str, template_name: str, **kwargs) -> str:
        """
        獲取使用者提示詞
        :param category: 提示詞類別
        :param template_name: 模板名稱
        :param kwargs: 模板參數
        """
        template = self.prompts[category]["user_prompt_templates"][template_name]["template"]
        return template.format(**kwargs)

class ContentEvaluator:
    def __init__(self, prompt_manager: PromptManager):
        """初始化 API clients"""
        self.claude = ClaudeAPI()
        self.openai = OpenAI(api_key=os.getenv("chatgpt_api_key"))
        self.prompt_manager = prompt_manager
        
    def generate_content(self, data: Dict[str, Any], prompt_type: str = "enrich_task", style: str = "comprehensive") -> str:
        """
        使用 Claude 生成內容
        :param data: 輸入數據
        :param prompt_type: 使用的提示詞類型
        :param style: 提示詞風格 (comprehensive 或 concise)
        """
        system_prompt = self.prompt_manager.get_system_prompt("content_generation", prompt_type, style)
        
        # 處理父任務/Epic 資訊
        parent_info = ""
        if "parent" in data:
            parent_info = f"""Parent/Epic:
Title: {data['parent']['title']}
Description: {data['parent']['description']}"""
        else:
            parent_info = "No parent or epic information available."
        
        user_prompt = self.prompt_manager.get_user_prompt(
            "content_generation",
            "enrich_task",
            task_title=data["title"],
            task_description=data["description"],
            parent_info=parent_info
        )
        
        return self.claude.get_completion(system_prompt, user_prompt)
    
    def evaluate_content(self, content: str, original_task: str = None) -> Dict[str, Any]:
        """評估生成的內容"""
        try:
            # 格式化原始任務資訊
            original_task_str = original_task if original_task else "無原始任務描述"
            
            user_prompt = self.prompt_manager.get_user_prompt(
                "content_evaluation",
                "evaluate_content",
                prd_content=content,
                original_task=original_task_str
            )
            
            response = self.openai.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": self.prompt_manager.get_system_prompt("content_evaluation")},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000,
                temperature=0  # 設定為 0 以獲得更確定性的輸出
            )
            
            try:
                result = response.choices[0].message.content
                return json.loads(result)
            except json.JSONDecodeError as e:
                print(f"JSON 解析錯誤: {e}")
                print(f"原始回應: {result[:200]}...")  # 只顯示前200個字符
                return self._get_error_evaluation("JSON 解析失敗")
                
        except Exception as e:
            print(f"評估過程發生錯誤: {e}")
            if 'result' in locals():
                print(f"原始回應: {result[:200]}...")  # 只顯示前200個字符
            return self._get_error_evaluation(str(e))

    def _get_error_evaluation(self, error_message: str) -> Dict[str, Any]:
        """生成錯誤評估結果"""
        return {
            "relevance": {"score": 0, "reason": f"評估失敗: {error_message}"},
            "clarity": {"score": 0, "reason": "評估失敗"},
            "completeness": {"score": 0, "reason": "評估失敗"},
            "measurability": {"score": 0, "reason": "評估失敗"},
            "feasibility": {"score": 0, "reason": "評估失敗"},
            "prioritization": {"score": 0, "reason": "評估失敗"},
            "acceptance_criteria": {"score": 0, "reason": "評估失敗"}
        }

def print_evaluation(evaluation: Dict[str, Any]):
    """Print evaluation results"""
    print("-" * 50)
    
    # If overall_score is provided in the evaluation, use it directly
    if "overall_score" in evaluation:
        print("\nScores:")
        for criterion, score in evaluation.get("scores", {}).items():
            print(f"{criterion.capitalize()}: {score}/10")
            print(f"Reason: {evaluation.get('reasons', {}).get(criterion, 'No reason provided')}")
            print()
            
        print("\nSuggestions for improvement:")
        for suggestion in evaluation.get("suggestions", []):
            print(f"- {suggestion}")
            
        print("\nConsistency Check:")
        print(evaluation.get("consistency_check", "No consistency check provided"))
            
        print("\nOverall Score:")
        print(f"Total: {evaluation['overall_score']:.1f}/10")
    else:
        # Fallback to old format with weights
        weights = {
            "relevance": 0.2,
            "clarity": 0.15,
            "completeness": 0.15,
            "measurability": 0.125,
            "feasibility": 0.125,
            "prioritization": 0.125,
            "acceptance_criteria": 0.125
        }
        
        total_score = 0
        for criterion in weights.keys():
            if criterion in evaluation:
                print(f"\n{criterion.capitalize()}:")
                print(f"Score: {evaluation[criterion]['score']}/10")
                print(f"Reason: {evaluation[criterion]['reason']}")
                total_score += evaluation[criterion]['score'] * weights[criterion]
        
        print("\nWeighted Average Score:")
        print(f"Total: {total_score:.1f}/10")
    
    print("-" * 50)

def test_enrich_task():
    """測試任務豐富化內容生成"""
    prompt_manager = PromptManager("prompts.json")
    evaluator = ContentEvaluator(prompt_manager)
    
    task_info = {
        "title": "Implement User Registration Feature",
        "description": "Need to implement a basic user registration feature, including form validation and database storage.",
        "parent": {
            "title": "User Management System",
            "description": "Build a complete user management system, including registration, login, and permission management features."
        }
    }
    
    # 測試 comprehensive prompt
    print("\n測試 Comprehensive Prompt...")
    print("-" * 50)
    content = evaluator.generate_content(task_info, style="comprehensive")
    print("生成的內容：")
    print(content)
    print("-" * 50)
    
    print("\n評估結果：")
    evaluation = evaluator.evaluate_content(content, original_task=json.dumps(task_info))
    print_evaluation(evaluation)
    
    # 測試 concise prompt
    print("\n測試 Concise Prompt...")
    print("-" * 50)
    content = evaluator.generate_content(task_info, style="concise")
    print("生成的內容：")
    print(content)
    print("-" * 50)
    
    print("\n評估結果：")
    evaluation = evaluator.evaluate_content(content, original_task=json.dumps(task_info))
    print_evaluation(evaluation)

def main():
    # 執行任務豐富化測試
    test_enrich_task()

if __name__ == "__main__":
    main()
