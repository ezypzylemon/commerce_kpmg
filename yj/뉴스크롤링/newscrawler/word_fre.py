import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from collections import Counter

# MySQL에서 데이터 로드
query = "SELECT tokens, upload_date FROM hyungtaeso.tokenised WHERE category='knews_articles'"
df = pd.read_sql(query, conn)

# 시간별 분석을 위한 날짜 변환
df['upload_date'] = pd.to_datetime(df['upload_date'])
df['month'] = df['upload_date'].dt.to_period('M')

# 모든 토큰 결합 (JSON 형식 가정)
all_tokens = []
for tokens_json in df['tokens']:
    tokens = json.loads(tokens_json)
    all_tokens.extend(tokens)

# 빈도수 계산
word_counts = Counter(all_tokens)
top_words = word_counts.most_common(30)

# 시각화
plt.figure(figsize=(12, 8))
plt.bar(*zip(*top_words))
plt.xticks(rotation=45, ha='right')
plt.title('상위 30개 키워드 빈도')
plt.tight_layout()
plt.show()