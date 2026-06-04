import requests
import config 


class BusService:
    def __init__(self):
        self.url = config.BUS_URL
        # 최소한의 사람인 척
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' 
        }
        # 정류장 정보
        self.payload = {
            'busStopId': '326009952',
            'serviceId': '[3260361]',
            'busName': '부영3차.팔마중',
            'locale': 'ko'
        }

    def get_bus_context(self) -> str:
        try:
            response = requests.post(self.url, headers=self.headers, data=self.payload, timeout=5)
            # 에러 발생시 예외 처리
            response.raise_for_status()

            bus_data = response.json()

            # print("데이터 수신 성공")
        except Exception as e:
            return "데이터를 받아오지 못했습니다."

        bus_list = bus_data.get("busStopRouteList")
        bus_time = []

        if not bus_list:
            return "데이터를 변환하지 못했습니다."
        
        for i in bus_list:
            if i.get("provide_type") == "정보없음":
                continue
            if i.get("route_name") in "71" "71-1":
                bus_time.append([i.get("provide_type"), i.get("rstop")])
        context = (
                f"현재 집 앞 정류장의 버스 도착 정보입니다. {bus_time}. "
                f"명령: 위 데이터를 바탕으로 사용자에게 '곧 도착할 버스는 n분 남았고, n정거장 남았습니다. 다음 버스는...'와 같이 브리핑 하세요"
            )
        
        return context

if __name__ == "__main__":
    b = BusService()
    print(b.get_bus_context())