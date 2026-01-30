# LeanPrompt (Backend)

**LeanPrompt**는 FastAPI 기반의 엔지니어링 중심 LLM 통합 프레임워크입니다. LLM을 단순한 텍스트 생성기가 아닌, 신뢰성 있고 예측 가능한 소프트웨어 컴포넌트로 활용할 수 있도록 돕습니다.

## ✨ Key Features

* **FastAPI Native:** 기존 FastAPI 앱에 플러그인 형태로 즉시 통합.
* **Markdown-Driven Prompts:** 프롬프트를 코드가 아닌 `.md` 파일로 분리하여 관리. 파일명이 곧 API 경로가 됩니다.
* **Session-Based Context Caching:** 세션 시작 시에만 프롬프트를 전달하고 이후엔 입력값만 전송하여 토큰 비용을 획기적으로 절감합니다.
* **Output Guardrails:** Pydantic 모델을 통한 출력 값 검증 및 자동 재시도(Retry) 로직 내장.
* **WebSocket First:** 실시간 스트리밍 피드백을 위해 고도로 최적화된 웹소켓 통신 지원.

## 🚀 Quick Start

### Installation
```bash
pip install leanprompt
```

### Usage
```python
from fastapi import FastAPI
from leanprompt import LeanPrompt, Guard
from pydantic import BaseModel

app = FastAPI()
lp = LeanPrompt(app, provider="deepseek")

class ResponseModel(BaseModel):
    answer: str
    confidence: float

# prompts/ask_me.md 파일을 로드하여 /ask 경로 생성
@lp.route("/ask", prompt_file="ask_me.md")
@Guard.validate(ResponseModel)
async def handle_ask(user_input: str):
    return {"input": user_input}
```
