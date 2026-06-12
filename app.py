import streamlit as st
import google.generativeai as genai

# 1. 웹페이지 기본 설정
st.set_page_config(
    page_title="대학생 전용 학업 보조 AI",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 대학생을 위한 AI 학업 보조 파트너")
st.caption("낮은 수준의 질문을 자동으로 최적화하여 전문가 수준의 결과물을 도출합니다.")
st.write("---")

# 2. 사이드바 설정 (API 키 및 파라미터 제어)
st.sidebar.header("🔑 API 설정")
api_key = st.sidebar.text_input("Gemini API Key를 입력하세요", type="password")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.sidebar.warning("구동을 위해 Gemini API Key가 필요합니다.")

st.sidebar.write("---")
st.sidebar.header("🎛️ AI 최적화 설정")

# 페르소나 라이브러리 구성
persona = st.sidebar.selectbox(
    "가상 조교 페르소나 선택",
    ["A+ 레포트 조교 (인문/사회)", "디버깅 마스터 (공학/IT)", "통계 분석가 (상경/데이터)"]
)

persona_prompts = {
    "A+ 레포트 조교 (인문/사회)": "너는 대학 수석 졸업생이자 인문사회학 전공 조교야. 논리적 구조, 비판적 사고, 학술적 문체(예: ~라 할 수 있다, ~를 시사한다)를 사용하여 깊이 있는 비판적 분석을 제공하도록 프롬프트를 재구성해라.",
    "디버깅 마스터 (공학/IT)": "너는 시니어 소프트웨어 엔지니어이자 컴퓨터공학 조교야. 코드의 가독성, 시간 복잡도, 예외 처리 및 에지 케이스를 고려한 구조적인 답변을 유도하도록 프롬프트를 재구성해라.",
    "통계 분석가 (상경/데이터)": "너는 데이터 사이언티스트이자 통계학 조교야. 가설 설정, 통계적 유의성, 데이터 해석 방법론 및 수식적 근거를 포함하도록 분석적인 프롬프트를 재구성해라."
}

# 대학생 맞춤형 변수 라벨링
st.sidebar.subheader("매개변수 미세조정")
temp_label = st.sidebar.select_slider(
    "답변 성향 (Temperature)",
    options=["정밀함/팩트 중심", "균형 잡힌 답변", "창의적/아이디어 발산"],
    value="균형 잡힌 답변"
)

# 라벨을 실제 토큰 값으로 변환
temp_map = {"정밀함/팩트 중심": 0.2, "균형 잡힌 답변": 0.5, "창의적/아이디어 발산": 0.9}
temperature = temp_map[temp_label]

# 3. 메인 화면 UI
user_input = st.text_area(
    "질문이나 과제 주제를 입력하세요 (대충 적어도 AI가 확장합니다)",
    placeholder="예: 포스트모더니즘에 대해 설명해줘 / 리스트 정렬하는 파이썬 코드 짜줘",
    height=150
)

if st.button("🚀 전문가 모드로 AI에게 질문하기"):
    if not api_key:
        st.error("좌측 사이드바에 Gemini API Key를 입력해주세요.")
    elif not user_input.strip():
        st.warning("질문 내용을 입력해주세요.")
    else:
        # 결과 값을 임시 저장할 변수를 블록 밖에 미리 선언합니다.
        refined_prompt = ""
        final_text = ""
        success_flag = False
        
        # 1. 연산 및 API 호출 단계 (st.status 로딩 블록 안에서 진행)
        with st.status("AI가 질문을 분석하고 프롬프트를 엔지니어링하는 중...", expanded=True) as status:
            try:
                st.write("1단계: 사용자 질문 분석 및 프롬프트 확장 중...")
                refiner_model = genai.GenerativeModel('gemini-flash-latest')
                
                refine_instruction = f"""
                역할: 너는 전문 프롬프트 엔지니어다.
                목표: 사용자의 단순한 질문을 대학 과제 및 학업에 적합한 '전문가 수준의 구조화된 프롬프트'로 확장해라.
                반드시 반영할 페르소나 지침: {persona_prompts[persona]}
                주의사항: 다른 인사말이나 설명은 절대 하지 말고, 오직 확장된 최종 프롬프트 내용만 텍스트로 출력해라.
                """
                
                refined_response = refiner_model.generate_content(
                    f"{refine_instruction}\n\n사용자 원본 질문: {user_input}"
                )
                refined_prompt = refined_response.text
                
                st.write("2단계: 최종 답변 생성 레이어 호출 중...")
                final_model = genai.GenerativeModel('gemini-flash-latest')
                
                final_response = final_model.generate_content(
                    refined_prompt,
                    generation_config={"temperature": temperature}
                )
                final_text = final_response.text
                
                # 성공적으로 마쳤다면 상태를 완료로 변경
                status.update(label="최적화 및 답변 생성 완료!", state="complete", expanded=False)
                success_flag = True
                
            except Exception as e:
                status.update(label="오류 발생", state="error")
                st.error(f"에러가 발생했습니다: {e}")
        
        # 2. 결과 출력 단계 (★ st.status 블록 완전히 '바깥'에서 실행하여 중첩 에러 해결)
        if success_flag:
            st.success("✨ 전문가급 최적화 답변이 준비되었습니다.")
            
            # 인사이트 카드 출력 (중첩 에러가 나지 않음)
            with st.expander("📊 적용된 인사이트 카드 (프롬프트 자동 최적화 결과)", expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**활성화된 페르소나:** `{persona}`")
                with col2:
                    st.markdown(f"**적용된 수치(Temp):** `{temperature} ({temp_label})`")
                st.markdown("**자동 생성된 전문 프롬프트:**")
                st.info(refined_prompt)
            
            # 최종 학술 답변 출력
            st.write("---")
            st.markdown("### 📝 AI 가상 조교의 학술적 답변")
            st.markdown(final_text)