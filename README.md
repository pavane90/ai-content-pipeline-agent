# AI Content Pipeline Agent

CrewAI Flow를 활용한 자동화된 콘텐츠 생성 파이프라인입니다. AI 에이전트가 주제를 조사하고, 블로그/트윗/LinkedIn 포스트를 자동으로 생성하며, 품질 점수가 기준에 도달할 때까지 자동으로 개선합니다.

## 📋 프로젝트 개요

이 프로젝트는 다음과 같은 자동화 워크플로우를 제공합니다:

1. **리서치 단계**: AI 에이전트가 웹 검색을 통해 주제 관련 정보 수집
2. **콘텐츠 생성**: 수집된 정보를 바탕으로 콘텐츠 생성
3. **품질 평가**: SEO/바이럴 점수 평가 (0-10점)
4. **자동 개선**: 점수가 8점 미만이면 피드백을 반영하여 재생성
5. **완료**: 품질 기준 충족 시 최종 콘텐츠 확정

### 핵심 기술

- **CrewAI Flow**: 워크플로우 오케스트레이션
- **Pydantic**: 타입 안전한 데이터 모델링
- **OpenAI API**: LLM 기반 콘텐츠 생성
- **Firecrawl**: 웹 검색 및 스크래핑

## 🚀 시작하기

### 필수 요구사항

- Python 3.13 이상
- OpenAI API 키
- Firecrawl API 키

### 1. 프로젝트 클론

```bash
git clone <repository-url>
cd ai-content-pipeline-agent
```

### 2. 가상 환경 설정

#### uv 사용 (권장)

```bash
# uv 설치 (미설치 시)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 의존성 설치
uv sync
```

#### pip 사용

```bash
# 가상 환경 생성
python -m venv .venv

# 가상 환경 활성화
# macOS/Linux:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 API 키를 설정합니다:

```bash
# .env 파일 생성
cp .env.example .env  # 또는 직접 생성
```

`.env` 파일 내용:

```env
# OpenAI API 키 (필수)
OPENAI_API_KEY=your-openai-api-key-here

# Firecrawl API 키 (필수)
FIRECRAWL_API_KEY=your-firecrawl-api-key-here

# CrewAI 추적 활성화 (선택)
CREWAI_TRACING_ENABLED=true
```

#### API 키 발급 방법

- **OpenAI API 키**: [platform.openai.com](https://platform.openai.com/api-keys)에서 발급
- **Firecrawl API 키**: [firecrawl.dev](https://firecrawl.dev)에서 발급

## 💡 사용 방법

### 기본 실행

```bash
# uv 사용
uv run main.py

# 또는 Python 직접 실행
python main.py
```

### 콘텐츠 타입 및 주제 변경

`main.py` 파일의 마지막 부분을 수정하여 원하는 콘텐츠를 생성할 수 있습니다:

```python
flow.kickoff(
    inputs={
        "content_type": "blog",        # "tweet", "blog", "linkedin" 중 선택
        "topic": "AI Dog Training",    # 원하는 주제 입력
    },
)
```

### Flow 시각화

워크플로우 다이어그램을 생성하려면:

```python
# main.py 마지막 줄 주석 해제
flow.plot()
```

실행 후 `crewai_flow.html` 파일이 생성되며, 브라우저로 열어 워크플로우를 확인할 수 있습니다.

## 📁 프로젝트 구조

```
ai-content-pipeline-agent/
├── main.py              # 메인 파이프라인 (Flow 정의)
├── seo_crew.py          # SEO 평가 Crew
├── virality_crew.py     # 바이럴 평가 Crew
├── tools.py             # 웹 검색 도구
├── .env                 # 환경 변수 (git에 포함 안 됨)
├── pyproject.toml       # 프로젝트 설정
└── README.md            # 이 파일
```

## 🔧 주요 구성 요소

### ContentPipelineFlow (main.py)

전체 워크플로우를 관리하는 Flow 클래스입니다:

- `init_content_pipeline`: 입력 검증 및 초기화
- `conduct_research`: 웹 검색으로 정보 수집
- `conduct_research_router`: 콘텐츠 타입별 분기
- `handle_make_blog/tweet/linkedin_post`: 콘텐츠 생성
- `check_seo/virality`: 품질 평가
- `score_router`: 점수에 따라 완료 or 재생성 결정
- `finalize_content`: 최종 완료 처리

### Crew 모듈

- **SeoCrew**: 블로그 포스트의 SEO 품질 평가
- **ViralityCrew**: 트윗/LinkedIn 포스트의 바이럴 가능성 평가

### 데이터 모델

- `BlogPost`: 제목, 부제목, 섹션
- `Tweet`: 내용, 해시태그
- `LinkedInPost`: 훅, 내용, CTA
- `Score`: 점수, 개선 사유

## 🎯 학습 포인트

이 프로젝트를 통해 다음을 배울 수 있습니다:

1. **Flow 패턴**: `@start`, `@listen`, `@router` 데코레이터로 워크플로우 구성
2. **State 관리**: Pydantic 모델로 파이프라인 전체 상태 추적
3. **Feedback Loop**: 품질 검사 후 자동 재생성으로 품질 개선
4. **Agent 패턴**: CrewAI의 Agent와 Crew로 역할 기반 작업 분담
5. **Structured Output**: LLM에서 타입 안전한 데이터 추출

## 🐛 트러블슈팅

### API 키 오류

```
Error: OPENAI_API_KEY not found
```

→ `.env` 파일이 있는지, API 키가 올바르게 설정되었는지 확인하세요.

### 의존성 오류

```
ModuleNotFoundError: No module named 'crewai'
```

→ 가상 환경이 활성화되어 있는지, 의존성이 설치되었는지 확인하세요.

### 웹 검색 실패

```
Error using tool.
```

→ Firecrawl API 키가 유효한지, API 할당량이 남아있는지 확인하세요.

## 📝 라이선스

이 프로젝트는 학습 목적으로 작성되었습니다.

## 🤝 기여

이슈나 개선 사항이 있다면 자유롭게 Issue나 PR을 등록해주세요.
