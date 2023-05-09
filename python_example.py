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

# CORS 설정
app = Flask('API')
api = Api(app)
CORS(app)

# GPT KEY
openai.api_key = gpt_api_key

# 아마존 KEY
session = boto3.Session(
    aws_access_key_id=aws_access_key_id,
    aws_secret_access_key=aws_secret_access_key,
    region_name='ap-northeast-2'
)

# 네이버 API 인증 정보
naverclient_id = naverclient_id
naverclient_secret = naverclient_secret
        

comprehend = session.client('comprehend')

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

# 한글 source_text -> 영어 파파고번역 -> GPT 요청 -> 리스폰받고 -> 한글 번역후 vue로 전송
class PapagomealengAPI(Resource):
    def post(self):
        # source_text = "어린이 또는 아이들에게 좋은 영양소( 탄수화물,지방,단백질 )들에 맞게 메인반찬을 포함하여 식단 3가지 추천해주고 건강에 어떻게 좋은지 알려줘 "
        source_text = "어린이 또는 아이들에게 좋은 영양소( 탄수화물,지방,단백질 )들에 맞게 메인반찬을 포함하여 식단 1가지 추천해주고 건강에 어떻게 좋은지 알려줘 "
        enc_text = urllib.parse.quote(source_text)
        data = f"source=ko&target=en&text={enc_text}"
        url = "https://openapi.naver.com/v1/papago/n2mt"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", naverclient_id)
        request.add_header("X-Naver-Client-Secret", naverclient_secret)

        try:
            response = urllib.request.urlopen(request, data=data.encode("utf-8"))
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
        


# 구글 번역 잘되는지 안되는지 테스트용
class googletransrateAPI(Resource):
    def post(self):
        translator = googletrans.Translator()
        inStr = """어린이집을 보내기 위해서 고려해야 할것들 자세하게 알려줘"""
        outStr = translator.translate(inStr, dest='en', src='auto')
        print(f"{inStr} => {outStr.text}")


# vue에서 번역된 문장 유니코드 걸렸을때 해결법
    # async function kinderrecommendAPP() {
    #   try {
    #     const kinderrecommend = await fetch(
    #       "http://localhost:5000/kinderrecommendAPI",
    #       {
    #         method: "POST",
    #       }
    #     );
    #     const responseData = await kinderrecommend.text();
    #     data.dialog = true;
    #     const decodedResponse = JSON.parse(responseData);
    #     const decodedText = decodedResponse.result.translatedText;
    #     data.kinderrecommend = decodedText;
    #     if (typeof data.kinderrecommend !== "undefined") {
    #       console.log(data.kinderrecommend);
    #       console.log(typeof data.kinderrecommend);
    #     } else {
    #       console.log("data.kinderrecommend is not defined.");
    #     }
    #     data.koreanText = data.kinderrecommend
    #       .replace(/(^{|}$)/g, "")
    #       .replace(/\\n/g, "\n");

    #   } catch (error) {
    #     console.error(error);
    #   }
    # }

        
api.add_resource(GptAPI, '/gptApi')
api.add_resource(PapagomealengAPI, '/gptmeal2API')
api.add_resource(PapagomealkorAPI, '/gptmealkorAPI')
api.add_resource(GptmealAPI, '/gptmealAPI')
api.add_resource(googletransrateAPI, '/googletransrateAPI')


if __name__ == '__main__':
    app.run(debug=True)
