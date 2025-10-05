# Gemini Integration Module (`src/gemini_integration/`)

## Purpose
Google Gemini 2.5 Flash API integration for AI-powered code analysis and issue insights.

## Key Components

### Client (Low-Level API)
```python
class GeminiClient:
    """Low-level Gemini API client with retry logic."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def generate(self, prompt: str) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text
```

### Analyzer (High-Level Interface)
```python
class GeminiAnalyzer:
    """High-level analyzer for code and issues."""
    
    async def analyze_code(self, code: str, language: str) -> CodeAnalysisResult:
        prompt = self._build_code_analysis_prompt(code, language)
        response = await self.client.generate(prompt)
        return self._parse_code_analysis(response)
    
    async def suggest_labels(self, issue: Issue, available_labels: List[str]) -> List[str]:
        # AI-powered label suggestions
        pass
```

## Prompt Engineering

### Structure
```python
prompt = f"""
# Context
{context}

# Task
{task}

# Output Format
- Be specific
- Use JSON format
- Limit to 500 words
"""
```

### Few-Shot Examples
```python
prompt = """
Examples:
Issue: "Login button doesn't work" → Category: bug
Issue: "Add dark mode" → Category: feature

Now classify: "{text}"
"""
```

### Structured Output
```python
structured_prompt = f"""
{prompt}

Respond ONLY with valid JSON:
{{
    "severity": "low|medium|high|critical",
    "suggestions": ["...", "..."]
}}
"""
```

## Best Practices

### Error Handling
```python
try:
    response = await client.generate(prompt)
except RateLimitError:
    await asyncio.sleep(60)
    response = await client.generate(prompt)
except GeminiAPIError as e:
    logger.error(f"API error: {e}")
    return None
```

### Response Validation
```python
def validate_response(response: str) -> bool:
    try:
        json.loads(response)
        return True
    except json.JSONDecodeError:
        return False
```

### Caching
```python
class CachedGeminiAnalyzer:
    def __init__(self, api_key: str):
        self.analyzer = GeminiAnalyzer(api_key)
        self._cache = {}
    
    async def analyze_code(self, code: str) -> CodeAnalysisResult:
        cache_key = hashlib.sha256(code.encode()).hexdigest()
        if cache_key in self._cache:
            return self._cache[cache_key]
        # ...
```

## Testing
```python
@pytest.fixture
def mock_gemini_client(mocker):
    mock_response = mocker.Mock()
    mock_response.text = "Test analysis"
    mock_model = mocker.Mock()
    mock_model.generate_content_async = AsyncMock(return_value=mock_response)
    mocker.patch('google.generativeai.GenerativeModel', return_value=mock_model)
    return mock_model
```

## Security
- Never send sensitive data (sanitize inputs)
- Validate all responses
- Log API usage (but never log prompts with sensitive data)
- Handle rate limits gracefully
