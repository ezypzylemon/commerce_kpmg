import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
from collections import Counter, defaultdict
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go

def word_association_analysis(df, font_path):
    st.subheader("연관어 분석")
    
    # 모든 토큰 결합
    all_tokens = []
    for tokens in df['token_list']:
        all_tokens.extend(tokens)
    
    # 단어 빈도 계산
    word_counts = Counter(all_tokens)
    
    # 상위 단어 선택
    top_n = st.slider("분석할 상위 단어 수", 50, 500, 300)
    
    # 상위 N개 단어 선택
    top_words = [word for word, _ in word_counts.most_common(top_n)]
    
    # 최소 동시 출현 빈도 설정
    min_count = st.slider("최소 동시 출현 빈도", 2, 20, 5)
    
    # 연관어 분석 옵션
    association_options = [
        "단어 네트워크 분석",
        "특정 단어 연관어 분석",
        "동시 출현 히트맵"
    ]
    
    selected_association_option = st.radio(
        "분석 옵션 선택",
        options=association_options,
        horizontal=True
    )
    
    if selected_association_option == "단어 네트워크 분석":
        # 단어 동시 출현 행렬 생성
        st.subheader("단어 네트워크 분석")
        
        with st.spinner("단어 동시 출현 분석 중..."):
            # 단어 세트
            word_set = set(top_words)
            
            # 동시 출현 횟수 계산
            cooccurrence = defaultdict(int)
            
            for tokens in df['token_list']:
                # 선택된 단어만 필터링
                filtered_tokens = [token for token in tokens if token in word_set]
                
                # 같은 문서 내 단어 쌍 확인
                for i, word1 in enumerate(filtered_tokens):
                    for word2 in filtered_tokens[i+1:]:
                        if word1 != word2:
                            # 알파벳 순으로 정렬하여 중복 쌍 방지
                            pair = tuple(sorted([word1, word2]))
                            cooccurrence[pair] += 1
            
            # 네트워크 그래프 생성
            G = nx.Graph()
            
            # 노드 추가
            for word in word_set:
                G.add_node(word, count=word_counts[word])
            
            # 엣지 추가 (임계값 이상 공동 출현)
            for (word1, word2), count in cooccurrence.items():
                if count >= min_count:
                    G.add_edge(word1, word2, weight=count)
            
            st.success(f"네트워크 그래프 생성 완료: {G.number_of_nodes()}개 노드, {G.number_of_edges()}개 엣지")
        
        # 네트워크 시각화 설정
        max_nodes = st.slider("시각화할 최대 노드 수", 20, 200, 100)
        
        # 중심성 계산
        with st.spinner("네트워크 중심성 계산 중..."):
            # 노드 수가 많으면 계산에 시간이 오래 걸릴 수 있음
            if G.number_of_nodes() <= 1000:
                degree_centrality = nx.degree_centrality(G)
                
                # 상위 노드로 제한된 서브그래프
                top_nodes = sorted(degree_centrality.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
                top_node_names = [node for node, _ in top_nodes]
                
                G_vis = G.subgraph(top_node_names).copy()
                
                st.success("네트워크 중심성 계산 완료")
            else:
                # 노드가 너무 많은 경우 단순히 빈도 기준으로 필터링
                top_node_names = [word for word, _ in word_counts.most_common(max_nodes)]
                G_vis = G.subgraph(top_node_names).copy()
                
                st.warning("노드가 너무 많아 빈도 기준으로 필터링했습니다.")
        
        # 네트워크 시각화 생성
        with st.spinner("네트워크 시각화 생성 중..."):
            # 그래프를 Plotly로 시각화
            pos = nx.spring_layout(G_vis, seed=42)
            
            # 노드 좌표
            node_x = []
            node_y = []
            for node in G_vis.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
            
            # 노드 크기 (단어 빈도에 비례)
            node_size = [word_counts[node] / 10 for node in G_vis.nodes()]
            
            # 노드 텍스트
            node_text = []
            for node in G_vis.nodes():
                node_text.append(f"{node}<br>빈도: {word_counts[node]}")
            
            # 엣지 좌표
            edge_x = []
            edge_y = []
            
            for edge in G_vis.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.append(x0)
                edge_y.append(y0)
                edge_x.append(x1)
                edge_y.append(y1)
                edge_x.append(None)
                edge_y.append(None)
            
            # 엣지 트레이스
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            # 노드 트레이스
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=list(G_vis.nodes()),
                textposition="top center",
                hoverinfo='text',
                hovertext=node_text,
                marker=dict(
                    showscale=True,
                    colorscale='YlGnBu',
                    size=node_size,
                    colorbar=dict(
                        thickness=15,
                        title='단어 빈도',
                        xanchor='left',
                        titleside='right'
                    ),
                    color=[word_counts[node] for node in G_vis.nodes()],
                    line=dict(width=2)
                )
            )
            
            # 그래프 생성
            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              title='단어 연관 네트워크',
                              titlefont=dict(size=16),
                              showlegend=False,
                              hovermode='closest',
                              margin=dict(b=20,l=5,r=5,t=40),
                              annotations=[ dict(
                                  text="",
                                  showarrow=False,
                                  xref="paper", yref="paper"
                              ) ],
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              height=700
                          )
                         )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # 상위 중심 단어
        st.subheader("상위 중심 단어")
        
        centrality_df = pd.DataFrame({
            '단어': list(G_vis.nodes()),
            '빈도': [word_counts[node] for node in G_vis.nodes()],
            '연결 수': [G_vis.degree(node) for node in G_vis.nodes()]
        }).sort_values('연결 수', ascending=False).head(20)
        
        st.dataframe(centrality_df, use_container_width=True)
    
    elif selected_association_option == "특정 단어 연관어 분석":
        # 특정 단어 연관어 분석
        st.subheader("특정 단어 연관어 분석")
        
        # 분석할 단어 입력
        available_words = [word for word, count in word_counts.most_common(200)]
        target_word = st.selectbox("분석할 단어 선택", options=available_words)
        
        if target_word:
            # 단어 동시 출현 분석
            with st.spinner(f"'{target_word}'의 연관어 분석 중..."):
                # 해당 단어가 포함된 문서 찾기
                contains_word = [target_word in tokens for tokens in df['token_list']]
                docs_with_word = df[contains_word]
                
                # 연관 단어 빈도 계산
                related_words = Counter()
                
                for tokens in docs_with_word['token_list']:
                    # 대상 단어를 제외한 다른 단어 빈도 계산
                    for token in tokens:
                        if token != target_word:
                            related_words[token] += 1
                
                # 상위 연관어
                top_related = related_words.most_common(30)
                
                # 연관어 비율 계산 (해당 단어가 포함된 문서 대비)
                total_docs = len(docs_with_word)
                related_word_pct = [(word, count / total_docs * 100) for word, count in top_related]
                
                # 결과 데이터프레임
                related_df = pd.DataFrame(related_word_pct, columns=['단어', '출현 비율(%)'])
                
                st.success(f"'{target_word}'가 포함된 문서: {total_docs}개")
            
            # 결과 출력
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(related_df, use_container_width=True)
            
            with col2:
                # 상위 15개만 시각화
                fig = px.bar(
                    related_df.head(15), 
                    x='출현 비율(%)', 
                    y='단어',
                    orientation='h',
                    color='출현 비율(%)',
                    color_continuous_scale=px.colors.sequential.Viridis
                )
                
                fig.update_layout(
                    title=f"'{target_word}'의 주요 연관어 (상위 15개)",
                    yaxis={'categoryorder': 'total ascending'},
                    height=500
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # 단어 네트워크로 시각화
            st.subheader(f"'{target_word}'의 연관어 네트워크")
            
            # 상위 연관어만 사용
            top_related_words = [word for word, _ in top_related[:15]]
            top_related_words.append(target_word)
            
            # 동시 출현 행렬
            cooccurrence = defaultdict(int)
            
            for tokens in docs_with_word['token_list']:
                # 선택된 단어만 필터링
                filtered_tokens = [token for token in tokens if token in top_related_words]
                
                # 같은 문서 내 단어 쌍 확인
                for i, word1 in enumerate(filtered_tokens):
                    for word2 in filtered_tokens[i+1:]:
                        if word1 != word2:
                            pair = tuple(sorted([word1, word2]))
                            cooccurrence[pair] += 1
            
            # 그래프 생성
            G = nx.Graph()
            
            # 노드 추가
            for word in top_related_words:
                G.add_node(word)
            
            # 엣지 추가
            for (word1, word2), count in cooccurrence.items():
                if count >= 1:  # 최소 1번 이상 동시 출현
                    G.add_edge(word1, word2, weight=count)
            
            # 그래프를 Plotly로 시각화
            pos = nx.spring_layout(G, seed=42)
            
            # 노드 좌표
            node_x = []
            node_y = []
            for node in G.nodes():
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
            
            # 노드 크기 및 색상
            node_size = []
            node_color = []
            for node in G.nodes():
                if node == target_word:
                    node_size.append(40)  # 대상 단어는 더 크게
                    node_color.append('red')
                else:
                    node_size.append(20)
                    node_color.append('skyblue')
            
            # 엣지 좌표
            edge_x = []
            edge_y = []
            
            for edge in G.edges():
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.append(x0)
                edge_y.append(y0)
                edge_x.append(x1)
                edge_y.append(y1)
                edge_x.append(None)
                edge_y.append(None)
            
            # 엣지 트레이스
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=0.5, color='#888'),
                hoverinfo='none',
                mode='lines')
            
            # 노드 트레이스
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                text=list(G.nodes()),
                textposition="top center",
                hoverinfo='text',
                marker=dict(
                    size=node_size,
                    color=node_color,
                    line=dict(width=2)
                )
            )
            
            # 그래프 생성
            fig = go.Figure(data=[edge_trace, node_trace],
                          layout=go.Layout(
                              title=f"'{target_word}'의 연관어 네트워크",
                              titlefont=dict(size=16),
                              showlegend=False,
                              hovermode='closest',
                              margin=dict(b=20,l=5,r=5,t=40),
                              xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                              height=600
                          )
                         )
            
            st.plotly_chart(fig, use_container_width=True)
    
    elif selected_association_option == "동시 출현 히트맵":
        # 동시 출현 히트맵
        st.subheader("동시 출현 히트맵")
        
        # 표시할 단어 수 선택
        heatmap_words_count = st.slider("표시할 단어 수", 10, 50, 20)
        
        # 동시 출현 행렬 계산
        with st.spinner("동시 출현 행렬 계산 중..."):
            # 상위 단어 선택
            top_words_for_heatmap = [word for word, _ in word_counts.most_common(heatmap_words_count)]
            
            # 동시 출현 행렬 초기화
            cooc_matrix = np.zeros((len(top_words_for_heatmap), len(top_words_for_heatmap)))
            
            # 단어 인덱스 매핑
            word_to_idx = {word: i for i, word in enumerate(top_words_for_heatmap)}
            
            # 동시 출현 계산
            for tokens in df['token_list']:
                # 선택된 단어만 필터링
                filtered_tokens = [token for token in tokens if token in top_words_for_heatmap]
                
                # 같은 문서 내 단어 쌍 확인
                for i, word1 in enumerate(filtered_tokens):
                    for word2 in filtered_tokens[i:]:  # 자기 자신과의 관계도 포함
                        idx1, idx2 = word_to_idx[word1], word_to_idx[word2]
                        cooc_matrix[idx1, idx2] += 1
                        cooc_matrix[idx2, idx1] += 1  # 대칭 행렬
            
            # 자기 자신과의 관계는 0으로 설정 (선택 사항)
            for i in range(len(top_words_for_heatmap)):
                cooc_matrix[i, i] = 0
        
        # 히트맵 시각화
        fig = px.imshow(
            cooc_matrix,
            x=top_words_for_heatmap,
            y=top_words_for_heatmap,
            color_continuous_scale="Viridis",
            labels=dict(x="단어", y="단어", color="동시 출현 빈도")
        )
        
        fig.update_layout(
            title="주요 단어 간 동시 출현 히트맵",
            height=700,
            width=700
        )
        
        st.plotly_chart(fig, use_container_width=True)

def generate_network_graph(data):
    try:
        # 모든 토큰 결합
        all_tokens = []
        for tokens in data['tokens']:
            if isinstance(tokens, list):
                all_tokens.extend(tokens)
        
        # 단어 빈도수 계산 및 상위 50개 선택
        word_freq = Counter(all_tokens)
        top_words = [word for word, _ in word_freq.most_common(50)]
        
        # 동시 출현 횟수 계산
        cooccurrence = {}
        for tokens in data['tokens']:
            if not isinstance(tokens, list):
                continue
            # 상위 단어만 고려
            tokens = [t for t in tokens if t in top_words]
            for i, word1 in enumerate(tokens):
                for word2 in tokens[i+1:]:
                    if word1 != word2:
                        pair = tuple(sorted([word1, word2]))
                        cooccurrence[pair] = cooccurrence.get(pair, 0) + 1
        
        # 네트워크 그래프 생성
        G = nx.Graph()
        
        # 노드 추가
        for word in top_words:
            G.add_node(word, size=word_freq[word])
        
        # 엣지 추가 (가중치가 2 이상인 경우만)
        for (word1, word2), weight in cooccurrence.items():
            if weight >= 2:
                G.add_edge(word1, word2, weight=weight)
        
        # 노드 위치 계산
        pos = nx.spring_layout(G, k=1, iterations=50)
        
        # 엣지 트레이스
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.8, color='#888'),
            hoverinfo='none',
            mode='lines')
        
        # 노드 트레이스
        node_x = []
        node_y = []
        node_text = []
        node_size = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_size.append(G.nodes[node]['size'] * 2)
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="top center",
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                size=node_size,
                color=node_size,
                line=dict(width=2, color='#FFFFFF')
            )
        )
        
        # 레이아웃 설정
        layout = go.Layout(
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20,l=5,r=5,t=40),
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            title='키워드 연관성 네트워크'
        )
        
        # 그래프 생성
        fig = go.Figure(data=[edge_trace, node_trace], layout=layout)
        
        return fig.to_html(full_html=False)
        
    except Exception as e:
        print(f"네트워크 그래프 생성 중 오류 발생: {e}")
        return None