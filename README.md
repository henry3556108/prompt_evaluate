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
- Automated testing framework for content generation
- Support for both Claude and GPT-4 API integration

## Components

### PromptManager
- Manages prompt templates from JSON configuration
- Supports different prompt styles (comprehensive/concise)
- Handles system and user prompt generation
- Flexible template parameter substitution

### ContentEvaluator
- Integrates with both Claude and OpenAI APIs
- Generates content based on task information
- Provides comprehensive content evaluation
- Supports different generation styles and prompt types

### Testing Framework
- Automated test cases for various scenarios:
  - User Registration Features
  - API Performance Optimization
  - Data Analytics Dashboard
  - Security Enhancements
  - Mobile App Features
- Detailed evaluation metrics and scoring
- Comparison between comprehensive and concise generation styles
- Optional detailed output for debugging

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
