"""
AI 콘텐츠 생성 파이프라인 - CrewAI Flow를 사용한 자동화 워크플로우

이 코드는 주제를 입력받아 블로그/트윗/LinkedIn 포스트를 자동으로 생성하고,
품질 점수가 기준(8점 이상)에 도달할 때까지 자동으로 개선하는 AI 에이전트 시스템입니다.

핵심 개념:
- Flow: 여러 단계를 연결하는 워크플로우 오케스트레이션
- State: 전체 파이프라인에서 공유되는 데이터 상태
- Decorator: @start, @listen, @router로 실행 흐름 제어
- Feedback Loop: 품질 검사 → 재생성 반복으로 콘텐츠 품질 향상
"""

from typing import List
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai.agent import Agent
from crewai import LLM
from pydantic import BaseModel
from tools import web_search_tool
from seo_crew import SeoCrew
from virality_crew import ViralityCrew


# ============================================================
# 데이터 모델 정의 (Pydantic BaseModel)
# ============================================================
# Pydantic을 사용하면 타입 검증, 직렬화, LLM 응답 파싱이 자동화됩니다.
# 특히 LLM의 structured output을 받을 때 매우 유용합니다.

class BlogPost(BaseModel):
    """블로그 포스트 구조 정의"""
    title: str           # 제목
    subtitle: str        # 부제목
    sections: List[str]  # 본문 섹션들 (여러 단락)


class Tweet(BaseModel):
    """트윗 구조 정의"""
    content: str    # 트윗 내용 (150자 이내)
    hashtags: str   # 해시태그


class LinkedInPost(BaseModel):
    """LinkedIn 포스트 구조 정의"""
    hook: str            # 시선을 끄는 도입부
    content: str         # 본문
    call_to_action: str  # 행동 유도 문구 (CTA)


class Score(BaseModel):
    """콘텐츠 품질 평가 점수"""
    score: int = 0    # 0-10점 척도의 점수
    reason: str = ""  # 점수에 대한 설명 (개선이 필요한 이유)


class ContentPipelineState(BaseModel):
    """
    전체 파이프라인의 상태를 관리하는 클래스

    Flow의 모든 단계에서 self.state로 접근 가능하며,
    각 단계가 상태를 읽고 수정하면서 데이터가 흘러갑니다.

    State 관리의 장점:
    - 단계 간 데이터 전달이 명시적
    - 디버깅 시 현재 상태 확인 용이
    - 파이프라인 중단 후 재개 가능
    """

    # === 입력 데이터 ===
    content_type: str = ""  # "tweet" | "blog" | "linkedin"
    topic: str = ""         # 콘텐츠 주제

    # === 내부 처리 데이터 ===
    max_length: int = 0        # 콘텐츠 타입별 최대 길이
    research: str = ""         # 리서치 에이전트가 수집한 정보
    score: Score | None = None # 품질 평가 점수 (None이면 아직 평가 전)

    # === 생성된 콘텐츠 (타입별로 하나만 사용됨) ===
    blog_post: BlogPost | None = None
    tweet: Tweet | None = None
    linkedin_post: LinkedInPost | None = None


class ContentPipelineFlow(Flow[ContentPipelineState]):
    """
    콘텐츠 생성 파이프라인의 전체 흐름을 정의하는 Flow 클래스

    Flow[ContentPipelineState]: 제네릭으로 State 타입을 지정

    주요 데코레이터:
    - @start(): 파이프라인의 시작점 (kickoff 시 가장 먼저 실행)
    - @listen(메서드): 특정 메서드가 완료되면 실행
    - @router(메서드): 조건에 따라 다음 경로를 결정
    - or_("route1", "route2"): 여러 경로 중 하나에서 오면 실행
    """

    @start()
    def init_content_pipeline(self):
        """
        1단계: 파이프라인 초기화 및 유효성 검사

        @start() 데코레이터:
        - flow.kickoff()가 호출되면 가장 먼저 실행되는 메서드
        - 입력 검증 및 초기 설정을 수행
        """

        # 입력 검증: 지원하는 콘텐츠 타입인지 확인
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError("The content type is wrong.")

        # 입력 검증: 주제가 비어있지 않은지 확인
        if self.state.topic == "":
            raise ValueError("The topic can't be blank.")

        # 콘텐츠 타입별 최대 길이 설정 (현재는 사용되지 않지만 향후 검증용)
        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type == "blog":
            self.state.max_length = 800
        elif self.state.content_type == "linkedin":
            self.state.max_length = 500

    @listen(init_content_pipeline)
    def conduct_research(self):
        """
        2단계: 리서치 에이전트로 주제에 대한 정보 수집

        @listen(init_content_pipeline):
        - init_content_pipeline이 완료되면 자동 실행
        - 이전 단계의 state를 읽을 수 있음

        Agent 패턴:
        - role: 에이전트의 역할 정의 (프롬프트에 영향)
        - backstory: 배경 스토리로 페르소나 강화
        - goal: 명확한 목표 설정
        - tools: 에이전트가 사용할 도구 (웹 검색 등)
        """

        # 리서치 전문 에이전트 생성
        researcher = Agent(
            role="Head Researcher",
            backstory="You're like a digital detective who loves digging up fascinating facts and insights. You have a knack for finding the good stuff that others miss.",
            goal=f"Find the most interesting and useful info about {self.state.topic}",
            tools=[web_search_tool],  # 웹 검색 도구 제공
        )

        # 에이전트 실행: kickoff()는 목표를 달성하기 위해 도구를 사용하며 작업
        # 결과는 문자열로 반환되어 state.research에 저장
        self.state.research = researcher.kickoff(
            f"Find the most interesting and useful info about {self.state.topic}"
        )

    @router(conduct_research)
    def conduct_research_router(self):
        """
        3단계: 콘텐츠 타입에 따라 다음 경로 결정

        @router 데코레이터:
        - 조건부 분기를 구현하는 핵심 패턴
        - 반환된 문자열이 다음에 실행될 경로의 이름이 됨
        - 동적 워크플로우를 가능하게 함

        이 Router의 역할:
        - 리서치 완료 후 콘텐츠 타입별로 다른 생성 메서드 호출
        """
        content_type = self.state.content_type

        # 문자열 반환 → Flow가 해당 이름의 경로를 실행
        if content_type == "blog":
            return "make_blog"
        elif content_type == "tweet":
            return "make_tweet"
        else:
            return "make_linkedin_post"

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        """
        4-A단계: 블로그 포스트 생성 (또는 재생성)

        @listen(or_("make_blog", "remake_blog")):
        - "make_blog" 또는 "remake_blog" 경로에서 오면 실행
        - or_(): 여러 트리거 중 하나라도 발생하면 실행
        - 피드백 루프 구현: 품질이 낮으면 "remake_blog"로 재진입

        LLM 활용 패턴:
        - response_format=BlogPost: Pydantic 모델로 구조화된 출력 강제
        - 초기 생성 vs 개선: 조건에 따라 다른 프롬프트 사용
        """

        blog_post = self.state.blog_post

        # LLM 인스턴스 생성: response_format으로 출력 형식 지정
        llm = LLM(model="openai/o4-mini", response_format=BlogPost)

        # 케이스 1: 최초 생성 (blog_post가 None)
        if blog_post is None:
            result = llm.call(
                f"""
            Make a blog post with SEO practices on the topic {self.state.topic} using the following research:

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )
        # 케이스 2: 개선 (품질 점수가 낮아서 재생성)
        else:
            result = llm.call(
                f"""
            You wrote this blog post on {self.state.topic}, but it does not have a good SEO score because of {self.state.score.reason}

            Improve it.

            <blog post>
            {self.state.blog_post.model_dump_json()}
            </blog post>

            Use the following research.

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )

        # JSON 문자열을 BlogPost 객체로 변환하여 state에 저장
        self.state.blog_post = BlogPost.model_validate_json(result)

    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        """
        4-B단계: 트윗 생성 (또는 재생성)

        블로그와 동일한 패턴이지만:
        - 평가 기준: SEO → Virality (바이럴 가능성)
        - 출력 형식: BlogPost → Tweet
        - 프롬프트: "go viral" 강조
        """

        tweet = self.state.tweet

        llm = LLM(model="openai/o4-mini", response_format=Tweet)

        if tweet is None:
            result = llm.call(
                f"""
            Make a tweet that can go viral on the topic {self.state.topic} using the following research:

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )
        else:
            result = llm.call(
                f"""
            You wrote this tweet on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason}

            Improve it.

            <tweet>
            {self.state.tweet.model_dump_json()}
            </tweet>

            Use the following research.

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )

        self.state.tweet = Tweet.model_validate_json(result)

    @listen(or_("make_linkedin_post", "remake_linkedin_post"))
    def handle_make_linkedin_post(self):
        """
        4-C단계: LinkedIn 포스트 생성 (또는 재생성)

        트윗과 유사하지만:
        - 출력 형식: hook, content, call_to_action 구조
        - 더 긴 형식의 전문적인 콘텐츠
        """

        linkedin_post = self.state.linkedin_post

        llm = LLM(model="openai/o4-mini", response_format=LinkedInPost)

        if linkedin_post is None:
            result = llm.call(
                f"""
            Make a linkedin post that can go viral on the topic {self.state.topic} using the following research:

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )
        else:
            result = llm.call(
                f"""
            You wrote this linkedin post on {self.state.topic}, but it does not have a good virality score because of {self.state.score.reason}

            Improve it.

            <linkedin_post>
            {self.state.linkedin_post.model_dump_json()}
            </linkedin_post>

            Use the following research.

            <research>
            ================
            {self.state.research}
            ================
            </research>
            """
            )

        self.state.linkedin_post = LinkedInPost.model_validate_json(result)

    @listen(handle_make_blog)
    def check_seo(self):
        """
        5-A단계: 블로그 포스트의 SEO 품질 평가

        Crew 패턴:
        - SeoCrew: 여러 에이전트가 협업하는 팀 (seo_crew.py에 정의)
        - 전문화된 평가 로직을 별도 모듈로 분리
        - kickoff(): Crew 실행, inputs로 평가 대상 전달
        - result.pydantic: 결과를 Pydantic 모델(Score)로 파싱
        """

        # SEO 전문 Crew 실행 → Score 객체 반환
        result = (
            SeoCrew()
            .crew()
            .kickoff(
                inputs={
                    "topic": self.state.topic,
                    "blog_post": self.state.blog_post.model_dump_json(),
                }
            )
        )
        self.state.score = result.pydantic  # Score 객체로 저장

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        """
        5-B단계: 트윗/LinkedIn 포스트의 바이럴 가능성 평가

        @listen(or_(...)): 트윗 또는 LinkedIn 포스트 생성 완료 후 실행
        """
        result = (
            ViralityCrew()
            .crew()
            .kickoff(
                inputs={
                    "topic": self.state.topic,
                    "content_type": self.state.content_type,
                    "content": (
                        self.state.tweet
                        if self.state.content_type == "tweet"
                        else self.state.linkedin_post
                    ),
                }
            )
        )
        self.state.score = result.pydantic

    @router(or_(check_seo, check_virality))
    def score_router(self):
        """
        6단계: 품질 점수에 따라 완료 or 재생성 결정

        피드백 루프(Feedback Loop)의 핵심:
        - 점수 >= 8: "check_passed"로 파이프라인 종료
        - 점수 < 8: "remake_*"로 4단계로 다시 돌아가 개선

        이 패턴으로 자동으로 품질을 반복 개선합니다.
        무한 루프 방지를 위해 최대 반복 횟수 제한이 필요할 수 있습니다.
        """

        content_type = self.state.content_type
        score = self.state.score

        # 품질 기준 충족: 파이프라인 종료
        if score.score >= 8:
            return "check_passed"
        # 품질 미달: 콘텐츠 타입별로 재생성 경로로 분기
        else:
            if content_type == "blog":
                return "remake_blog"  # → handle_make_blog 재실행
            elif content_type == "linkedin":
                return "remake_linkedin_post"  # → handle_make_linkedin_post 재실행
            else:
                return "remake_tweet"  # → handle_make_tweet 재실행

    @listen("check_passed")
    def finalize_content(self):
        """
        7단계: 최종 완료 처리

        @listen("check_passed"): score_router에서 품질 통과 시 실행

        현재는 단순 메시지 출력이지만, 실제로는:
        - 데이터베이스 저장
        - 파일 출력
        - API로 발행
        - 알림 전송 등 후처리 가능
        """
        print("Finalizing content")
        # TODO: 실제 운영에서는 여기서 콘텐츠를 저장/발행


# ============================================================
# Flow 실행 (Entry Point)
# ============================================================

# Flow 인스턴스 생성
flow = ContentPipelineFlow()

# 파이프라인 시작
# inputs의 데이터가 ContentPipelineState에 매핑됩니다
flow.kickoff(
    inputs={
        "content_type": "blog",      # 생성할 콘텐츠 타입
        "topic": "AI Dog Training",  # 주제
    },
)

# 실행 흐름 요약:
# 1. init_content_pipeline: 검증 및 초기화
# 2. conduct_research: 리서치 에이전트가 정보 수집
# 3. conduct_research_router: 콘텐츠 타입별 분기
# 4. handle_make_blog: 블로그 포스트 생성
# 5. check_seo: SEO 점수 평가
# 6. score_router: 점수 >= 8이면 완료, 아니면 4단계로 재진입
# 7. finalize_content: 최종 완료

# flow.plot()  # Flow의 시각화 다이어그램 생성 (주석 해제하면 그래프 출력)