import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from collections import Counter
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go

def tfidf_analysis(df, font_path):
    st.subheader("TF-IDF 분석")
    
    # 토큰을 문자열로 결합
    df['token_text'] = df['token_list'].apply(lambda tokens: ' '.join(tokens))
    
    # TF-IDF 매개변수 설정
    with st.expander("TF-IDF 매개변수 설정"):
        col1, col2 = st.columns(2)
        max_features = col1.slider("최대 특성 수", 100, 2000, 1000)
        min_df = col2.slider("최소 문서 빈도", 1, 20, 2)
    
    # TF-IDF 행렬 계산
    with st.spinner("TF-IDF 행렬 계산 중..."):
        # TF-IDF 벡터라이저 초기화
        vectorizer = TfidfVectorizer(max_features=max_features, min_df=min_df)
        
        # TF-IDF 행렬 계산
        tfidf_matrix = vectorizer.fit_transform(df['token_text'])
        feature_names = vectorizer.get_feature_names_out()
        
        st.success(f"TF-IDF 행렬 계산 완료: {tfidf_matrix.shape[0]}개 문서 × {tfidf_matrix.shape[1]}개 특성")
    
    # 분석 옵션
    tfidf_options = [
        "주요 키워드 분석",
        "유사 기사 검색",
        "기사 클러스터링",
        "차원 축소 시각화"
    ]
    
    selected_tfidf_option = st.radio(
        "분석 옵션 선택",
        options=tfidf_options,
        horizontal=True
    )
    
    if selected_tfidf_option == "주요 키워드 분석":
        # 코퍼스 전체에서의 단어별 TF-IDF 평균 점수 계산
        mean_tfidf = np.array(tfidf_matrix.mean(axis=0)).flatten()
        word_scores = [(feature_names[i], mean_tfidf[i]) for i in range(len(feature_names))]
        word_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 키워드 표시
        top_n = st.slider("표시할 상위 키워드 수", 10, 50, 30)
        top_words = word_scores[:top_n]
        
        top_words_df = pd.DataFrame(top_words, columns=['단어', 'TF-IDF 점수'])
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.dataframe(top_words_df, use_container_width=True)
        
        with col2:
            fig = px.bar(
                top_words_df,
                x='TF-IDF 점수',
                y='단어',
                orientation='h',
                color='TF-IDF 점수',
                color_continuous_scale=px.colors.sequential.Viridis
            )
            
            fig.update_layout(
                title=f'상위 {top_n}개 TF-IDF 키워드',
                yaxis={'categoryorder': 'total ascending'},
                height=600
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # TF-IDF 기반 워드클라우드
        if font_path:
            st.subheader("TF-IDF 기반 워드클라우드")
            
            word_score_dict = dict(word_scores[:200])  # 상위 200개 단어만 사용
            
            wordcloud = WordCloud(
                font_path=font_path,
                width=800, 
                height=500,
                background_color='white',
                max_words=100,
                max_font_size=150,
                random_state=42
            ).generate_from_frequencies(word_score_dict)
            
            plt.figure(figsize=(10, 6))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            st.pyplot(plt)
    
    elif selected_tfidf_option == "유사 기사 검색":
        # 유사 기사 검색
        st.subheader("유사 기사 검색")
        
        # 문서 간 유사도 계산
        with st.spinner("문서 간 유사도 계산 중..."):
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        # 검색 방법 선택
        search_method = st.radio(
            "검색 방법",
            options=["기사 ID로 검색", "키워드로 검색"],
            horizontal=True
        )
        
        if search_method == "기사 ID로 검색":
            # 기사 ID 선택
            article_ids = df['id'].tolist()
            article_id = st.selectbox("기사 ID 선택", options=article_ids)
            
            if article_id:
                # 선택한 기사 정보 표시
                article_idx = df[df['id'] == article_id].index[0]
                selected_article = df.iloc[article_idx]
                
                st.write("**선택한 기사:**")
                st.write(f"제목: {selected_article['title']}")
                st.write(f"날짜: {selected_article['upload_date'].strftime('%Y-%m-%d')}")
                
                # 유사도 임계값 및 표시할 유사 기사 수 설정
                similarity_threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.3)
                top_n = st.slider("표시할 유사 기사 수", 1, 20, 5)
                
                # 유사 기사 찾기
                sim_scores = list(enumerate(cosine_sim[article_idx]))
                sim_scores = [(i, score) for i, score in sim_scores 
                             if i != article_idx and score >= similarity_threshold]
                sim_scores.sort(key=lambda x: x[1], reverse=True)
                top_sim_scores = sim_scores[:top_n]
                
                # 결과 표시
                if top_sim_scores:
                    st.write("**유사한 기사:**")
                    
                    similar_articles = []
                    for i, (idx, score) in enumerate(top_sim_scores, 1):
                        similar_articles.append({
                            '순위': i,
                            'ID': df.iloc[idx]['id'],
                            '제목': df.iloc[idx]['title'],
                            '날짜': df.iloc[idx]['upload_date'].strftime('%Y-%m-%d'),
                            '유사도': score
                        })
                    
                    similar_df = pd.DataFrame(similar_articles)
                    st.dataframe(similar_df, use_container_width=True)
                else:
                    st.info(f"유사도 {similarity_threshold} 이상인 기사를 찾을 수 없습니다.")
        
        elif search_method == "키워드로 검색":
            # 키워드 입력
            search_keywords = st.text_input("검색할 키워드 입력 (공백으로 구분)")
            
            if search_keywords:
                # 키워드를 TF-IDF 벡터로 변환
                search_vector = vectorizer.transform([search_keywords])
                
                # 모든 문서와의 유사도 계산
                doc_sim = cosine_similarity(search_vector, tfidf_matrix).flatten()
                
                # 유사도 임계값 및 표시할 기사 수 설정
                similarity_threshold = st.slider("유사도 임계값", 0.0, 1.0, 0.1, key="keyword_threshold")
                top_n = st.slider("표시할 기사 수", 1, 20, 10, key="keyword_top_n")
                
                # 유사 기사 찾기
                sim_scores = list(enumerate(doc_sim))
                sim_scores = [(i, score) for i, score in sim_scores if score >= similarity_threshold]
                sim_scores.sort(key=lambda x: x[1], reverse=True)
                top_sim_scores = sim_scores[:top_n]
                
                # 결과 표시
                if top_sim_scores:
                    st.write(f"**'{search_keywords}'와 유사한 기사:**")
                    
                    similar_articles = []
                    for i, (idx, score) in enumerate(top_sim_scores, 1):
                        similar_articles.append({
                            '순위': i,
                            'ID': df.iloc[idx]['id'],
                            '제목': df.iloc[idx]['title'],
                            '날짜': df.iloc[idx]['upload_date'].strftime('%Y-%m-%d'),
                            '유사도': score
                        })
                    
                    similar_df = pd.DataFrame(similar_articles)
                    st.dataframe(similar_df, use_container_width=True)
                else:
                    st.info(f"유사도 {similarity_threshold} 이상인 기사를 찾을 수 없습니다.")
    
    elif selected_tfidf_option == "기사 클러스터링":
        # 클러스터링
        st.subheader("기사 클러스터링")
        
        # 클러스터 수 설정
        n_clusters = st.slider("클러스터 수", 2, 20, 5)
        
        # K-means 클러스터링
        with st.spinner("클러스터링 중..."):
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
            
            # 데이터프레임에 클러스터 라벨 추가
            df_with_clusters = df.copy()
            df_with_clusters['cluster'] = cluster_labels
        
        # 클러스터별 주요 키워드 추출
        cluster_keywords = {}
        
        for i in range(n_clusters):
            # 해당 클러스터의 중심 벡터
            center_vector = kmeans.cluster_centers_[i]
            
            # 상위 키워드 추출
            top_indices = center_vector.argsort()[-10:][::-1]
            top_keywords = [feature_names[idx] for idx in top_indices]
            
            cluster_keywords[i] = top_keywords
        
        # 결과 표시
        st.write("**클러스터별 주요 키워드:**")
        
        for cluster_id, keywords in cluster_keywords.items():
            cluster_size = sum(cluster_labels == cluster_id)
            st.write(f"클러스터 {cluster_id} (기사 수: {cluster_size}):")
            st.write(f"핵심 키워드: {', '.join(keywords)}")
        
        # 클러스터별 기사 표시
        selected_cluster = st.selectbox(
            "클러스터 선택",
            options=list(range(n_clusters))
        )
        
        if selected_cluster is not None:
            cluster_articles = df_with_clusters[df_with_clusters['cluster'] == selected_cluster]
            
            st.write(f"**클러스터 {selected_cluster}의 기사 ({len(cluster_articles)}개):**")
            
            article_table = []
            for _, article in cluster_articles.head(10).iterrows():
                article_table.append({
                    'ID': article['id'],
                    '제목': article['title'],
                    '날짜': article['upload_date'].strftime('%Y-%m-%d')
                })
            
            st.dataframe(pd.DataFrame(article_table), use_container_width=True)
            
            if len(cluster_articles) > 10:
                st.info(f"전체 {len(cluster_articles)}개 중 10개만 표시됩니다.")
    
    elif selected_tfidf_option == "차원 축소 시각화":
        # 차원 축소 시각화
        st.subheader("차원 축소 시각화")
        
        # 차원 축소 방법 선택
        dim_reduction_method = st.radio(
            "차원 축소 방법",
            options=["TruncatedSVD (LSA)"],
            horizontal=True
        )
        
        # 클러스터 수 설정
        n_clusters = st.slider("클러스터 수", 2, 20, 5, key="dim_reduction_clusters")
        
        # 차원 축소 및 클러스터링
        with st.spinner("차원 축소 및 클러스터링 중..."):
            # TruncatedSVD 차원 축소
            svd = TruncatedSVD(n_components=2, random_state=42)
            reduced_data = svd.fit_transform(tfidf_matrix)
            
            # K-means 클러스터링
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(tfidf_matrix)
        
        # 시각화 데이터 준비
        vis_data = pd.DataFrame({
            'x': reduced_data[:, 0],
            'y': reduced_data[:, 1],
            'cluster': cluster_labels,
            'id': df['id'],
            'title': df['title']
        })
        
        # 클러스터별 색상 지정
        fig = px.scatter(
            vis_data,
            x='x',
            y='y',
            color='cluster',
            hover_data=['id', 'title'],
            color_continuous_scale=px.colors.qualitative.G10
        )
        
        fig.update_layout(
            title='TF-IDF 기반 기사 클러스터 시각화',
            xaxis_title='차원 1',
            yaxis_title='차원 2',
            height=700
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 분산 설명 비율
        explained_variance = svd.explained_variance_ratio_.sum()
        st.write(f"2차원으로 설명된 원본 데이터의 분산 비율: {explained_variance:.2%}")