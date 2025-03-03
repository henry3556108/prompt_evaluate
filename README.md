# PRD Generation and Evaluation System

A Python-based system for generating and evaluating Product Requirements Documents (PRDs) using AI models (Claude and GPT-4).

## Features

- Generate structured PRD content using Jira markdown format
- Support for comprehensive and concise generation styles
- Evaluation system with multiple criteria:
  - Relevance
  - Clarity
  - Completeness
  - Measurability
  - Feasibility
  - Prioritization
  - Acceptance Criteria

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your API keys:
   ```
   chatgpt_api_key=your_openai_api_key
   claude_api_key=your_claude_api_key
   ```

## Usage

```python
from test_generation import PromptManager, ContentEvaluator

# Initialize
prompt_manager = PromptManager("prompts.json")
evaluator = ContentEvaluator(prompt_manager)

# Generate content
task_info = {
    "title": "Implement User Registration Feature",
    "description": "Need to implement a basic user registration feature...",
    "parent": {
        "title": "User Management System",
        "description": "Build a complete user management system..."
    }
}

content = evaluator.generate_content(task_info, style="comprehensive")
evaluation = evaluator.evaluate_content(content)
```

## Configuration

- `prompts.json`: Contains all prompt templates and evaluation criteria
- `environment.yml`: Conda environment configuration
- `.env`: API key configuration (not included in repository)

## Requirements

- Python 3.8+
- OpenAI API key
- Claude API key
