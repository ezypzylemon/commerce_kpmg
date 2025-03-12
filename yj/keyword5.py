import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

def load_data():
    file_path = "/Users/jiyeonjoo/Desktop/최종 플젝/연관키워드 20250311 1634.xlsx"
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
    df['Total_Search'] = df['Search_PC'].astype(str).str.replace(',', '').astype(float) + df['Search_Mobile'].astype(str).str.replace(',', '').astype(float)
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
    
    st.subheader("📊 클러스터별 키워드 분석 및 AI 인사이트")
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

def main():
    st.title("📊 키워드 분석 대시보드")
    df = load_data()
    
    identify_core_keywords(df)
    sns_keywords_and_item_dashboard(df)

if __name__ == "__main__":
    main()
