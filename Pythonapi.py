# -*- coding: utf-8 -*-
from flask import Flask, request
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
import os
import sys
import urllib.request
import json
import openai
import boto3
import json
from config import gpt_api_key, aws_access_key_id, aws_secret_access_key, naverclient_id, naverclient_secret

openai.api_key = gpt_api_key

app = Flask('API')
api = Api(app)
CORS(app)

session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='ap-northeast-2'
)

# 네이버 API 인증 정보
naverclient_id = naverclient_id
naverclient_secret = naverclient_secret
        

comprehend = session.client('comprehend')

class EmotionAPI(Resource):
    def post(self):
        text = """안녕하세요, 내년, 이사, 어린이, 집, 옮겨야, 정보, 부족, 입주민, 문의, 시립, 구름산, 하안누리, 가까운, 언덕, 은근, 시립, 원비, 저렴, 안전, 수준, 느끼고, 실제, 보내고, 계신, 맘님, 소견, 철산, 동, 은총, 유치원, 옆, 곳, 만, 세, 낮잠, 자나, 전화, 문의, 가깝고, 원비가, 저렴할, 것이다, 그리고, 안전할, 것같다, 이정도, 수준으로만, 느끼고, 있는데, 실제, 보내고, 계신, 맘님들, 소견, 듣고싶어요, 철산, 동, 은총, 유치원, 옆, 곳, 시립, 구름산, 어린이집, 만, 세, 낮잠, 자나, 전화, 문의, 다녔던, 선배, 맘님, 어린이, 집, 정보, 부탁드려요, 집, 그나마, 가까워서, 오래전, 신청, 했는데, 입소, 가능하다는, 연락, 받았는데, 정보, 너무, 없네요, ㅜㅜ, 시설, 선생님, 교육, 프로그램, 식사, 차량, 등등, 아무거나, 말씀, 해주세요."""

        print('Calling DetectSentiment')
        result = comprehend.detect_sentiment(Text=text, LanguageCode='en')
        print(json.dumps(result, sort_keys=True, indent=4))
        print("End of DetectSentiment\n")

        # 결과를 클라이언트에게 반환합니다.
        return {'result': result}


class GptAPI(Resource):
    def post(self):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="center_num, center_detail_state, center_detail_city, center_detail_name, center_detail_classification, center_detail_centeropen, center_detail_officenumber, center_detail_address, center_detail_phone, center_detail_fax, center_detail_roomcount, center_detail_roomsize, center_detail_playgroundcount, center_detail_teachercount, center_detail_regularperson, center_detail_currentperson, center_detail_Latitude, center_detail_longitude, center_detail_vehicle, center_detail_hompage, center_detail_establish','16', '서울특별시', '종로구', '구기어린이집', '민간', '정상', '3012', '서울특별시 종로구 진흥로22길 8-1 (구기동)', '02-391-7072', '02-391-7071', '6', '88', '0', '9', '33', '23', '37.60668049186278', '126.95830100591703', '운영', '', '2013-09-02','20', '서울특별시', '종로구', '다솔 방과후교실', '민간', '정상', '3180', '서울특별시 종로구 통일로8길 16 (송월동)', '02-722-5011', '02-722-5011', '3', '408', '0', '7', '39', '38', '37.56926643', '126.9654484', '운영', '', '2006-03-13', '어린이집에 대한 주어진 정보들로 다음 어린이집중에 장점이 많아 보이는 어린이집의 name을 무조건 정해서 무조건 작은 따옴표 안에 name의 정보를 전부 담아서 다른 부연설명 하지말고 한 단어로 말해줘 ",
            temperature=0,
            max_tokens=50,
        )
        answer = response['choices'][0]['text']
        return {'answer': answer}


class NaverAPI(Resource):
    def post(self):

        # 검색어 입력
        query = "\"시립구름산어린이집\""

        # 검색 API 요청 URL 설정
        encText = urllib.parse.quote(query)
        url = "https://openapi.naver.com/v1/search/cafearticle?query=" + encText

        # API 요청 헤더 설정
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", naverclient_id)
        request.add_header("X-Naver-Client-Secret", naverclient_secret)

        try:
            # API 요청 및 응답 처리
            response = urllib.request.urlopen(request)
            rescode = response.getcode()

            if rescode == 200:
                response_body = response.read()
                result = json.loads(response_body.decode('utf-8'))
                return result
            else:
                return {"message": "Error Code:" + rescode}, rescode
        except Exception as e:
            return {"message": str(e)}, 500
        
api.add_resource(EmotionAPI, '/emotionApi')
api.add_resource(GptAPI, '/gptApi')
api.add_resource(NaverAPI, '/naverApi')

if __name__ == '__main__':
    app.run(debug=True)
