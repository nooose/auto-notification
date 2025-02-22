import threading
import time

# 1번 스레드: 매분 30초마다 외부로부터 정보를 가져와 출력
def thread_1():
    while True:
        current_time = time.localtime()
        if current_time.tm_sec == 30:  # 매분 30초에 출력
            print("Thread 1: Information fetched at", time.strftime("%H:%M:%S", current_time))
        time.sleep(1)

# 2번 스레드: 10초마다 계속 정보를 가져와 출력
def thread_2():
    while True:
        print("Thread 2: Information fetched")
        time.sleep(10)

# 3번 스레드: 외부 시간 값에 따라 반복 출력
def thread_3():
    while True:
        # 외부값을 여기서 받아옴 (예시: '4' -> 4분)
        external_time_value = 1
        interval = external_time_value * 60
        next_time = time.time() + interval
        print(f"Thread 3: Starting with external time value: {external_time_value} minutes.")

        while True:
            current_time = time.time()
            if current_time >= next_time:
                print(f"Thread 3: Information fetched at {time.strftime('%H:%M:%S', time.localtime(current_time))}")
                next_time += interval  # 외부 시간에 맞춰 출력 주기 업데이트
            time.sleep(1)

# 스레드 생성
thread_1_obj = threading.Thread(target=thread_1)
thread_2_obj = threading.Thread(target=thread_2)
thread_3_obj = threading.Thread(target=thread_3)

# 스레드 시작
thread_1_obj.start()
thread_2_obj.start()
thread_3_obj.start()

# 스레드들이 계속 돌아가게 하기 위해 메인 스레드는 기다림
thread_1_obj.join()
thread_2_obj.join()
thread_3_obj.join()
