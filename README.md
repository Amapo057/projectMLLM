# projectMLLM
## 역사
### 시작
[![Raspberry Pi를 (물리적) 가상 애완동물로 만들기](https://img.youtube.com/vi/EGkv6HqoYZk/0.jpg)](https://www.youtube.com/watch?v=EGkv6HqoYZk)
- 해당 영상을 상당히 인상깊게 보고 비슷한 프로젝트를 해보려고 시도.(11월 말 경)
- 라즈베리파이를 구매해보려했으나 꽤나 비싸 안쓰던 S22U로 시도해보기로 결정.
### S22U
#### Termux with llama.cpp
<details>

##### 핸드폰
- termux로 리눅스 환경 구성
- 파이썬 서버로 전체 프로세스 관리
- phi-3 mini lmm사용해 로컬 ai 구축
	- llama.cpp 사용
	- 4bit 양자화
##### llama.cpp
- vulkan api 사용해 gpu 성능 사용
	- cmake가 불칸 못잡아 vulkan-headers와 vulkan-tools패키지 깔아 작동
	- 사실 glslc 쉐이더 컴파일러가 없는거였음
- opencl로 변경
	- gpu 경로꼬임
	- ld_library_path넣음
	- cmake가 꼬임
	- termux랑 안드로이드 opencl 드라이버가 꼬임
	- 폴더 만들어서 삼성 opencl 드라이버 가져옴
	- 그래도 gpu 못잡아서 다시 경로 최적화하고 작성
	- 또안됨
- gpu를 잡아서 테스트해봤으나 속도가 cpu랑 별 차이가 없었음...
---
##### 프로젝트 개선
- phi-3에서 qwen3로 변경
  - phi-3의 처참한 한국어 실력에 경악해 프로젝트를 한번 포기함
	- 2B 사용
- qwen3에서 qwen 2.5로 변경
  - qwen3는 사고중심이라 대답으론 잘 작동하지 않음
- llama에서 mnn으로 변경
	- guff가 아닌 mnn 모델 사용
- 전체 초기화 후 mnn설치해 실행
- 빌드중 문제 생겨 gl2인가 라이브러리 추가 설치하고 실행
- opencl 여전히 사용
	- 문제 생기는건 LD어쩌고로 경로 잡으면 됨
---
#### TTS, STT
- termux api사용해서 작동
- TTS는 훌륭히 작동
- STT는 뭔가 꼬였는지 한국어를 인식안함...
	- 구글 인식사용
	- 영어만 가능
	- vosk사용해보려했지만 libatomic라이브러리 설치가 불가능해 구글 사용하기로 결정
---
#### 날씨
- openmeteo 사용

</details>

- 여러 방면으로 시도해봤으나 불편한 개발, stt 꼬임, 불안정한 환경과 mac mini구매로 해당 프로젝트 파기
#### mlc-llm
- 모바일에서 로컬 llm은 포기한 상태였으나 램 부족과 open claw로 인한 물량 부족으로 배송이 5달 가량 밀려 강제로 부활
- termux의 답답한 환경을 벗어나고자 앱으로 선택
- gemma4를 사용하고 싶었으나 아직 지원하지 않아 qwen3.5 사용
- 앱 빌드 후 설치까지 되었으나 이상하게 로컬모델 작동에 문제가 많고, 매우 느리며, 매우 발열이 심해 정상적인 사용이 어렵다 판단 후 폐기
#### mnn
- 앱 빌드과정에서 무언가 꼬였는지 빌드에 오류가 많아 폐기
#### flutter
- 로컬 llm을 포기하고 flutter와 gemini api를 이용해 프로젝트를 가볍게 만들기로 결정
- 호출어관련 모듈들이 제대로 돌아가지 않아 stt를 억지로 사용해 호출하는 방향으로 전환
  - 박수치는 것도 해봤으나 중거리에서의 인식률이 좋지않아 폐기
- 억지로 돌아가는 호출어가 잘 될리가 없어 한계를 느끼고 폐기
### Steam-deck
#### python
- 프로젝트의 한계를 느끼던 와중, 방에서 놀던 스팀덱을 보고 프로젝트의 목표를 전환
  - 리눅스, 저전력 칩셋, 마이크, 스피커, 조도 센서등 다양한 장치가 이미 탑재되어 있어 활용하기 매우 좋음
