# and, or에 _를 붙여야하는것에 주의
from crewai.flow.flow import Flow, listen, start, router, and_, or_
from pydantic import BaseModel

#타입 지정
class MyFirstFlowState(BaseModel):

    user_id: int = 1
    is_admin: bool = False

class MyFirstFlow(Flow[MyFirstFlowState]) :

    #first가 가장 먼저 실행
    @start()
    def first(self):
        #flow에 데이터 저장
        self.state.user_id = 1
        print('Hello')

    #first가 종료되면 아래 두개가 실행
    @listen(first)
    def second(self):
        self.state.user_id = 2
        print('world')

    @listen(first)
    def third(self):
        print("!")

    #second와 third가 종료되면 실행, 하나만 끝나도 실행되길 원한다면 or사용
    @listen(and_(second,third))
    def final(self):
        print(":)")

    @router(final)
    def route(self):
        if self.state.is_admin:
            return "even"
        else:
            return "odd"
    
    @listen("even")
    def handle_even(self):
        print("even")

    @listen("odd")
    def handle_odd(self):
        print("odd")

flow = MyFirstFlow()
flow.plot()
flow.kickoff()