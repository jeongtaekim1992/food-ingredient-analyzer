from typing import List, Optional, Dict, Any, TypedDict
import json
import os
from dotenv import load_dotenv

from pydantic import BaseModel, Field
from PIL import Image
import google.generativeai as genai
import streamlit as st

# 환경 변수 로드
load_dotenv()

# API 키를 환경 변수 또는 Streamlit secrets에서 가져옴
try:
    # Streamlit Cloud에서 실행 중인 경우
    API_KEY = st.secrets["gemini"]["api_key"]
except Exception:
    # 로컬에서 실행 중인 경우
    API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyCp1fqnZlpcSFccZclPx5oyRrsxzG0ibPA")

genai.configure(api_key=API_KEY)

IMAGE_PATH = '/content/drive/MyDrive/ocr/ocr_test_img_ko.png'
MODEL_NAME = "gemini-2.0-flash"
INGREDIENTS_TEMPERATURE = 0.2
DESCRIPTION_TEMPERATURE = 0.7

class PersonaType(TypedDict):
    gender: str
    age: int
    health_issues: List[str]
    purpose: str

PERSONA: PersonaType = {
    "gender": "여성",
    "age": 60,
    "health_issues": ["당뇨", "고혈압"],
    "purpose": "건강한 식단 관리"
}

SYSTEM_INSTRUCTION = "당신은 이미지 OCR 및 NER 전문가입니다. 동시에 친절한 영양사입니다."

INGREDIENT_DESCRIPTION_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "재료명": {
                "type": "string",
                "description": "OCR을 통해 추출된 재료명"
            },
            "설명": {
                "type": "string",
                "description": "추출된 재료명에 대한 자세한 설명"
            }
        },
        "required": ["재료명", "설명"]
    }
}

HEALTH_TIPS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "재료명": {
                "type": "string",
                "description": "OCR을 통해 추출된 재료명"
            },
            "건강팁": {
                "type": "string",
                "description": "해당 재료의 건강상 이점과 주의사항"
            }
        },
        "required": ["재료명", "건강팁"]
    }
}

OVERALL_ASSESSMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "종합평가": {
            "type": "string",
            "description": "사용자 정보와 건강 이슈를 고려한 전체 식품 재료의 종합적인 평가"
        },
        "적합도": {
            "type": "string",
            "description": "이 식품이 사용자에게 전반적으로 얼마나 적합한지에 대한 점수와 평가 (최상/상/중/하/최하)"
        },
        "추가조언": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "카테고리": {
                        "type": "string",
                        "description": "조언 카테고리 (예: 식단 구성, 조리팁, 영양소, 생활 습관, 자가 모니터링, 식품 선택 등)"
                    },
                    "내용": {
                        "type": "string",
                        "description": "구체적인 조언 내용"
                    }
                },
                "required": ["카테고리", "내용"]
            }
        }
    },
    "required": ["종합평가", "적합도", "추가조언"]
}

ALTERNATIVES_SCHEMA = {
    "type": "object",
    "properties": {
        "alternatives": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "원재료": {
                        "type": "string",
                        "description": "OCR을 통해 추출된 원래 재료명"
                    },
                    "대체재료": {
                        "type": "string",
                        "description": "건강에 더 좋은 대체 재료 제안"
                    },
                    "대체이유": {
                        "type": "string",
                        "description": "이 대체 재료를 추천하는 건강상 이유"
                    }
                },
                "required": ["원재료", "대체재료", "대체이유"]
            }
        },
        "조리팁": {
            "type": "string",
            "description": "건강에 더 좋은 조리법 및 방법 제안"
        }
    },
    "required": ["alternatives", "조리팁"]
}

# 수정된 부분: OCRResult 클래스에 새로운 종합평가 필드 추가
class OCRResult(BaseModel):
    ingredients: List[str] = Field(description="추출된 식품 재료 목록")
    descriptions: Optional[Dict[str, str]] = Field(default=None, description="각 재료에 대한 설명")
    health_tips: Optional[Dict[str, str]] = Field(default=None, description="각 재료와 페르소나 간의 건강 궁합")
    overall_assessment: Optional[str] = Field(default=None, description="사용자와 음식 간의 궁합 총평")
    suitability: Optional[str] = Field(default=None, description="사용자에게 식품의 적합도")
    additional_advice: Optional[List[Dict[str, str]]] = Field(default=None, description="카테고리별 추가 조언")
    alternatives: Optional[List[Dict[str, str]]] = Field(default=None, description="건강에 더 좋은 대체 재료 제안")
    cooking_tips: Optional[str] = Field(default=None, description="건강에 더 좋은 조리법 제안")

def setup_persona():
    persona_prompt = f"사용자 정보: ({PERSONA['age']}세, {PERSONA['gender']}), 건강 이슈: {', '.join(PERSONA['health_issues'])}, 목적: {PERSONA['purpose']}"
    return persona_prompt

def setup_gemini_model():
    return genai.GenerativeModel(
        MODEL_NAME,
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=genai.GenerationConfig(temperature=INGREDIENTS_TEMPERATURE)
    )

def parse_ingredients(text: str) -> OCRResult:
    ingredients = [ingredient for ingredient in text.split('^')]
    print("첫 번째 질문 정규화 :", ingredients)
    print("-"*100)
    return OCRResult(ingredients=ingredients)

def parse_json_items(items: List[Dict[str, Any]], key_name: str) -> Dict[str, str]:
    result_dict = {}

    for item in items:
        item_name = item.get("재료명", "")
        item_value = item.get(key_name, "")
        result_dict[item_name] = item_value

    return result_dict


def analyze_food_ingredients(image_path=IMAGE_PATH):
    image = Image.open(image_path)
    model = setup_gemini_model()
    persona_prompt = setup_persona()

    # 첫 번째 쿼리 (시스템 인스트럭션 포함)
    system_prompt = f"{SYSTEM_INSTRUCTION}\n\n{persona_prompt}"
    ingredient_query = {
        "parts": [system_prompt + "\n\n이미지에서 식품에 들어간 재료를 정확히 추출해서 '^'로 구분하여 나열해주세요. 단, 식재료 영역에 감지된 객체만 보여주세요. 다른 영역은 필요없습니다. 다른 답변도 필요하지마세요.",
                 image]
    }

    history = []

    query_with_role = {'role': 'user', 'parts': ingredient_query['parts']}
    history.append(query_with_role)
    print("첫 번째 질문 누적 :", history)
    print("-"*100)

    ingredient_response = model.generate_content(history)
    history.append({'role': 'model', 'parts': [ingredient_response.text]})
    print("첫 질문 응답 누적 :", history)
    print("-"*100)

    result = parse_ingredients(ingredient_response.text)
    print("첫 질문 응답 구조화 :", result)
    print("-"*100)

    # 두 번째 쿼리
    description_query = {
        "parts": [f"다음 식품 재료에 대해 설명해주세요: {', '.join(result.ingredients)}. 다른 답변은 필요없습니다."]
    }

    query_with_role = {'role': 'user', 'parts': description_query['parts']}
    history.append(query_with_role)
    print("두 번째 질문 누적 :", history)
    print("-"*100)

    description_response = model.generate_content(
        history,
        generation_config=genai.GenerationConfig(
            temperature=DESCRIPTION_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=INGREDIENT_DESCRIPTION_SCHEMA
        )
    )

    history.append({'role': 'model', 'parts': [description_response.text]})
    print("두 번째 응답 누적 :", history)
    print("-"*100)

    description_data = json.loads(description_response.text)
    print("두 번째 응답 정규화 : ", description_data)
    print("-"*100)

    descriptions = parse_json_items(description_data, "설명")
    result.descriptions = descriptions
    print("두 번째 응답 구조화 :", result)
    print("-"*100)

    # 세 번째 쿼리
    health_tips_query = {
        "parts": [f"{persona_prompt}을 참고하여 다음 재료들({', '.join(result.ingredients)})의 건강상 이점과 주의사항에 대해 조언해주세요. 다른 답변은 필요없습니다."]
    }

    query_with_role = {'role': 'user', 'parts': health_tips_query['parts']}
    history.append(query_with_role)
    print("세 번째 질문 누적 : ", history)
    print("-"*100)

    health_tips_response = model.generate_content(
        history,
        generation_config=genai.GenerationConfig(
            temperature=DESCRIPTION_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=HEALTH_TIPS_SCHEMA
        )
    )

    history.append({'role': 'model', 'parts': [health_tips_response.text]})
    print("세 번째 응답 누적 : ", history)
    print("-"*100)

    health_tips_data = json.loads(health_tips_response.text)
    print("세 번째 응답 정규화 : ", health_tips_data)
    print("-"*100)

    health_tips = parse_json_items(health_tips_data, "건강팁")
    result.health_tips = health_tips
    print("세 번째 응답 구조화 : ", result)
    print("-"*100)

    # 네 번째 쿼리
    overall_assessment_query = {
        "parts": [f"{persona_prompt}을 고려해서, 지금까지 분석한 모든 재료({', '.join(result.ingredients)})를 종합적으로 평가해주세요. 이 식품이 사용자에게 전반적으로 얼마나 적합한지, 추가 조언도 해주세요."]
    }

    query_with_role = {'role': 'user', 'parts': overall_assessment_query['parts']}
    history.append(query_with_role)
    print("네 번째 질문 누적 : ", history)
    print("-"*100)

    overall_assessment_response = model.generate_content(
        history,
        generation_config=genai.GenerationConfig(
            temperature=DESCRIPTION_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=OVERALL_ASSESSMENT_SCHEMA
        )
    )

    history.append({'role': 'model', 'parts': [overall_assessment_response.text]})
    print("네 번째 응답 누적 : ", history)
    print("-"*100)

    overall_assessment_data = json.loads(overall_assessment_response.text)
    print("네 번째 응답 정규화 : ", overall_assessment_data)
    print("-"*100)

    result.overall_assessment = overall_assessment_data.get("종합평가", "")
    result.suitability = overall_assessment_data.get("적합도", "")
    result.additional_advice = overall_assessment_data.get("추가조언", [])
    print("네 번째 응답 구조화 : ", result)
    print("-"*100)

    #  다섯 번째 쿼리
    alternatives_query = {
        "parts": [f"{persona_prompt}을 고려하여, 분석한 재료들({', '.join(result.ingredients)}) 중 건강에 더 좋은 대체 재료와 조리법을 추천해주세요."]
    }

    query_with_role = {'role': 'user', 'parts': alternatives_query['parts']}
    history.append(query_with_role)
    print("다섯 번째 질문 누적 : ", history)
    print("-"*100)

    alternatives_response = model.generate_content(
        history,
        generation_config=genai.GenerationConfig(
            temperature=DESCRIPTION_TEMPERATURE,
            response_mime_type="application/json",
            response_schema=ALTERNATIVES_SCHEMA
        )
    )

    history.append({'role': 'model', 'parts': [alternatives_response.text]})
    print("다섯 번째 응답 누적 : ", history)
    print("-"*100)

    alternatives_data = json.loads(alternatives_response.text)
    print("다섯 번째 응답 정규화 : ", alternatives_data)
    print("-"*100)

    result.alternatives = alternatives_data.get("alternatives", [])
    result.cooking_tips = alternatives_data.get("조리팁", "")
    print("다섯 번째 응답 구조화 : ", result)
    print("-"*100)

    return result



