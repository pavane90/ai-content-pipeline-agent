# CrewAI Flow에서 논리 연산자(and, or)는 Python 예약어와 구분하기 위해 _를 붙여야 함
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from crewai import Agent
from pydantic import BaseModel

# 콘텐츠 생성 파이프라인 Flow 구현
# 트위터, 블로그, 링크드인 포스트를 주제에 따라 자동으로 생성하는 워크플로우

# 파이프라인 상태 관리 클래스
class ContentPipelineState(BaseModel):
    """
    전체 콘텐츠 생성 파이프라인의 상태를 관리하는 데이터 모델
    Flow의 각 단계에서 공유되는 정보를 저장
    """

    # 사용자로부터 받는 입력값들
    content_type: str = ""  # 생성할 콘텐츠 타입 ("tweet", "blog", "linkedin")
    topic: str = ""         # 콘텐츠 주제

    # 파이프라인 내부에서 사용되는 값들
    max_length: int = 0     # 콘텐츠 타입별 최대 글자 수 제한


class ContentPipelineFlow(Flow[ContentPipelineState]):
    """
    콘텐츠 생성 파이프라인의 메인 Flow 클래스
    각 콘텐츠 타입별로 최적화된 생성 및 검증 프로세스를 관리
    """

    @start()
    def init_content_pipeline(self):
        """
        파이프라인 시작점 - 입력값 검증 및 초기 설정
        @start() 데코레이터로 Flow의 첫 번째 실행 단계로 지정
        """
        # 입력값 검증: 지원하는 콘텐츠 타입인지 확인
        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError("The content type is wrong.")

        # 주제가 비어있는지 검증
        if self.state.topic == "":
            raise ValueError("The topic can't be blank.")

        # 콘텐츠 타입별 최대 글자 수 설정
        # 각 플랫폼의 특성에 맞는 최적 길이로 제한
        if self.state.content_type == "tweet":
            self.state.max_length = 150    # 트위터: 간결한 메시지
        elif self.state.content_type == "blog":
            self.state.max_length = 800    # 블로그: 상세한 내용
        elif self.state.content_type == "linkedin":
            self.state.max_length = 500    # 링크드인: 전문적이면서 적당한 길이

    @listen(init_content_pipeline)
    def conduct_research(self):
        """
        주제에 대한 리서치 수행
        @listen() 데코레이터로 init_content_pipeline 완료 후 자동 실행
        실제 구현시에는 여기서 AI 에이전트가 주제 관련 정보를 수집
        """
        print("Researching....")
        # 리서치 완료를 알리는 True 반환 (다음 단계 트리거용)
        return True

    @router(conduct_research)
    def router(self):
        """
        콘텐츠 타입에 따른 경로 분기점
        @router() 데코레이터로 conduct_research 완료 후 실행되며,
        반환값에 따라 다음 실행할 메서드를 결정
        """
        content_type = self.state.content_type

        # 콘텐츠 타입별로 적절한 생성 메서드로 라우팅
        if content_type == "blog":
            return "make_blog"          # 블로그 포스트 생성으로 이동
        elif content_type == "tweet":
            return "make_tweet"         # 트위터 포스트 생성으로 이동
        else:
            return "make_linkedin_post" # 링크드인 포스트 생성으로 이동

    @listen("make_blog")
    def handle_make_blog(self):
        """
        블로그 포스트 생성 처리
        router에서 "make_blog" 반환시 실행됨
        실제 구현시에는 AI 에이전트가 블로그 형식의 긴 글을 생성
        """
        print("Making blog post...")

    @listen("make_tweet")
    def handle_make_tweet(self):
        """
        트위터 포스트 생성 처리
        router에서 "make_tweet" 반환시 실행됨
        실제 구현시에는 AI 에이전트가 150자 이내의 간결한 트윗을 생성
        """
        print("Making tweet...")

    @listen("make_linkedin_post")
    def handle_make_linkedin_post(self):
        """
        링크드인 포스트 생성 처리
        router에서 "make_linkedin_post" 반환시 실행됨
        실제 구현시에는 AI 에이전트가 전문적인 톤의 링크드인 포스트를 생성
        """
        print("Making linkedin post...")

    @listen(handle_make_blog)
    def check_seo(self):
        """
        블로그 포스트 SEO 최적화 검사
        블로그 포스트 생성 완료 후에만 실행됨
        키워드 밀도, 메타 태그, 제목 구조 등을 검증
        """
        print("Checking Blog SEO")

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        """
        소셜 미디어 콘텐츠의 바이럴 가능성 검사
        트윗 또는 링크드인 포스트 생성 완료 후 실행됨
        or_() 사용으로 둘 중 하나라도 완료되면 실행
        해시태그, 감정적 어필, 참여 유도 요소 등을 분석
        """
        print("Checking virality...")

    @listen(or_(check_virality, check_seo))
    def finalize_content(self):
        """
        최종 콘텐츠 완성 및 마무리
        SEO 검사 또는 바이럴성 검사 완료 후 실행됨
        or_() 사용으로 어떤 검사든 완료되면 파이프라인 종료
        최종 포맷팅, 저장, 배포 준비 등을 수행
        """
        print("Finalizing content")


# Flow 인스턴스 생성
flow = ContentPipelineFlow()

# 파이프라인 실행 예시 (현재 주석 처리됨)
# 실제 사용시에는 아래 주석을 해제하고 원하는 입력값을 제공
# flow.kickoff(
#     inputs={
#         "content_type": "tweet",      # 생성할 콘텐츠 타입
#         "topic": "AI Dog Training",   # 콘텐츠 주제
#     },
# )

# 파이프라인 구조를 시각화하여 워크플로우 확인
# 각 단계간의 연결관계와 실행 순서를 그래프로 표시
flow.plot()