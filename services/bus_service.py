import requests
import config

class BusService:
    def __init__(self):
        self.api_key = config.BUS_API_KEY
        self.city_code = '36030'
        self.node_id = 'SCB326009952'
        self.url = f"http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList"

    def get_bus_context(self) -> str:
        """TAGO API를 호출하여 버스 도착 정보를 가져와 프롬프트 컨텍스트로 반환합니다."""
        try:
            params = {
                'serviceKey': self.api_key,
                'cityCode': self.city_code,
                'nodeId': self.node_id,
                '_type': 'json'
            }
            # requests는 params에 포함된 URL 인코딩된 키를 한 번 더 인코딩할 수 있으므로 주의.
            # 공공데이터포털 API의 경우 인코딩된 키를 그대로 넘기기 위해 URL 문자열을 직접 조립하기도 합니다.
            # 하지만 우선 권장되는 params 방식을 사용합니다. (문제 발생 시 직접 조립 방식으로 변경)
            response = requests.get(self.url, params=params, timeout=5)
            response.raise_for_status()
            
            try:
                data = response.json()
                # print(f"버스 정보: {data}")
            except ValueError:
                # JSON 파싱 에러 발생 시 (일반적으로 XML 에러 메시지가 리턴될 때)
                print(f"[Bus Error] API 응답이 JSON 형식이 아닙니다: {response.text}")
                return "현재 버스 도착 정보를 가져오는 데 문제가 발생했습니다 (API 응답 오류)."

            items = data.get("response", {}).get("body", {}).get("items", {})
            if not items:
                return "현재 집 앞 정류장에 도착 예정인 버스 정보가 없습니다."
                
            item_data = items.get("item", [])

            # 단일 객체 응답 처리
            if isinstance(item_data, dict):
                item_data = [item_data]

            bus_info_list = []
            for item in item_data:
                routeno = item.get("routeno")
                if not str(routeno).startswith("71"):
                    continue
                arrtime = item.get("arrtime") # 도착예정시간(초)
                arrprevstationcnt = item.get("arrprevstationcnt") # 남은 정류장 수
                
                if arrtime is not None:
                    minutes = int(arrtime) // 60
                    bus_info_list.append(f"[{routeno}번 버스: {minutes}분 후 도착 예정 ({arrprevstationcnt}정거장 전)]")
            
            if not bus_info_list:
                return "도착 예정인 버스의 상세 정보를 파악할 수 없습니다."
                
            buses_str = ", ".join(bus_info_list)
            context = (
                f"현재 집 앞 정류장의 버스 도착 정보입니다. {buses_str}. "
                f"명령: 위 데이터를 바탕으로 사용자에게 가장 빠른 버스 두개의 정보를 제공해야합니다.'곧 도착할 버스는 ~번이며, ~정거장 남았고, 약 ~분 뒤에 도착합니다. 다음 버스는 ~번이며, 약 ~분 뒤에 도착합니다.' 같이 브리핑해주세요."
            )
            print(f"\n[Bus Info] 수집된 버스 도착 정보:\n{buses_str}\n")
            return context

        except requests.exceptions.RequestException as e:
            # print(f"[Bus Error] 버스 정보 조회 실패: {e}")
            return "현재 버스 도착 정보를 통신 문제로 가져오지 못했습니다."
        except Exception as e:
            # print(f"[Bus Error] 예기치 않은 오류: {e}")
            return "현재 버스 도착 정보를 처리하는 중 오류가 발생했습니다."


