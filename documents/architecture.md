# 프로젝트 아키텍처 개요

## 1. 프로젝트 개요 및 기술 스택
- 프로젝트
  - leanprompt (Backend)
  - leanprompt-client (Frontend)
- 기술 스택
  - Backend: Python, FastAPI
  - Frontend: React, TypeScript
  - 통신: WebSocket (실시간 스트리밍, 세션 유지)
- 주요 목표
  - LLM 호출 신뢰성(Validation)
  - 토큰 비용 절감(Caching)
  - 선언적 관리(Markdown-based Routing)

## 2. 백엔드 (leanprompt) 핵심 아키텍처

### 2.1 FastAPI 통합 및 라우팅
- 플러그인 구조: FastAPI 앱 인스턴스를 받아 기능을 확장하는 클래스 형태
- 데코레이터 기반 인터페이스 예시
  - `@lp.route(path, prompt_file)` — 경로와 마크다운 프롬프트 파일 매핑
  - `@Guard.validate_output(PydanticModel)` — LLM 응답 스키마 검증
- 파일 기반 프롬프트 관리
  - `prompts/` 디렉토리 내 마크다운 파일명/경로 ↔ API 엔드포인트 동기화

### 2.2 세션 및 토큰 최적화 (Context Caching)
- 세션 관리: 클라이언트와 Session-ID 공유로 상태 유지
- 델타 전송: 세션 시작 시 시스템 프롬프트(Full Context) 전송 후 입력(Delta)만 전송
- 프로바이더 연동: DeepSeek(Prefix Caching), Gemini(Context Caching), Anthropic 등 하드웨어/서비스 캐시 활용 설계
- 프롬프트 해싱: 시스템 프롬프트 변경 여부를 해시로 판단하여 캐시 갱신 결정

### 2.3 검증 및 가드레일 (Reliability)
- 출력 검증: Pydantic 모델로 LLM의 JSON 응답 형식 검사
- 자기 수정 로직: 검증 실패 시 에러 메시지를 포함해 LLM에게 재생성 요청하는 Retry 메커니즘

## 3. 프론트엔드 (leanprompt-client) 요구사항
- 커스텀 훅: `useLeanPrompt`
  - WebSocket 연결 상태 관리: `connecting`, `connected`, `disconnected`
  - 메시지 히스토리 관리 및 실시간 스트리밍 업데이트
  - Session-ID 자동 저장 및 재사용 (localStorage/sessionStorage)
- 통신 프로토콜: JSON 기반 WebSocket 메시지 규격
  - 메시지 타입: `chunk`, `error`, `complete`, `session_init`

## 4. 시스템 디렉토리 구조 및 규칙
- Prompts
  - `prompts/*.md` 내부 Frontmatter(YAML) 파싱
  - 모델 설정(temperature, model_name 등) 및 검증 함수 연결 정보 포함
- Session Reset
  - 단일 세션에 요청이 임계치 이상 쌓일 경우 세션 자동 요약 또는 재생성 로직 포함
- 기타 규칙
  - 프롬프트 파일 변경 시 해시 기반으로 캐시 무효화
  - 라우팅·검증 설정은 마크다운/Frontmatter로 선언적 관리