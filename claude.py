import anthropic
import os
from typing import Optional
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class ClaudeAPI:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Claude API client
        :param api_key: Anthropic API key. If not provided, will look for CLAUDE_API_KEY environment variable
        """
        self.api_key = api_key or os.getenv("claude_api_key")
        if not self.api_key:
            raise ValueError("API key must be provided either directly or through claude_api_key environment variable")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    def get_completion(self, system_prompt: str, user_prompt: str, model: str = "claude-3-opus-20240229", max_tokens: int = 1000) -> str:
        """
        Get completion from Claude using system and user prompts
        
        :param system_prompt: The system prompt to set Claude's behavior
        :param user_prompt: The user's input/question
        :param model: The Claude model to use
        :param max_tokens: Maximum number of tokens in the response
        :return: Claude's response
        """
        try:
            message = self.client.messages.create(
                max_tokens=max_tokens,
                model=model,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ],
                temperature=0
            )
            return message.content[0].text
            
        except Exception as e:
            raise Exception(f"Error getting completion from Claude: {str(e)}")

def main():
    # Example usage
    claude = ClaudeAPI()  # Will use environment variable
    
    system_prompt = "You are a helpful AI assistant."
    user_prompt = "What is the capital of France?"
    
    try:
        response = claude.get_completion(system_prompt, user_prompt)
        print(f"Claude's response: {response}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()