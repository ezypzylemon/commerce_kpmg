import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 데이터 파일 경로
INVENTORY_FILE = "inventory_data.csv"
PAYMENT_FILE = "payment_data.csv"
SHIPPING_FILE = "shipping_data.csv"
BRAND_FILE = "brand_data.csv"
PRODUCT_FILE = "product_data.csv"
INBOUND_FILE = "inbound_data.csv"
OUTBOUND_FILE = "outbound_data.csv"

# 데이터 로드 함수
def load_data(file, columns):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=columns)

def save_data(df, file):
    df.to_csv(file, index=False)

# 데이터 로드
df_inventory = load_data(INVENTORY_FILE, [
    "SEASON", "PICTURE", "BRAND", "STYLE", "ONLINE CODE (BO)", "ITEM", "MATERIAL", "ITEM CODE", "FABRIC",
    "COLOR (ORIGINAL)", "COLOR CODE", "DESCRIPTION", "SIZE", "QTY PER SIZE", "CURRENCY", "QTY (TOTAL)",
    "UNIT PRICE (SUPPLY)", "AMOUNT (TOTAL)", "SUPPLIER", "ENTRY DATE", "SHIPPING DATE", "PAYMENT TERMS (T/T, L/C, D/A)",
    "ENTRY YEAR", "ENTRY QUARTER"
])
df_shipping = load_data(SHIPPING_FILE, [
    "SHIPMENT ID", "B/L NUMBER", "INVOICE NUMBER", "PACKING LIST ID", "ORIGIN CERTIFICATE", "IMPORT DECLARATION", 
    "SHIPMENT DATE", "ARRIVAL DATE", "SHIPPING STATUS"
])
df_payment = load_data(PAYMENT_FILE, [
    "PAYMENT ID", "INVOICE NUMBER", "PAYMENT TYPE", "BANK NAME", "ACCOUNT NUMBER", "AMOUNT", "PAYMENT STATUS", "PAYMENT DATE"
])
df_brand = load_data(BRAND_FILE, [
    "BRAND ID", "BRAND NAME", "BUYING CONTRACT", "QC REPORT", "PRICE LIST", "LOOKBOOK", "CREATED AT"
])
df_product = load_data(PRODUCT_FILE, [
    "PRODUCT ID", "PRODUCT NAME", "CATEGORY", "BRAND", "SUPPLIER", "UNIT PRICE", "STOCK LEVEL"
])
df_inbound = load_data(INBOUND_FILE, [
    "INBOUND ID", "PRODUCT ID", "QUANTITY", "SUPPLIER", "DATE"
])
df_outbound = load_data(OUTBOUND_FILE, [
    "OUTBOUND ID", "PRODUCT ID", "QUANTITY", "CUSTOMER", "DATE"
])

# 날짜 필드 변환
df_inventory["ENTRY DATE"] = pd.to_datetime(df_inventory["ENTRY DATE"], errors='coerce')
df_inventory["ENTRY YEAR"] = df_inventory["ENTRY DATE"].dt.year
df_inventory["ENTRY QUARTER"] = df_inventory["ENTRY DATE"].dt.to_period("Q").astype(str)
df_inventory["MONTH"] = df_inventory["ENTRY DATE"].dt.to_period("M").astype(str)

# Streamlit 대시보드 구현
st.title("📦 글로벌 바잉 AMD 관리 시스템")

# 사이드바 메뉴
menu = st.sidebar.radio("메뉴 선택", [
    "대시보드", "재고 관리", "입출고 현황", "선적 서류 관리", "결제 관리", "브랜드 관리", "데이터 업로드 (CSV)"
])

if menu == "대시보드":
    st.subheader("📊 대시보드 현황판")
    
    if not df_inventory.empty:
        # 재고 현황
        st.subheader("🏭 재고 현황")
        stock_summary = df_inventory.groupby("BRAND")["QTY (TOTAL)"].sum().reset_index()
        st.dataframe(stock_summary)
        fig = px.bar(stock_summary, x="BRAND", y="QTY (TOTAL)", title="브랜드별 재고 현황")
        st.plotly_chart(fig, use_container_width=True)
        
        # 입출고 현황
        st.subheader("📈 입출고 현황")
        inbound_summary = df_inbound.groupby("DATE")["QUANTITY"].sum().reset_index()
        outbound_summary = df_outbound.groupby("DATE")["QUANTITY"].sum().reset_index()
        fig = px.line(inbound_summary, x="DATE", y="QUANTITY", title="입고량 추이", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        fig = px.line(outbound_summary, x="DATE", y="QUANTITY", title="출고량 추이", markers=True)
        st.plotly_chart(fig, use_container_width=True)

elif menu == "입출고 현황":
    st.subheader("📦 품목별 입출고 현황")
    st.dataframe(pd.merge(df_inbound, df_outbound, on="PRODUCT ID", how="outer"))

elif menu == "재고 관리":
    st.subheader("📊 재고 관리 현황")
    st.dataframe(df_inventory)

elif menu == "선적 서류 관리":
    st.subheader("🚢 선적 서류 관리")
    st.dataframe(df_shipping)

elif menu == "결제 관리":
    st.subheader("💳 결제 관리")
    st.dataframe(df_payment)

elif menu == "브랜드 관리":
    st.subheader("🏷️ 브랜드 관리")
    st.dataframe(df_brand)

elif menu == "데이터 업로드 (CSV)":
    st.subheader("📤 CSV 파일 업로드")
    uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
    if uploaded_file is not None:
        new_data = pd.read_csv(uploaded_file)
        category = st.selectbox("업로드할 데이터 카테고리", ["재고", "입고", "출고", "선적", "결제", "브랜드"])
        if category == "입고":
            df_inbound = pd.concat([df_inbound, new_data], ignore_index=True)
            save_data(df_inbound, INBOUND_FILE)
        elif category == "출고":
            df_outbound = pd.concat([df_outbound, new_data], ignore_index=True)
            save_data(df_outbound, OUTBOUND_FILE)
        st.success("CSV 파일 업로드 완료!")
        st.experimental_rerun()

st.sidebar.subheader("📋 최신 거래 내역")
st.sidebar.dataframe(df_inventory)
