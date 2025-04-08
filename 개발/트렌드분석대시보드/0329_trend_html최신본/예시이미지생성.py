import os
from PIL import Image

# 필요한 이미지 파일 이름들
image_files = [
    "card1.jpg", "card2.jpg", "card3.jpg",
    "wordcloud.png", "network.png", "piechart.png",
    "trend1.png", "trend2.png"
]

# 디렉토리 생성
os.makedirs("static/images", exist_ok=True)

# 이미지 생성 함수
def create_dummy_image(path, size=(300, 200), color="gray"):
    img = Image.new("RGB", size, color=color)
    img.save(path)

# 이미지 생성 루프
for filename in image_files:
    path = os.path.join("static/images", filename)
    create_dummy_image(path)

print("✅ 더미 이미지 생성 완료")
