# -*- coding: utf-8 -*-
from flask import Flask, request, jsonify
from flask_restful import Resource, Api
from flask_cors import CORS, cross_origin
import os
import sys
import urllib.request
import json
import openai
import boto3
import requests
import googletrans
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

import json

class EmotionAPI(Resource):
    def post(self):
        text_list = request.json.get('text')
        text = ' '.join(text_list)  # 리스트 요소들을 공백으로 연결하여 하나의 문자열로 변환
        json_text = json.loads(json.dumps(text))  # 'text' 변수를 JSON 문자열로 변환
        print(json_text)
        print('Calling DetectSentiment')
        result = comprehend.detect_sentiment(Text=json_text, LanguageCode='en')
        decoded_result = json.dumps(result)  # 결과를 JSON 형식으로 변환하여 디코딩
        print(json.dumps(decoded_result, ensure_ascii=False, sort_keys=True, indent=4))  # 한글 표시를 위해 ensure_ascii=False 설정
        print("End of DetectSentiment\n")

        # 결과를 클라이언트에게 반환합니다.
        return {'result': decoded_result}




class GptAPI(Resource):
    def post(self):
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="center_num, center_detail_state, center_detail_city, center_detail_name, center_detail_classification, center_detail_centeropen, center_detail_officenumber, center_detail_address, center_detail_phone, center_detail_fax, center_detail_roomcount, center_detail_roomsize, center_detail_playgroundcount, center_detail_teachercount, center_detail_regularperson, center_detail_currentperson, center_detail_Latitude, center_detail_longitude, center_detail_vehicle, center_detail_hompage, center_detail_establish','16', '서울특별시', '종로구', '구기어린이집', '민간', '정상', '3012', '서울특별시 종로구 진흥로22길 8-1 (구기동)', '02-391-7072', '02-391-7071', '6', '88', '0', '9', '33', '23', '37.60668049186278', '126.95830100591703', '운영', '', '2013-09-02','20', '서울특별시', '종로구', '다솔 방과후교실', '민간', '정상', '3180', '서울특별시 종로구 통일로8길 16 (송월동)', '02-722-5011', '02-722-5011', '3', '408', '0', '7', '39', '38', '37.56926643', '126.9654484', '운영', '', '2006-03-13', '어린이집에 대한 주어진 정보들로 다음 어린이집중에 장점이 많아 보이는 어린이집의 name을 무조건 정해서 무조건 작은 따옴표 안에 name의 정보를 전부 담아서 다른 부연설명 하지말고 한 단어로 말해줘 ",
            temperature=1,
            max_tokens=2000,
        )
        answer = response['choices'][0]['text']
        return {'answer': answer}

class PapagomealengAPI(Resource):
    def post(self):
        source_text = request.json['exceptmeal'] + """3가지 식사인 ( 1.아침, 2.점심, 3.저녁 ) 추천해줘. 그리고 어린아이들에게 좋은 영양소들을 포함할 수있게 추천해줘. 그리고 건강에 어떻게 좋은지 알려줘"""
        print(f"{source_text}")
        enc_text = urllib.parse.quote(source_text)
        data = f"source=ko&target=en&text={enc_text}"
        url = "https://openapi.naver.com/v1/papago/n2mt"
        
        api_request = urllib.request.Request(url)
        api_request.add_header("X-Naver-Client-Id", naverclient_id)
        api_request.add_header("X-Naver-Client-Secret", naverclient_secret)

        try:
            response = urllib.request.urlopen(api_request, data=data.encode("utf-8"))
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code}")
            return {"error": "HTTP Error"}, e.code
        except urllib.error.URLError as e:
            print(f"URL Error: {e.reason}")
            return {"error": "URL Error"}, 500
        
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            result = response_body.decode('utf-8')
            print(result)
            # GptmealAPI에 POST 요청 보내기
            gptmeal_url = "http://localhost:5000/gptmealAPI"
            gptmeal_response = requests.post(gptmeal_url, json={'translatedText': result})
            gptmeal_json = gptmeal_response.json()
            # print(gptmeal_response.raise_for_status())
            PapagomealkorAPI_url = "http://localhost:5000/gptmealkorAPI"
            PapagomealkorAPI_response = requests.post(PapagomealkorAPI_url, json={'translatedText': gptmeal_json})
            lastresult = PapagomealkorAPI_response.json()  # <-- Call .json() method here
            return {"result": lastresult}, 200
        else:
            print("Error Code: {rescode}")
            return {"error": "API Error"}, rescode


class GptmealAPI(Resource):
    def post(self):
        data = request.get_json()
        prompt = data['translatedText']
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=1,
            max_tokens=2000,
        )
        answer = response['choices'][0]['text']
        print(f"answer: {answer}")
        return {'answer': answer}
    
class PapagomealkorAPI(Resource):
    def post(self):
        mealdata = request.get_json()
        kor_Text = json.dumps(mealdata)
        mealdata = f"source=en&target=ko&text={kor_Text}"
        url = "https://openapi.naver.com/v1/papago/n2mt"
        req = urllib.request.Request(url)
        req.add_header("X-Naver-Client-Id", naverclient_id)
        req.add_header("X-Naver-Client-Secret", naverclient_secret)
        response = urllib.request.urlopen(req, data=mealdata.encode("utf-8"))
        rescode = response.getcode()
        if rescode == 200:
            response_body = response.read()
            translated_text = json.loads(response_body.decode('utf-8'))['message']['result']['translatedText']
            print(translated_text)
            return {'translatedText': translated_text}, 200
        else:
            print("Error Code:" + rescode)
            return {'error': 'API Error'}, rescode


class NaverAPI(Resource):
    def post(self):
        # 검색어 입력
        query = request.json.get('centerName')
        print(query)

        # 검색 API 요청 URL 설정
        encText = urllib.parse.quote(query)
        url = "https://openapi.naver.com/v1/search/cafearticle?query=" + encText

        # API 요청 헤더 설정
        request_obj = urllib.request.Request(url)
        request_obj.add_header("X-Naver-Client-Id", naverclient_id)
        request_obj.add_header("X-Naver-Client-Secret", naverclient_secret)

        try:
            # API 요청 및 응답 처리
            response = urllib.request.urlopen(request_obj)
            rescode = response.getcode()

            if rescode == 200:
                response_body = response.read()
                result = json.loads(response_body.decode('utf-8'))

                # EmotionAPI 호출
                descriptions = [item['description'] for item in result['items']]
                # print(descriptions)
                response = requests.post('http://localhost:5000/emotionApi', json={'text': descriptions})
                print(response)
                response.raise_for_status()
                result = response.json()

                return result
            else:
                return {"message": "Error Code:" + rescode}, rescode
        except Exception as e:
            return {"message": str(e)}, 500

        

# class googlemealAPI(Resource):
#     def post(self):
#         translator = googletrans.Translator()
#         inStr = request.json['exceptmeal'] + """3가지 식사인 ( 1.아침, 2.점심, 3.저녁 ) 추천해줘. 그리고 어린아이들에게 좋은 영양소들을 포함할 수있게 추천해줘. 그리고 건강에 어떻게 좋은지 알려줘"""
#         outStr = translator.translate(inStr, dest='en', src='auto')
#         print(f"{inStr} => {outStr.text}")
#         # GptmealAPI에 POST 요청 보내기
#         gptmeal_url = "http://localhost:5000/gptmealAPI"
#         gptmeal_response = requests.post(gptmeal_url, json={'translatedText': outStr.text})
#         lastoutStr = translator.translate(gptmeal_response.text, dest='ko', src='auto')
#         gptmeal_json = {'translatedText': lastoutStr.text}
#         print(gptmeal_json)
#         return jsonify({"result": gptmeal_json})

class kinderrecommendAPI(Resource):
    def post(self):
        translator = googletrans.Translator()
        # state.testData의 요소들을 instr 문자열에 추가
        inStr = str(request.json['favorgptlist']) + """다음과 같은 어린이집 또는 유치원들에 대한 정보들이 있다. 이중에 제일 좋아보이는 어린이집을 추천해주고 왜 그런지 이유를 알려줘"""
        if inStr is not None and len(inStr) > 0:
            outStr = translator.translate(inStr, dest='en', src='auto')
            print(f"{inStr} => {outStr.text}")
            # GptmealAPI에 POST 요청 보내기
            gptmeal_url = "http://localhost:5000/gptmealAPI"
            # gptmeal_response = requests.post(gptmeal_url, json={'translatedText': inStr.text})
            gptmeal_response = requests.post(gptmeal_url, json={'translatedText': outStr.text})
            lastoutStr = translator.translate(gptmeal_response.text, dest='ko', src='auto')
            gptmeal_json = {'translatedText': lastoutStr.text}
            print(gptmeal_json)
            return jsonify({"result": gptmeal_json})
        else:
            print("ㅠㅠ")

    
class kinderemotionAPI(Resource):
    def post(self):
        translator = googletrans.Translator()
        inStr =  """ 명품 광명 편한세상센트레빌 행복        안녕하세요 내년 이사를 앞두고 어린이집을 옮겨야하는데 정보가 부족해 입주민분들께 문의드려요 시립구름산어린이집이랑 시립하안누리어린이집 어떤가요 구름산은 가까운데 가는길이 언덕이고 하안누리는 은근         시립 구름산어린이집 하안누리 어린이집 어떤가요           나눔카페 구광명맘대디 광명시광        년 월생이구요 년 월에 보낸다 치면 희망이 있을까요ㅠㅠ 시립구름산어린이집 대기하려구 생각 중이에요 ㅠ        국공립 어린이집 대기자 인데요 희망있을까요           나눔카페 구광명맘대디 광명시광        저는 가깝고 시립이니까 원비가 저렴할 것이다 그리고 시립이니까 안전할 것같다 이정도 수준으로만 느끼고 있는데 실제 보내고 계신 맘님들의 소견 듣고싶어요 철산동 은총유치원 옆에 있는 곳이요 시립구름산어린이집        시립구름산어린이집 보냐시는 맘님들께 여쭤요           나눔카페 구광명맘대디 광명시광        도덕파크 언덕에 있는 구름산어린이집이요 몇살부터 보육하는지 아시는분 계실까요 세부터라고 생각했는데 오늘 친구랑 얘기하다보니 아닐수도 있다고  갑자기 궁금해져서 문의드려요        시립구름산어린이집           나눔카페 구광명맘대디 광명시광        만세세는 낮잠 자나요 학기만 잔다던지학기만 잔다던지 전화문의드려보기전에 궁금해서 글올려보아요        시립구름산어린이집도덕파크 낮잠여부           나눔카페 구광명맘대디 광명시광        시립구름산어린이집 보내시는 분 있으신가요 제 주위에 보낸분이 없어서 평이 어떤지 잘 모르겠네요 ㅠㅠ        시립구름산어린이집 어떤가요           나눔카페 구광명맘대디 광명시광        민간에서 옮기려해요 시립이라 특별활동이 코로나 이후 없나요 당연히 시립이라 믿고 보내는게 맞다여겼는데 평가인증이던데 그 이유를 아시는분 계실까요 그냥 엄마입장에서 보내시기 어떤지 궁금해요 사소한것도         시립구름산어린이집도덕파크옆 어떤가요           나눔카페 구광명맘대디 광명시광        혹시 다녔던 선배맘님 어린이집 정보 부탁드려요 집에서 그나마 가까워서 오래전에 신청했는데 입소가능하다는 연락 받았는데 정보가 너무 없네요 ㅜㅜ 시설 선생님 교육프로그램식사 차량 등등 아무거나 말씀해주세용        시립구름산어린이집           나눔카페 구광명맘대디 광명시광        시립구름산어린이집 하안동 원복 구해여 연락부탁드릴께여 혹시 이편한세상센트레빌에서 세 다니는 아이혹시 있나여 같이다니는 친구가 있었으면하는데 있다면 꼭 연락부탁드립니다        시립구름산어린이집 하안동 원복 가방 구해여           나눔카페 구광명맘대디 광명시광        거래완료한 회원의 닉네임을 제목이나 본문에 수정해서 남겨주세요 시립푸른어린이집 가방 체육복 드림합니다 체육복 사이즈는 호 입니다 저희 아이 세때 입혔던 사이즈네요 댓글 주세요 문고리 드림합니다        시립푸른어린이집 가방체육복세 
다음 글들에서 긍정적인 부분과 부정적인 단어들을 나눠서 알려주고 각각의 퍼센트가 어떻게 될지 나타내줘. 그리고 종합해서 총 감정이 긍정적 또는 부정적으로 표현하고있는지 알려줘
"""
        outStr = translator.translate(inStr, dest='en', src='auto')
        print(f"{inStr} => {outStr.text}")
        # GptmealAPI에 POST 요청 보내기
        gptmeal_url = "http://localhost:5000/gptmealAPI"
        gptmeal_response = requests.post(gptmeal_url, json={'translatedText': outStr.text})
        lastoutStr = translator.translate(gptmeal_response.text, dest='ko', src='auto')
        gptmeal_json = {'translatedText': lastoutStr.text}
        print(gptmeal_json)
        return jsonify({"result": gptmeal_json})
    
class googletransrateAPI(Resource):
    def post(self):
        translator = googletrans.Translator()
        inStr = """어린이집을 보내기 위해서 고려해야 할것들 자세하게 알려줘"""
        outStr = translator.translate(inStr, dest='en', src='auto')
        print(f"{inStr} => {outStr.text}")
        lastoutStr = translator.translate(outStr.text, dest='ko', src='auto')
        print(f"{outStr} => {lastoutStr.text}")
        googletransrate_json = {'translatedText': lastoutStr.text}
        print(googletransrate_json)
        return jsonify({"result": googletransrate_json})
        

class kinderresourceAPI(Resource):
    def post(self):
        translator = googletrans.Translator()
        inStr =  """ 어린이집을 보내기 위해서 고려해야 할것들 자세하게 알려줘"""
        outStr = translator.translate(inStr, dest='en', src='auto')
        print(f"{inStr} => {outStr.text}")
        # GptmealAPI에 POST 요청 보내기
        gptmeal_url = "http://localhost:5000/gptmealAPI"
        gptmeal_response = requests.post(gptmeal_url, json={'translatedText': outStr.text})
        lastoutStr = translator.translate(gptmeal_response.text, dest='ko', src='auto')
        gptmeal_json = {'translatedText': lastoutStr.text}
        print(gptmeal_json)
        return jsonify({"result": gptmeal_json})

       

api.add_resource(EmotionAPI, '/emotionApi')
api.add_resource(GptAPI, '/gptApi')
api.add_resource(NaverAPI, '/naverApi')
api.add_resource(PapagomealengAPI, '/gptmeal2API')
api.add_resource(PapagomealkorAPI, '/gptmealkorAPI')
api.add_resource(GptmealAPI, '/gptmealAPI')
# api.add_resource(googlemealAPI, '/googlemealAPI')
api.add_resource(googletransrateAPI, '/googletransrateAPI')
api.add_resource(kinderrecommendAPI, '/kinderrecommendAPI')
api.add_resource(kinderemotionAPI, '/kinderemotionAPI')
api.add_resource(kinderresourceAPI, '/kinderresourceAPI')


if __name__ == '__main__':
    app.run(debug=True)
