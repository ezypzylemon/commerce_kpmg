import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import base64
from io import BytesIO
import tempfile
import os
import re
from collections import Counter

def topic_modeling_analysis(df, font_path):
    st.subheader("토픽 모델링 분석")
    
    # 토큰을 문자열로 결합
    df['token_text'] = df['token_list'].apply(lambda tokens: ' '.join(tokens))
    
    # 문서-단어 행렬 매개변수 설정
    with st.expander("문서-단어 행렬 매개변수 설정"):
        col1, col2, col3 = st.columns(3)
        max_features = col1.slider("최대 특성 수", 100, 2000, 1000)
        min_df = col2.slider("최소 문서 빈도", 1, 20, 2)
        max_df = col3.slider("최대 문서 빈도 비율", 0.5, 1.0, 0.95)
    
    # 문서-단어 행렬 생성
    with st.spinner("문서-단어 행렬 생성 중..."):
        # CountVectorizer 초기화
        count_vectorizer = CountVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df
        )
        
        # 문서-단어 행렬 생성
        doc_term_matrix = count_vectorizer.fit_transform(df['token_text'])
        feature_names = count_vectorizer.get_feature_names_out()
        
        st.success(f"문서-단어 행렬 생성 완료: {doc_term_matrix.shape[0]}개 문서 × {doc_term_matrix.shape[1]}개 특성")
    
    # 토픽 수 설정
    n_topics = st.slider("토픽 수", 2, 20, 5)
    
    # LDA 매개변수 설정
    with st.expander("LDA 매개변수 설정"):
        col1, col2 = st.columns(2)
        max_iter = col1.slider("최대 반복 횟수", 5, 50, 10)
        learning_method = col2.selectbox("학습 방법", options=["online", "batch"])
    
    # LDA 모델 학습
    with st.spinner("LDA 모델 학습 중..."):
        # LDA 모델 초기화 및 학습
        lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=max_iter,
            learning_method=learning_method,
            random_state=42,
            n_jobs=-1  # 모든 CPU 사용
        )
        
        lda_model.fit(doc_term_matrix)
        
        st.success("LDA 모델 학습 완료")
    
    # 토픽별 주요 단어 추출
    n_top_words = 10  # 기본값으로 10개 단어 사용
    topic_words = []
    for topic_idx, topic in enumerate(lda_model.components_):
        top_indices = topic.argsort()[:-n_top_words-1:-1]
        top_words = [feature_names[i] for i in top_indices]
        topic_words.append(top_words)
    
    # 토픽 자동 명명 기능
    topic_names_auto = []
    for words in topic_words:
        # 상위 3개 단어를 사용하여 자동 명명
        topic_name = " & ".join(words[:3])
        topic_names_auto.append(topic_name)
    
    # 세션 상태에 토픽 이름 저장 (처음 실행 시에만 자동 이름 사용)
    if 'topic_names' not in st.session_state:
        st.session_state.topic_names = topic_names_auto.copy()
    # 토픽 수가 변경된 경우 토픽 이름 초기화
    elif len(st.session_state.topic_names) != n_topics:
        st.session_state.topic_names = topic_names_auto.copy()
    
    # 토픽 이름 편집 기능
    st.subheader("토픽 이름 지정")
    
    naming_col1, naming_col2 = st.columns([1, 3])
    with naming_col1:
        edit_topic_names = st.checkbox("토픽 이름 수동 편집")
    
    with naming_col2:
        if edit_topic_names:
            st.write("토픽의 주요 단어를 참고하여 의미 있는 이름을 지정해주세요:")
            for topic_idx in range(n_topics):
                default_name = st.session_state.topic_names[topic_idx]
                st.session_state.topic_names[topic_idx] = st.text_input(
                    f"토픽 {topic_idx+1}의 이름",
                    value=default_name,
                    key=f"topic_name_{topic_idx}"
                )
        else:
            # 자동 이름 생성 방식 선택
            auto_naming_method = st.radio(
                "자동 명명 방식",
                options=["Top-3 단어 조합", "가장 중요한 단어", "단어 빈도수 기반"],
                horizontal=True
            )
            
            if auto_naming_method == "Top-3 단어 조합":
                st.session_state.topic_names = [" & ".join(words[:3]) for words in topic_words]
            elif auto_naming_method == "가장 중요한 단어":
                st.session_state.topic_names = [words[0] + " 관련" for words in topic_words]
            elif auto_naming_method == "단어 빈도수 기반":
                # 문서에서 가장 자주 등장하는 단어를 사용
                st.session_state.topic_names = []
                for topic_idx in range(n_topics):
                    # 해당 토픽에 속한 문서들 필터링
                    doc_topic_dist = lda_model.transform(doc_term_matrix)
                    dominant_topics = doc_topic_dist.argmax(axis=1)
                    topic_docs = [i for i, topic in enumerate(dominant_topics) if topic == topic_idx]
                    
                    if topic_docs:
                        # 토픽 문서에서 가장 빈번한 단어 찾기
                        topic_doc_tokens = []
                        for doc_idx in topic_docs:
                            if doc_idx < len(df):
                                topic_doc_tokens.extend(df.iloc[doc_idx]['token_list'])
                        
                        word_counts = Counter(topic_doc_tokens)
                        common_words = [word for word, _ in word_counts.most_common(3)]
                        if common_words:
                            topic_name = " & ".join(common_words)
                        else:
                            topic_name = topic_words[topic_idx][0] + " 관련"
                    else:
                        topic_name = topic_words[topic_idx][0] + " 관련"
                    
                    st.session_state.topic_names.append(topic_name)

            st.info("자동 생성된 토픽 이름을 수동으로 편집하려면 '토픽 이름 수동 편집' 체크박스를 선택하세요.")
    
    # 토픽 이름 및 주요 단어 표시
    st.subheader("토픽 요약")
    topic_summary = []
    for topic_idx in range(n_topics):
        topic_summary.append({
            "토픽 번호": f"토픽 {topic_idx+1}",
            "토픽 이름": st.session_state.topic_names[topic_idx],
            "주요 단어": ", ".join(topic_words[topic_idx][:5]) + "..."
        })
    
    st.dataframe(pd.DataFrame(topic_summary), use_container_width=True)
    
    # 문서별 토픽 확률 분포
    doc_topic_dist = lda_model.transform(doc_term_matrix)
    
    # 주요 토픽 할당
    df_with_topics = df.copy()
    df_with_topics['dominant_topic'] = doc_topic_dist.argmax(axis=1)
    df_with_topics['topic_confidence'] = doc_topic_dist.max(axis=1)
    df_with_topics['topic_name'] = df_with_topics['dominant_topic'].apply(
        lambda x: st.session_state.topic_names[x] if x < len(st.session_state.topic_names) else f"토픽 {x+1}"
    )
    
    # 분석 옵션
    topic_options = [
        "토픽별 주요 단어",
        "문서별 토픽 분포",
        "시간에 따른 토픽 트렌드"
    ]
    
    selected_topic_option = st.radio(
        "분석 옵션 선택",
        options=topic_options,
        horizontal=True
    )
    
    if selected_topic_option == "토픽별 주요 단어":
        # 토픽별 주요 단어 출력
        st.subheader("토픽별 주요 단어")
        
        # 표시할 단어 수
        n_top_words = st.slider("표시할 단어 수", 5, 30, 10)
        
        # 결과 표시
        for topic_idx, words in enumerate(topic_words):
            topic_name = st.session_state.topic_names[topic_idx]
            st.write(f"**토픽 #{topic_idx+1} [{topic_name}]**: {', '.join(words[:n_top_words])}")
        
        # 히트맵 시각화
        st.subheader("토픽-단어 히트맵")
        
        # 토픽별 상위 단어 및 중요도 추출
        topic_word_matrix = np.zeros((n_topics, n_top_words))
        words_for_heatmap = []
        
        for topic_idx, topic in enumerate(lda_model.components_):
            top_indices = topic.argsort()[:-n_top_words-1:-1]
            topic_word_matrix[topic_idx] = topic[top_indices]
            if topic_idx == 0:  # 첫 번째 토픽에서만 단어 저장
                words_for_heatmap = [feature_names[i] for i in top_indices]
        
        # 히트맵 데이터 준비
        heatmap_data = []
        for topic_idx in range(n_topics):
            topic_name = st.session_state.topic_names[topic_idx]
            for word_idx, word in enumerate(words_for_heatmap):
                heatmap_data.append({
                    '토픽': f'토픽 {topic_idx+1}<br>[{topic_name}]',
                    '단어': word,
                    '중요도': topic_word_matrix[topic_idx, word_idx]
                })
        
        heatmap_df = pd.DataFrame(heatmap_data)
        
        # 피벗 테이블로 변환
        pivot_df = heatmap_df.pivot(index='토픽', columns='단어', values='중요도')
        
        # 히트맵 생성
        fig = px.imshow(
            pivot_df,
            color_continuous_scale='Viridis',
            aspect="auto"
        )
        
        fig.update_layout(
            title='토픽-단어 중요도 히트맵',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 토픽별 워드클라우드
        if font_path:
            st.subheader("토픽별 워드클라우드")
            
            # 토픽 선택 옵션에 토픽 이름 추가
            topic_options = [f"토픽 {i+1}: {st.session_state.topic_names[i]}" for i in range(n_topics)]
            selected_topic = st.selectbox(
                "토픽 선택",
                options=topic_options
            )
            
            if selected_topic:
                topic_idx = int(re.search(r'토픽 (\d+)', selected_topic).group(1)) - 1
                
                # 선택한 토픽의 단어 가중치 추출
                topic_weights = lda_model.components_[topic_idx]
                word_weights = {feature_names[i]: topic_weights[i] for i in range(len(feature_names))}
                
                # 워드클라우드 생성
                wordcloud = WordCloud(
                    font_path=font_path,
                    width=800, 
                    height=500,
                    background_color='white',
                    max_words=100,
                    max_font_size=150,
                    random_state=42
                ).generate_from_frequencies(word_weights)
                
                plt.figure(figsize=(10, 6))
                plt.imshow(wordcloud, interpolation='bilinear')
                plt.axis('off')
                plt.title(f'{selected_topic} 워드클라우드')
                st.pyplot(plt)
    
    elif selected_topic_option == "문서별 토픽 분포":
        # 문서별 토픽 분포
        st.subheader("문서별 토픽 분포")
        
        # 토픽별 문서 수
        topic_counts = df_with_topics['dominant_topic'].value_counts().sort_index()
        topic_names = [st.session_state.topic_names[i] for i in topic_counts.index]
        topic_labels = [f'토픽 {i+1}: {topic_names[idx]}' for idx, i in enumerate(topic_counts.index)]
        
        # 토픽 분포 시각화
        fig = px.bar(
            x=topic_labels,
            y=topic_counts.values,
            color=topic_counts.values,
            color_continuous_scale=px.colors.sequential.Viridis,
            labels={'x': '토픽', 'y': '문서 수'}
        )
        
        fig.update_layout(
            title='토픽별 문서 분포',
            xaxis_title='토픽',
            yaxis_title='문서 수',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 토픽별 확신도 분포
        topic_confidence = []
        for topic in range(n_topics):
            topic_docs = df_with_topics[df_with_topics['dominant_topic'] == topic]
            if len(topic_docs) > 0:
                topic_name = st.session_state.topic_names[topic]
                topic_confidence.append({
                    '토픽': f'토픽 {topic+1}: {topic_name}',
                    '평균 확신도': topic_docs['topic_confidence'].mean(),
                    '문서 수': len(topic_docs)
                })
        
        confidence_df = pd.DataFrame(topic_confidence)
        
        # 확신도 시각화
        fig = px.bar(
            confidence_df,
            x='토픽',
            y='평균 확신도',
            color='문서 수',
            color_continuous_scale=px.colors.sequential.Blues
        )
        
        fig.update_layout(
            title='토픽별 평균 확신도',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 토픽별 주요 문서
        st.subheader("토픽별 주요 문서")
        
        # 토픽 선택 옵션에 토픽 이름 추가
        topic_options = [f"토픽 {i+1}: {st.session_state.topic_names[i]}" for i in range(n_topics)]
        selected_topic_docs = st.selectbox(
            "토픽 선택",
            options=topic_options,
            key="topic_select_docs"
        )
        
        if selected_topic_docs:
            topic_idx = int(re.search(r'토픽 (\d+)', selected_topic_docs).group(1)) - 1
            
            # 해당 토픽의 문서 필터링 및 확신도 기준 정렬
            topic_articles = df_with_topics[df_with_topics['dominant_topic'] == topic_idx]
            topic_articles = topic_articles.sort_values('topic_confidence', ascending=False)
            
            if not topic_articles.empty:
                st.write(f"**{selected_topic_docs}의 주요 문서 (총 {len(topic_articles)}개):**")
                
                article_table = []
                for _, article in topic_articles.head(10).iterrows():
                    article_table.append({
                        'ID': article['id'],
                        '제목': article['title'],
                        '날짜': article['upload_date'].strftime('%Y-%m-%d'),
                        '확신도': f"{article['topic_confidence']:.4f}"
                    })
                
                st.dataframe(pd.DataFrame(article_table), use_container_width=True)
                
                if len(topic_articles) > 10:
                    st.info(f"전체 {len(topic_articles)}개 중 10개만 표시됩니다.")
            else:
                st.info(f"{selected_topic_docs}에 해당하는 문서가 없습니다.")
    
    elif selected_topic_option == "시간에 따른 토픽 트렌드":
        # 시간에 따른 토픽 트렌드
        st.subheader("시간에 따른 토픽 트렌드")
        
        # 월별, 토픽별 문서 수 집계
        df_with_topics['year_month'] = df_with_topics['upload_date'].dt.strftime('%Y-%m')
        topic_trends = pd.crosstab(
            df_with_topics['year_month'], 
            df_with_topics['dominant_topic']
        ).sort_index()
        
        # 컬럼명 변경 (토픽 이름 포함)
        new_columns = {}
        for col in topic_trends.columns:
            if col < len(st.session_state.topic_names):
                new_columns[col] = f'토픽 {col+1}: {st.session_state.topic_names[col]}'
            else:
                new_columns[col] = f'토픽 {col+1}'
        
        topic_trends = topic_trends.rename(columns=new_columns)
        
        # 각 월의 전체 문서 수로 정규화
        normalized_trends = topic_trends.div(topic_trends.sum(axis=1), axis=0)
        
        # 표시 방식 선택
        display_method = st.radio(
            "표시 방식",
            options=["선 그래프", "히트맵"],
            horizontal=True
        )
        
        if display_method == "선 그래프":
            # 선 그래프 시각화
            fig = go.Figure()
            
            for topic in topic_trends.columns:
                fig.add_trace(
                    go.Scatter(
                        x=normalized_trends.index,
                        y=normalized_trends[topic],
                        mode='lines+markers',
                        name=topic
                    )
                )
            
            fig.update_layout(
                title='시간에 따른 토픽 트렌드',
                xaxis_title='년-월',
                yaxis_title='토픽 비율',
                height=500,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif display_method == "히트맵":
            # 히트맵 시각화
            fig = px.imshow(
                normalized_trends.T,
                color_continuous_scale='Viridis',
                labels=dict(
                    x="년-월", 
                    y="토픽", 
                    color="비율"
                )
            )
            
            fig.update_layout(
                title='토픽 트렌드 히트맵',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # 토픽 모델 다운로드 옵션
    st.subheader("토픽 모델 결과 다운로드")
    
    # 토픽 모델 결과 저장
    topic_model_results = {
        "model": lda_model,
        "vectorizer": count_vectorizer,
        "feature_names": feature_names,
        "topic_words": topic_words,
        "topic_names": st.session_state.topic_names
    }
    
    # 문서-토픽 분포 파일
    document_topics_df = df[['id', 'title']].copy()
    
    # 문서별 각 토픽의 확률 추가
    for topic_idx in range(n_topics):
        topic_name = st.session_state.topic_names[topic_idx]
        document_topics_df[f"토픽_{topic_idx+1}_{topic_name}"] = doc_topic_dist[:, topic_idx]
    
    # 주요 토픽 및 확신도 추가
    document_topics_df['주요_토픽_번호'] = df_with_topics['dominant_topic'] + 1
    document_topics_df['주요_토픽_이름'] = df_with_topics['topic_name']
    document_topics_df['주요_토픽_확신도'] = df_with_topics['topic_confidence']
    
    # CSV 파일로 변환
    csv = document_topics_df.to_csv(index=False)
    
    # 다운로드 버튼
    st.download_button(
        label="문서-토픽 분포 다운로드 (CSV)",
        data=csv,
        file_name="document_topics.csv",
        mime="text/csv"
    )
    
    return df_with_topics, topic_model_results

def analyze_topics(data):
    """토픽 모델링을 수행하고 결과를 반환합니다."""
    try:
        # 토큰을 문자열로 결합
        data['token_text'] = data['tokens'].apply(lambda tokens: ' '.join(tokens) if isinstance(tokens, list) else '')
        
        # 문서-단어 행렬 생성
        count_vectorizer = CountVectorizer(
            max_features=1000,
            min_df=2,
            max_df=0.95
        )
        
        doc_term_matrix = count_vectorizer.fit_transform(data['token_text'])
        feature_names = count_vectorizer.get_feature_names_out()
        
        # LDA 모델 학습
        n_topics = 5
        lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            max_iter=10,
            learning_method='online',
            random_state=42,
            n_jobs=-1
        )
        
        lda_model.fit(doc_term_matrix)
        
        # 토픽별 주요 단어 추출
        n_top_words = 10
        topic_words = []
        for topic_idx, topic in enumerate(lda_model.components_):
            top_indices = topic.argsort()[:-n_top_words-1:-1]
            top_words = [feature_names[i] for i in top_indices]
            topic_words.append(top_words)
        
        # 토픽 자동 명명
        topic_names = []
        for words in topic_words:
            topic_name = " & ".join(words[:3])
            topic_names.append(topic_name)
        
        # 문서별 토픽 확률 분포
        doc_topic_dist = lda_model.transform(doc_term_matrix)
        
        # 토픽별 문서 수 계산
        dominant_topics = doc_topic_dist.argmax(axis=1)
        topic_counts = pd.Series(dominant_topics).value_counts().sort_index()
        
        # Plotly 그래프 생성
        fig = go.Figure()
        
        # 토픽별 문서 수 바 차트
        fig.add_trace(go.Bar(
            x=[f"토픽 {i+1}<br>{topic_names[i]}" for i in range(n_topics)],
            y=topic_counts,
            marker_color='royalblue'
        ))
        
        # 레이아웃 설정
        fig.update_layout(
            title='토픽별 문서 분포',
            xaxis_title='토픽',
            yaxis_title='문서 수',
            height=500
        )
        
        # 토픽별 주요 단어 표 생성
        topic_words_table = pd.DataFrame({
            '토픽': [f"토픽 {i+1}" for i in range(n_topics)],
            '토픽명': topic_names,
            '주요 단어': [', '.join(words) for words in topic_words]
        }).to_html(index=False, escape=False)
        
        # HTML 결과 생성
        html_result = f"""
        <div class="topic-analysis">
            <h3>토픽 모델링 결과</h3>
            <div class="topic-distribution">
                {fig.to_html(include_plotlyjs=True, full_html=False)}
            </div>
            <div class="topic-words">
                <h4>토픽별 주요 단어</h4>
                {topic_words_table}
            </div>
        </div>
        """
        
        return html_result
        
    except Exception as e:
        print(f"토픽 분석 중 오류 발생: {e}")
        return None