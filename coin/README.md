
# 퀵 스타트
```bash
pip3 install -r requirements.txt

touch .env
echo "TELEGRAM_BOT_TOKEN=텔레그램_토큰" >> .env
echo "TELEGRAM_CHAT_ID=텔레그램_챗_아이디" >> .env
echo "UPBIT_ACCESS_KEY=업비트_액세스_키" >> .env
echo "UPBIT_SECRET_KEY=업비트_시크릿_키" >> .env

python3 main.py
```

# TODO
- [ ] 물타기 동작하면 본전치기로만 하고 탈출하는 전략
- [ ] 시가와 종가가 같을 때 무시 처리
- [ ] 양봉 용어(윗꼬리, 아래꼬리, ..) 캔들 객체에 적용
- [ ] 3개 캔들 기준이라면, 첫 구매를 -3 ~ -5 구매해야한다.