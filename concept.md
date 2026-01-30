# LeanPrompt Concept & Philosophy

## Core Philosophy: "Deterministic AI Engineering"

대부분의 AI 라이브러리는 '자유로운 대화'에 집중하지만, **LeanPrompt**는 **'신뢰 가능한 기능'**에 집중합니다. 우리는 AI를 다음 세 가지 원칙 아래 관리합니다.

1. **AI as a Component:** AI 응답은 데이터베이스 쿼리 결과처럼 구조화되고 검증되어야 합니다.
2. **Efficiency by Default:** 무의미한 프롬프트 반복 전송은 리소스 낭비입니다. 세션과 캐싱을 통해 엔지니어링적 효율을 극대화합니다.
3. **Decoupled Logic:** 프롬프트(기획/설계)와 로직(구현)은 분리되어야 합니다. 마크다운은 그 최적의 접점입니다.

## Technical Architecture

### 1. 세션 기반 컨텍스트 캐싱 (Session-Key Sharing)
- 클라이언트와 서버는 첫 연결 시 `Session-ID`를 공유합니다.
- 서버는 해당 ID의 첫 요청 시에만 무거운 System Prompt를 LLM에 전달하고, 이후 요청에서는 델타(Delta) 값만 처리합니다.
- 이는 **DeepSeek Prefix Caching**이나 **Gemini Context Caching**과 연동되어 비용을 절감합니다.

### 2. 가드레일 시스템 (The Guardrail)
- 단순한 에러 리턴이 아닙니다. 검증 실패 시 LeanPrompt는 LLM에게 무엇이 틀렸는지 피드백을 주며 **자기 수정(Self-Correction)**을 요구합니다.
- 개발자는 `validator` 함수를 통해 비즈니스 규칙을 강제할 수 있습니다.

## 🛣️ Development Roadmap

### Phase 1: Foundation (Current)
- FastAPI 통합 레이어 및 기본 웹소켓 프로토콜 정립.
- Pydantic 기반 모델 검증기 구현.

### Phase 2: Optimization
- 주요 LLM 프로바이더별 전용 캐싱 어댑터(Anthropic, Google, DeepSeek) 지원.
- 마크다운 내 Frontmatter 설정을 통한 세밀한 모델 제어.

### Phase 3: Ecosystem
- React 외 Vue, Svelte 클라이언트 확장.
- 로컬 테스트를 위한 Mock LLM 서버 기능 내장.
