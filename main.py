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
    score: int = 0

    # Content
    blog_post: str = ""
    tweet: str = ""
    linkedin_post: str = ""


class ContentPipelineFlow(Flow[ContentPipelineState]):

    @start()
    def init_content_pipeline(self):

        if self.state.content_type not in ["tweet", "blog", "linkedin"]:
            raise ValueError("The content type is wrong.")

        if self.topic == "":
            raise ValueError("The topic can't be blank.")

        if self.state.content_type == "tweet":
            self.state.max_length = 150
        elif self.state.content_type == "blog":
            self.state.max_length = 800
        elif self.state.content_type == "linkedin":
            self.state.max_length = 500

    @listen(init_content_pipeline)
    def conduct_research(self):
        print("Researching....")
        return True

    @router(conduct_research)
    def conduct_research_router(self):
        content_type = self.state.content_type

        if content_type == "blog":
            return "make_blog"
        elif content_type == "tweet":
            return "make_tweet"
        else:
            return "make_linkedin_post"

    @listen(or_("make_blog", "remake_blog"))
    def handle_make_blog(self):
        # if blog post has been made, show the old one to the ai and ask it to improve, else
        # just ask to create.
        print("Making blog post...")

    @listen(or_("make_tweet", "remake_tweet"))
    def handle_make_tweet(self):
        # if tweet has been made, show the old one to the ai and ask it to improve, else
        # just ask to create.
        print("Making tweet...")

    @listen(or_("make_linkedin_post", "remake_linkedin_post"))
    def handle_make_linkedin_post(self):
        # if post has been made, show the old one to the ai and ask it to improve, else
        # just ask to create.
        print("Making linkedin post...")

    @listen(handle_make_blog)
    def check_seo(self):
        print("Checking Blog SEO")

    @listen(or_(handle_make_tweet, handle_make_linkedin_post))
    def check_virality(self):
        print("Checking virality...")

    @router(or_(check_seo, check_virality))
    def score_router(self):

        content_type = self.state.content_type
        score = self.state.score

        if score >= 8:
            return "check_passed"
        else:
            if content_type == "blog":
                return "remake_blog"
            elif content_type == "linkedin":
                return "remake_linkedin_post"
            else:
                return "remake_tweet"

    @listen("check_passed")
    def finalize_content(self):
        print("Finalizing content")


flow = ContentPipelineFlow()

# flow.kickoff(
#     inputs={
#         "content_type": "tweet",
#         "topic": "AI Dog Training",
#     },
# )


flow.plot()