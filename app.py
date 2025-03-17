import streamlit as st
import main
from PIL import Image
import os
import json

st.set_page_config(layout="wide", page_title="식품 재료 분석기")


st.title("식품 재료 분석기")

# 컬럼 분할
col1, col2 = st.columns(2)

with col1:
    st.subheader("입력")

    image_path1 = "ocr_test_img_01.png"  # 첫 번째 이미지 경로
    image_path2 = "ocr_test_img_02.png"  # 두 번째 이미지 경로
    
    # 이미지 선택 라디오 버튼
    selected_image = st.radio(
        "이미지 선택",
        ["이미지 1", "이미지 2"],
        horizontal=True
    )
    
    # 선택된 이미지 경로 설정
    if selected_image == "이미지 1":
        image_path = image_path1
        if os.path.exists(image_path):
            st.image(image_path, width=300)
        else:
            st.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
    else:
        image_path = image_path2
        if os.path.exists(image_path):
            st.image(image_path, width=500)
        else:
            st.error(f"이미지 파일이 존재하지 않습니다: {image_path}")
    
    # Persona 설정
    st.subheader("사용자 정보")
    
    # 성별 선택 - 기본값 없이 "선택해주세요" 옵션 추가
    gender = st.selectbox(
        "성별", 
        ["선택해주세요", "여성", "남성"],
        index=0  # 첫 번째 옵션("선택해주세요")을 기본값으로 설정
    )
    
    # 나이 입력 - 기본값 없이 빈 값으로 시작
    age = st.number_input(
        "나이", 
        min_value=0, 
        max_value=100, 
        value=0,  # 0으로 시작하여 사용자가 직접 입력하도록 유도
        help="나이를 입력해주세요"
    )
    
    # 건강 이슈 - multiselect로 변경
    health_issues = st.multiselect(
        "건강 이슈",
        [
            "당뇨", 
            "고혈압", 
            "비만", 
            "심장병", 
            "뇌졸중", 
            "간 질환", 
            "신장 질환", 
            "식품 알레르기", 
            "유당 불내증", 
            "글루텐 불내증", 
            "통풍"
        ],
        default=[],
        help="해당하는 건강 이슈를 모두 선택해주세요 (여러 개 선택 가능)"
    )
    

    
    # 목적 - multiselect 박스로 변경
    purpose = st.multiselect(
        "목적",
        [
            "체중 관리", 
            "영양 균형", 
            "알레르기 확인", 
            "건강 증진", 
            "식단 다양화", 
            "특정 영양소 섭취", 
            "식품 첨가물 확인", 
            "식이 제한 준수", 
            "질병 관리", 
            "운동 성능 향상"
        ],
        default=[],
        help="식품 분석 목적을 선택해주세요 (여러 개 선택 가능)"
    )
    

with col2:
    st.subheader("출력")
    
    # 분석 시작 버튼을 col2로 이동
    analyze_button = st.button("분석 시작")
    
    # 기본 출력 구조 텍스트
    default_output = """📋 식품 재료 분석 결과 📋

🔍 추출된 재료:
1. 재료1
2. 재료2
...

📚 재료 설명:
1. 재료1: 설명
2. 재료2: 설명
...

💊 건강 팁:
1. 재료1: 건강 팁
2. 재료2: 건강 팁
...

🧐 종합 평가:
전체적인 평가 내용

⭐ 적합도:
적합도 평가 내용

💡 추가 조언:
1. [카테고리] 조언 내용
2. [카테고리] 조언 내용
...

🔄 대체 재료 제안:
1. 원재료 → 대체재료
   이유: 대체 이유
...

👨‍🍳 조리 팁:
조리 팁 내용
    """
    
    # 분석 결과를 저장할 변수 초기화
    result_text = default_output
    
    # 입력 검증
    input_valid = True
    error_message = ""
    
    if analyze_button:
        # 입력값 검증
        if gender == "선택해주세요":
            input_valid = False
            error_message += "성별을 선택해주세요. "
        
        if age == 0:
            input_valid = False
            error_message += "나이를 입력해주세요. "
        
        if not health_issues:
            input_valid = False
            error_message += "건강 이슈를 하나 이상 선택해주세요. "
        
        if not purpose:
            input_valid = False
            error_message += "목적을 입력해주세요. "
        
        if not os.path.exists(image_path):
            input_valid = False
            error_message += "이미지 파일이 존재하지 않습니다. "
        
        # 입력이 유효하지 않으면 오류 메시지 표시
        if not input_valid:
            st.error(error_message)
        # 입력이 유효하면 분석 실행
        elif os.path.exists(image_path):
            # Persona 업데이트
            main.PERSONA.update({
                "gender": gender,
                "age": age,
                "health_issues": health_issues,
                "purpose": purpose
            })
            
            # 진행 상황 표시를 위한 상태 컴포넌트
            progress_bar = st.progress(0)
            status_text = st.empty()
            result_container = st.empty()
            
            # 초기 결과 텍스트
            current_result = "📋 식품 재료 분석 결과 📋\n\n"
            result_container.text_area("", value=current_result, height=700, disabled=True)
            
            # 이미지 분석 실행 - 단계별로 진행
            status_text.text("이미지에서 재료를 추출하는 중...")
            
            # 1단계: 재료 추출
            image = Image.open(image_path)
            model = main.setup_gemini_model()
            persona_prompt = main.setup_persona()
            
            system_prompt = f"{main.SYSTEM_INSTRUCTION}\n\n{persona_prompt}"
            ingredient_query = {
                "parts": [system_prompt + "\n\n이미지에서 식품에 들어간 재료를 정확히 추출해서 '^'로 구분하여 나열해주세요. 단, 식재료 영역에 감지된 객체만 보여주세요. 다른 영역은 필요없습니다. 다른 답변도 필요하지마세요.",
                         image]
            }
            
            history = []
            query_with_role = {'role': 'user', 'parts': ingredient_query['parts']}
            history.append(query_with_role)
            
            ingredient_response = model.generate_content(history)
            history.append({'role': 'model', 'parts': [ingredient_response.text]})
            
            result = main.parse_ingredients(ingredient_response.text)
            
            # 재료 추출 결과 표시
            current_result += "🔍 추출된 재료:\n"
            for idx, ingredient in enumerate(result.ingredients, 1):
                current_result += f"{idx}. {ingredient}\n"
            current_result += "\n"
            
            result_container.text_area("", value=current_result, height=700, disabled=True)
            progress_bar.progress(25)
            
            # 2단계: 재료 설명
            status_text.text("재료에 대한 설명을 생성하는 중...")
            
            description_query = {
                "parts": [f"다음 식품 재료에 대해 설명해주세요: {', '.join(result.ingredients)}. 다른 답변은 필요없습니다."]
            }
            
            query_with_role = {'role': 'user', 'parts': description_query['parts']}
            history.append(query_with_role)
            
            description_response = model.generate_content(
                history,
                generation_config=main.genai.GenerationConfig(
                    temperature=main.DESCRIPTION_TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=main.INGREDIENT_DESCRIPTION_SCHEMA
                )
            )
            
            history.append({'role': 'model', 'parts': [description_response.text]})
            description_data = json.loads(description_response.text)
            descriptions = main.parse_json_items(description_data, "설명")
            result.descriptions = descriptions
            
            # 재료 설명 결과 표시
            current_result += "📚 재료 설명:\n"
            for idx, (ingredient, description) in enumerate(result.descriptions.items(), 1):
                current_result += f"{idx}. {ingredient}: {description}\n"
            current_result += "\n"
            
            result_container.text_area("", value=current_result, height=700, disabled=True)
            progress_bar.progress(50)
            
            # 3단계: 건강 팁
            status_text.text("건강 팁을 생성하는 중...")
            
            health_tips_query = {
                "parts": [f"{persona_prompt}을 참고하여 다음 재료들({', '.join(result.ingredients)})의 건강상 이점과 주의사항에 대해 조언해주세요. 다른 답변은 필요없습니다."]
            }
            
            query_with_role = {'role': 'user', 'parts': health_tips_query['parts']}
            history.append(query_with_role)
            
            health_tips_response = model.generate_content(
                history,
                generation_config=main.genai.GenerationConfig(
                    temperature=main.DESCRIPTION_TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=main.HEALTH_TIPS_SCHEMA
                )
            )
            
            history.append({'role': 'model', 'parts': [health_tips_response.text]})
            health_tips_data = json.loads(health_tips_response.text)
            health_tips = main.parse_json_items(health_tips_data, "건강팁")
            result.health_tips = health_tips
            
            # 건강 팁 결과 표시
            current_result += "💊 건강 팁:\n"
            for idx, (ingredient, tip) in enumerate(result.health_tips.items(), 1):
                current_result += f"{idx}. {ingredient}: {tip}\n"
            current_result += "\n"
            
            result_container.text_area("", value=current_result, height=700, disabled=True)
            progress_bar.progress(75)
            
            # 4단계: 종합 평가 및 나머지 분석
            status_text.text("종합 평가 및 추가 정보를 생성하는 중...")
            
            # 나머지 분석 과정 실행 (main.py의 나머지 부분)
            # 여기서는 main.py의 나머지 분석 과정을 호출하는 대신 직접 구현
            
            # 종합 평가 쿼리
            overall_query = {
                "parts": [f"{persona_prompt}을 참고하여 다음 재료들({', '.join(result.ingredients)})에 대한 종합적인 평가와 적합도, 추가 조언을 제공해주세요."]
            }
            
            query_with_role = {'role': 'user', 'parts': overall_query['parts']}
            history.append(query_with_role)
            
            overall_response = model.generate_content(
                history,
                generation_config=main.genai.GenerationConfig(
                    temperature=main.DESCRIPTION_TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=main.OVERALL_ASSESSMENT_SCHEMA
                )
            )
            
            history.append({'role': 'model', 'parts': [overall_response.text]})
            overall_data = json.loads(overall_response.text)
            
            result.overall_assessment = overall_data.get("종합평가", "")
            result.suitability = overall_data.get("적합도", "")
            result.additional_advice = overall_data.get("추가조언", [])
            
            # 종합 평가 결과 표시
            if result.overall_assessment:
                current_result += "🧐 종합 평가:\n"
                current_result += f"{result.overall_assessment}\n\n"
            
            if result.suitability:
                current_result += "⭐ 적합도:\n"
                current_result += f"{result.suitability}\n\n"
            
            if result.additional_advice:
                current_result += "💡 추가 조언:\n"
                for idx, advice in enumerate(result.additional_advice, 1):
                    current_result += f"{idx}. [{advice['카테고리']}] {advice['내용']}\n"
                current_result += "\n"
            
            result_container.text_area("", value=current_result, height=700, disabled=True)
            progress_bar.progress(90)
            
            # 5단계: 대체 재료 및 조리 팁
            status_text.text("대체 재료 및 조리 팁을 생성하는 중...")
            
            alternatives_query = {
                "parts": [f"{persona_prompt}을 참고하여 다음 재료들({', '.join(result.ingredients)})의 건강에 더 좋은 대체 재료와 조리 팁을 제안해주세요."]
            }
            
            query_with_role = {'role': 'user', 'parts': alternatives_query['parts']}
            history.append(query_with_role)
            
            alternatives_response = model.generate_content(
                history,
                generation_config=main.genai.GenerationConfig(
                    temperature=main.DESCRIPTION_TEMPERATURE,
                    response_mime_type="application/json",
                    response_schema=main.ALTERNATIVES_SCHEMA
                )
            )
            
            history.append({'role': 'model', 'parts': [alternatives_response.text]})
            alternatives_data = json.loads(alternatives_response.text)
            
            result.alternatives = alternatives_data.get("alternatives", [])
            result.cooking_tips = alternatives_data.get("조리팁", "")
            
            # 대체 재료 및 조리 팁 결과 표시
            if result.alternatives:
                current_result += "🔄 대체 재료 제안:\n"
                for idx, alt in enumerate(result.alternatives, 1):
                    current_result += f"{idx}. {alt['원재료']} → {alt['대체재료']}\n"
                    current_result += f"   이유: {alt['대체이유']}\n"
                current_result += "\n"
            
            if result.cooking_tips:
                current_result += "👨‍🍳 조리 팁:\n"
                current_result += f"{result.cooking_tips}\n"
            
            # 최종 결과 표시
            result_container.text_area("", value=current_result, height=700, disabled=True)
            progress_bar.progress(100)
            status_text.text("분석이 완료되었습니다!")
            
            # 최종 결과 저장
            result_text = current_result
    
    # 출력 구조를 담을 텍스트 박스 추가 (분석 버튼을 누르지 않았을 때만 표시)
    if not analyze_button:
        output_structure = st.text_area(
            "",
            value=result_text,
            height=600,
            disabled=True
        ) 