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
    total_score = 0
    
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
        print("-" * 50)
        return evaluation['overall_score']

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
        return total_score

def calculate_average_scores(evaluations):
    """計算評估結果的平均分數"""
    total_scores = {
        "relevance": 0,
        "clarity": 0,
        "completeness": 0,
        "actionable": 0
    }
    count = 0
    
    for eval in evaluations:
        if isinstance(eval, dict) and "scores" in eval:
            scores = eval["scores"]
            if all(key in scores for key in ["相關性", "清晰性", "完整性", "可執行性"]):
                total_scores["relevance"] += float(scores["相關性"])
                total_scores["clarity"] += float(scores["清晰性"])
                total_scores["completeness"] += float(scores["完整性"])
                total_scores["actionable"] += float(scores["可執行性"])
                count += 1
    
    if count == 0:
        return {k: 0 for k in total_scores}, 0
        
    avg_scores = {k: round(v/count, 2) for k, v in total_scores.items()}
    overall_avg = round(sum(avg_scores.values()) / len(avg_scores), 2)
    return avg_scores, overall_avg

def test_enrich_task(show_details=False):
    """測試任務豐富化內容生成
    Args:
        show_details (bool): 是否顯示詳細的生成內容和評估結果
    """
    test_cases = [
        {
            "name": "User Registration Feature",
            "task_info": {
                "title": "Implement User Registration Feature",
                "description": "Need to implement a basic user registration feature, including form validation and database storage.",
                "parent": {
                    "title": "User Management System",
                    "description": "Build a complete user management system, including registration, login, and permission management features."
                }
            }
        },
        {
            "name": "API Performance Optimization",
            "task_info": {
                "title": "Optimize API Response Time",
                "description": "Current API response time is over 2s. Need to implement caching and query optimization to reduce response time to under 500ms.",
                "parent": {
                    "title": "System Performance Enhancement",
                    "description": "Improve overall system performance focusing on API response times, database queries, and front-end loading."
                }
            }
        },
        {
            "name": "Data Analytics Dashboard",
            "task_info": {
                "title": "Create User Behavior Analytics Dashboard",
                "description": "Develop a dashboard showing key user metrics including daily active users, session duration, and feature usage patterns.",
                "parent": {
                    "title": "Analytics Platform",
                    "description": "Build comprehensive analytics platform for tracking and visualizing user behavior and system performance."
                }
            }
        },
        {
            "name": "Security Enhancement",
            "task_info": {
                "title": "Implement Two-Factor Authentication",
                "description": "Add 2FA support using authenticator apps and SMS verification for enhanced account security.",
                "parent": {
                    "title": "Security Infrastructure Upgrade",
                    "description": "Enhance system security with modern authentication methods and encryption protocols."
                }
            }
        },
        {
            "name": "Mobile App Feature",
            "task_info": {
                "title": "Add Offline Mode Support",
                "description": "Implement offline data synchronization for the mobile app, allowing users to view and edit data without internet connection.",
                "parent": {
                    "title": "Mobile App Development",
                    "description": "Develop feature-rich mobile application with seamless online/offline experience."
                }
            }
        }
    ]
    
    prompt_manager = PromptManager("prompts.json")
    evaluator = ContentEvaluator(prompt_manager)
    
    comprehensive_evaluations = []
    concise_evaluations = []
    
    for test_case in test_cases:
        if show_details:
            print(f"\n\n測試案例: {test_case['name']}")
            print("=" * 50)
        
        # 測試 comprehensive prompt
        if show_details:
            print("\n使用 Comprehensive Prompt:")
            print("-" * 50)
        content = evaluator.generate_content(test_case["task_info"], style="comprehensive")
        if show_details:
            print("生成的內容：")
            print(content)
            print("-" * 50)
        evaluation = evaluator.evaluate_content(content, json.dumps(test_case["task_info"]))
        comprehensive_evaluations.append(evaluation)
        if show_details:
            print("\n評估結果：")
            comprehensive_score = print_evaluation(evaluation)
        
        # 測試 concise prompt
        if show_details:
            print("\n使用 Concise Prompt 生成內容:")
        concise_content = evaluator.generate_content(test_case["task_info"], style="concise")
        if show_details:
            print(concise_content)
            print("\n評估 Concise Prompt 生成的內容:")
            
        evaluation = evaluator.evaluate_content(concise_content, test_case["task_info"].get("description"))
        concise_evaluations.append(evaluation)
        if show_details:
            print("\n評估結果：")
            concise_score = print_evaluation(evaluation)
            
            # 計算並顯示平均分數
            print("\n綜合評分比較:")
            print("=" * 50)
            print(f"Comprehensive Score: {comprehensive_score:.1f}")
            print(f"Concise Score: {concise_score:.1f}")
            print("=" * 50)
    
    # 計算並顯示所有測試案例的平均分數
    comprehensive_avg = sum([evaluation["overall_score"] for evaluation in comprehensive_evaluations]) / len(comprehensive_evaluations)
    concise_avg = sum([evaluation["overall_score"] for evaluation in concise_evaluations]) / len(concise_evaluations)
    print("\n所有測試案例的平均分數:")
    print("=" * 50)
    print(f"Comprehensive Average Score: {comprehensive_avg:.1f}")
    print(f"Concise Average Score: {concise_avg:.1f}")
    print("=" * 50)

def main():
    """主程序"""
    # 執行任務豐富化測試，可以通過參數控制是否顯示詳細信息
    test_enrich_task(show_details=True)  

if __name__ == "__main__":
    main()
