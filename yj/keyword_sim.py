import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
from itertools import combinations

def load_data():
    file_path = "/Users/jiyeonjoo/Desktop/최종 플젝/연관키워드 20250311 1634.xlsx"
    df = pd.read_excel(file_path, sheet_name='sheet')
    df = df.rename(columns={
        '연관키워드': 'Keyword',
        '월간검색수(PC)': 'Search_PC',
        '월간검색수(모바일)': 'Search_Mobile',
        '월평균클릭수(PC)': 'Click_PC',
        '월평균클릭수(모바일)': 'Click_Mobile',
        '월평균클릭률(PC)': 'CTR_PC',
        '월평균클릭률(모바일)': 'CTR_Mobile',
        '경쟁정도': 'Competition',
        '월평균노출 광고수': 'Ad_Impressions'
    })
    
    # 숫자 컬럼들 정리
    # 콤마(,) 제거 및 float 변환
    for col in ['Search_PC', 'Search_Mobile', 'Click_PC', 'Click_Mobile']:
        df[col] = df[col].astype(str).str.replace(',', '').astype(float)
    
    # % 기호 제거 및 float 변환
    for col in ['CTR_PC', 'CTR_Mobile']:
        df[col] = df[col].astype(str).str.replace('%', '').astype(float) / 100
    
    # 총 검색량 계산
    df['Total_Search'] = df['Search_PC'] + df['Search_Mobile']
    
    return df

def identify_core_keywords(df):
    st.subheader("🔍 핵심 키워드 식별 & 클러스터링 분석")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📌 핵심 키워드")
        core_keywords = df.nlargest(10, 'Total_Search')[['Keyword', 'Total_Search']]
        st.dataframe(core_keywords)
    
    with col2:
        st.subheader("📌 키워드 클러스터링")
        df_cluster = df[['Total_Search', 'Click_PC', 'Click_Mobile']].fillna(0)
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df_cluster)
        
        kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        df['Cluster'] = kmeans.fit_predict(df_scaled)
        
        fig = px.scatter(df, x='Total_Search', y='Click_Mobile', color=df['Cluster'].astype(str),
                         hover_data=['Keyword'], title='키워드 클러스터링')
        st.plotly_chart(fig)
    
    st.subheader("📊 클러스터별 키워드 분석")
    cluster_groups = df.groupby('Cluster')
    cols = st.columns(2)
    
    for i, (cluster, group) in enumerate(cluster_groups):
        with cols[i % 2]:
            st.write(f"### Cluster {cluster} 대표 키워드")
            st.dataframe(group[['Keyword', 'Total_Search']].nlargest(3, 'Total_Search'))

def sns_keywords_and_item_dashboard(df):
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📲 SNS 크롤링을 위한 키워드")
        sns_keywords = df[(df['Total_Search'] > df['Total_Search'].median()) & (df['Click_Mobile'] > df['Click_Mobile'].median())]
        sns_keywords['Hashtag'] = sns_keywords['Keyword'].apply(lambda x: f"#{x.replace(' ', '')}")
        st.dataframe(sns_keywords[['Keyword', 'Total_Search', 'Click_Mobile', 'Hashtag']].head(10))
    
    with col2:
        st.subheader("📦 아이템 분류 및 순위 분석")
        item_mapping = {
            '상의': ["탑", "셔츠", "블라우스", "니트웨어"],
            '하의': ["팬츠", "청바지", "스커트"],
            '아우터': ["재킷", "코트", "패딩", "점퍼", "베스트"],
            '원피스': ["드레스", "점프수트"],
            '기타': ["캐주얼상의"]
        }
        
        def map_item(keyword):
            for category, keywords in item_mapping.items():
                if any(k in keyword for k in keywords):
                    return category
            return "기타"
        
        df['Item_Category'] = df['Keyword'].apply(map_item)
        item_rank = df.groupby('Item_Category')['Total_Search'].sum().reset_index().sort_values(by='Total_Search', ascending=False)
        st.dataframe(item_rank)

def analyze_keyword_associations(df):
    """키워드 간 연관도 분석 및 시각화"""
    st.subheader("🔄 키워드 연관도 분석")
    
    # 상위 키워드 선택
    top_n = st.slider("분석할 상위 키워드 수", 5, 30, 15)
    top_keywords = df.nlargest(top_n, 'Total_Search')
    
    # 코사인 유사도를 기반으로 연관도 매트릭스 생성
    features = ['Total_Search', 'Click_PC', 'Click_Mobile']
    
    # CTR 컬럼이 적절하게 변환되었는지 확인
    if df['CTR_PC'].dtype == np.float64 and df['CTR_Mobile'].dtype == np.float64:
        features.extend(['CTR_PC', 'CTR_Mobile'])
    
    # 결측치 처리
    keyword_features = top_keywords[features].fillna(0)
    # 정규화
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(keyword_features)
    
    # 코사인 유사도 계산
    similarity_matrix = cosine_similarity(scaled_features)
    
    # 네트워크 그래프 생성을 위한 데이터 준비
    G = nx.Graph()
    
    # 노드 추가
    for idx, keyword in enumerate(top_keywords['Keyword']):
        G.add_node(keyword, size=float(top_keywords.iloc[idx]['Total_Search']))
    
    # 연관도 임계값 (0.5 이상인 경우만 연결선 표시)
    threshold = st.slider("연관도 임계값", 0.0, 1.0, 0.5, 0.1)
    
    # 간선 추가
    for i in range(len(top_keywords)):
        for j in range(i+1, len(top_keywords)):
            if similarity_matrix[i, j] > threshold:
                G.add_edge(
                    top_keywords.iloc[i]['Keyword'], 
                    top_keywords.iloc[j]['Keyword'],
                    weight=similarity_matrix[i, j]
                )
    
    # 시각화
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 네트워크 그래프 생성
        pos = nx.spring_layout(G, seed=42)
        
        # 노드와 간선 정보 추출
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            # 검색량에 따라 노드 크기 조정
            size = G.nodes[node]['size'] / top_keywords['Total_Search'].max() * 30
            node_size.append(size + 10)  # 최소 크기 10으로 설정
            
        # 간선 트레이스
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # 노드 트레이스
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            textposition="top center",
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlGnBu',
                size=node_size,
                color=[G.degree(node) for node in G.nodes()],
                colorbar=dict(
                    thickness=15,
                    title='연결 강도',
                    xanchor='left',
                    titleside='right'
                ),
                line_width=2))
        
        # 그래프 그리기
        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='키워드 연관도 네트워크',
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=20, l=5, r=5, t=40),
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
        
        st.plotly_chart(fig)
        
    with col2:
        st.subheader("💡 주요 연관 키워드 쌍")
        # 연관도가 높은 키워드 쌍 추출
        keyword_pairs = []
        for i in range(len(top_keywords)):
            for j in range(i+1, len(top_keywords)):
                if similarity_matrix[i, j] > threshold:
                    keyword_pairs.append({
                        '키워드 1': top_keywords.iloc[i]['Keyword'],
                        '키워드 2': top_keywords.iloc[j]['Keyword'],
                        '연관도': similarity_matrix[i, j]
                    })
                    
        # 연관도가 높은 순으로 정렬
        if keyword_pairs:
            pairs_df = pd.DataFrame(keyword_pairs).sort_values('연관도', ascending=False)
            st.dataframe(pairs_df)
        else:
            st.info("임계값을 낮춰서 더 많은 연관 키워드 쌍을 확인하세요.")

def analyze_keyword_similarity(df):
    """키워드 텍스트 유사도 분석"""
    st.subheader("🔤 키워드 텍스트 유사도 분석")
    
    # 형태소 분석기를 사용하면 더 좋지만, 단순 분석으로 진행
    # 키워드 전처리
    keywords = df['Keyword'].tolist()
    
    # TF-IDF 벡터화
    vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(keywords)
    
    # 코사인 유사도 계산
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    
    # 인터랙티브 유사도 검색
    col1, col2 = st.columns([1, 1])
    
    with col1:
        selected_keyword = st.selectbox("키워드 선택", df['Keyword'].tolist())
        num_similar = st.slider("유사 키워드 수", 5, 20, 10)
        
        if selected_keyword:
            idx = df.index[df['Keyword'] == selected_keyword].tolist()[0]
            sim_scores = list(enumerate(cosine_sim[idx]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
            sim_scores = sim_scores[1:num_similar+1]  # 첫 번째는 자기 자신이므로 제외
            similar_indices = [i[0] for i in sim_scores]
            similar_keywords = df.iloc[similar_indices][['Keyword', 'Total_Search']]
            similar_keywords['유사도'] = [i[1] for i in sim_scores]
            
            st.dataframe(similar_keywords.sort_values('유사도', ascending=False))
    
    with col2:
        # 워드 클라우드 생성을 위한 유사 키워드들의 빈도 계산
        st.subheader("유사 키워드 시각화")
        
        # 유사도 히트맵
        if len(df) > 30:  # 데이터가 너무 많으면 히트맵이 복잡해질 수 있음
            top_keys = df.nlargest(20, 'Total_Search')['Keyword'].tolist()
            mask = df['Keyword'].isin(top_keys)
            subset_df = df[mask].reset_index(drop=True)
            
            # 서브셋에 대한 TF-IDF 및 코사인 유사도 다시 계산
            subset_keywords = subset_df['Keyword'].tolist()
            subset_tfidf = vectorizer.fit_transform(subset_keywords)
            subset_cosine_sim = cosine_similarity(subset_tfidf, subset_tfidf)
            
            # 히트맵 그리기
            fig = px.imshow(
                subset_cosine_sim,
                labels=dict(x="키워드", y="키워드", color="유사도"),
                x=subset_keywords,
                y=subset_keywords,
                color_continuous_scale="Viridis"
            )
            fig.update_layout(
                title="상위 20개 키워드 유사도 히트맵",
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig)
        else:
            st.info("데이터가 충분하지 않습니다.")

def keyword_association_analysis(df):
    """키워드 연관규칙 분석 (아이템 기반)"""
    st.subheader("🔗 키워드 연관규칙 분석")
    
    # 키워드에서 주요 단어 추출
    def extract_key_terms(keyword):
        # 단순 공백 기준 분리 (한국어 형태소 분석기를 사용하면 더 정확함)
        return keyword.split()
    
    # 키워드에서 주요 용어 추출
    df['terms'] = df['Keyword'].apply(extract_key_terms)
    
    # 용어 빈도 계산
    all_terms = []
    for terms in df['terms']:
        all_terms.extend(terms)
    
    term_freq = pd.Series(all_terms).value_counts().reset_index()
    term_freq.columns = ['Term', 'Frequency']
    
    # 빈도가 높은 용어 추출
    min_support = st.slider("최소 지지도 (최소 출현 빈도)", 2, 10, 3)
    frequent_terms = term_freq[term_freq['Frequency'] >= min_support]['Term'].tolist()
    
    # 연관규칙 분석을 위한 용어 쌍 생성
    term_pairs = []
    support_dict = {}
    confidence_dict = {}
    
    # 지지도와 신뢰도 계산
    for terms in df['terms']:
        # 빈번 용어만 포함
        filtered_terms = [term for term in terms if term in frequent_terms]
        
        # 용어 쌍 조합 생성
        for pair in combinations(filtered_terms, 2):
            sorted_pair = tuple(sorted(pair))
            if sorted_pair in support_dict:
                support_dict[sorted_pair] += 1
            else:
                support_dict[sorted_pair] = 1
    
    # 지지도를 비율로 변환
    total_records = len(df)
    for pair, count in support_dict.items():
        support_dict[pair] = count / total_records
    
    # 신뢰도 계산 (A → B)
    for pair in support_dict:
        term1, term2 = pair
        # term1이 나타난 키워드 수
        term1_count = sum(1 for terms in df['terms'] if term1 in terms)
        # term2가 나타난 키워드 수
        term2_count = sum(1 for terms in df['terms'] if term2 in terms)
        
        # 신뢰도: P(B|A) = support(A,B) / support(A)
        confidence_1_to_2 = support_dict[pair] * total_records / term1_count if term1_count > 0 else 0
        confidence_2_to_1 = support_dict[pair] * total_records / term2_count if term2_count > 0 else 0
        
        term_pairs.append({
            '용어1': term1,
            '용어2': term2,
            '지지도': support_dict[pair],
            '신뢰도(1→2)': confidence_1_to_2,
            '신뢰도(2→1)': confidence_2_to_1,
            '향상도': (support_dict[pair] * total_records) / (term1_count * term2_count) if term1_count * term2_count > 0 else 0
        })
    
    # 결과 정렬 및 표시
    if term_pairs:
        term_pairs_df = pd.DataFrame(term_pairs).sort_values('향상도', ascending=False)
        st.dataframe(term_pairs_df)
        
        # 시각화
        fig = px.scatter(
            term_pairs_df.head(20),
            x='지지도',
            y='향상도',
            size='신뢰도(1→2)',
            color='신뢰도(2→1)',
            hover_data=['용어1', '용어2'],
            title='용어 연관규칙 분석 (상위 20개)'
        )
        st.plotly_chart(fig)
    else:
        st.info("충분한 연관규칙을 찾을 수 없습니다. 최소 지지도를 낮춰보세요.")

def main():
    st.title("📊 키워드 분석 대시보드")
    df = load_data()
    
    # 기존 분석
    identify_core_keywords(df)
    sns_keywords_and_item_dashboard(df)
    
    # 새로운 연관도 및 유사도 분석
    st.title("🔄 키워드 연관도 및 유사도 분석")
    
    # 연관도 분석 탭
    analyze_keyword_associations(df)
    
    # 텍스트 유사도 분석 탭
    analyze_keyword_similarity(df)
    
    # 연관규칙 분석 탭
    keyword_association_analysis(df)

if __name__ == "__main__":
    main()