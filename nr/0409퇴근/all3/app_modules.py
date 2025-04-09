# 파일명: app_modules.py
from flask import render_template
import os
import pandas as pd
from datetime import datetime, timedelta
from collections import Counter
import logging

# 기존 모듈 임포트
from core.magazine_data_loader import MagazineDataLoader
from core.news_data_loader import NewsDataLoader
from core.visualizer import (
    generate_network_graph,
    generate_category_chart,
    generate_wordcloud,
    generate_tfidf_chart
)
from core.competitor_analyzer import generate_competitor_analysis, generate_competitor_analysis_by_date
from core.musinsa_module import MusinsaVisualizer

class DashboardModule:
    """통합 대시보드 관련 기능을 담당하는 클래스"""
    
    def __init__(self):
        self.data_loader = MagazineDataLoader()
        self.logger = logging.getLogger(__name__)
    
    def render_dashboard(self, period='7일', start_date=None, end_date=None):
        """대시보드 페이지 렌더링"""
        try:
            # 입력값 검증
            if period == 'custom':
                if not (start_date and end_date):
                    raise ValueError("직접 설정 시 시작일과 종료일이 필요합니다.")
                try:
                    start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
                except Exception as e:
                    raise ValueError(f"날짜 형식이 올바르지 않습니다: {e}")
                
                data = self.data_loader.load_data_by_date_range(start_date, end_date)
                display_period = f"{start_date} ~ {end_date}"
            else:
                if period not in ['7일', '2주', '1개월', '3개월', '6개월', '1년']:
                    self.logger.warning(f"지원하지 않는 기간: {period}, 기본값 '7일'로 설정")
                    period = '7일'
                data = self.data_loader.load_data_by_period(period)
                display_period = period

            if data is None or data.empty:
                return render_template('dashboard.html',
                                    error="해당 기간에 데이터가 없습니다.",
                                    period=period,
                                    start_date=start_date,
                                    end_date=end_date,
                                    magazine_data={},
                                    fig_network=None,
                                    fig_category=None,
                                    fig_wordcloud=None,
                                    fig_tfidf=None)

            # 시각화 생성
            fig_network = generate_network_graph(data)
            fig_category = generate_category_chart(data)
            fig_wordcloud = generate_wordcloud(data)
            fig_tfidf = generate_tfidf_chart(data)
            
            # 매거진별 데이터 수집
            magazine_data = {}
            for magazine in data['source'].unique():
                keywords = self.data_loader.get_magazine_keywords(magazine)
                card_news = self.data_loader.get_card_news(magazine)
                if keywords:
                    magazine_data[magazine] = {
                        'keywords': keywords,
                        'card_news': card_news
                    }

            return render_template('dashboard.html',
                                period=period,
                                display_period=display_period,
                                start_date=start_date,
                                end_date=end_date,
                                fig_network=fig_network,
                                fig_category=fig_category,
                                fig_wordcloud=fig_wordcloud,
                                fig_tfidf=fig_tfidf,
                                magazine_data=magazine_data)

        except ValueError as e:
            self.logger.error(f"입력값 오류: {e}")
            return render_template('dashboard.html',
                                error=str(e),
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                magazine_data={},
                                fig_network=None,
                                fig_category=None,
                                fig_wordcloud=None,
                                fig_tfidf=None)
        except Exception as e:
            self.logger.error(f"대시보드 렌더링 중 오류 발생: {e}", exc_info=True)
            return render_template('dashboard.html',
                                error="데이터 처리 중 오류가 발생했습니다.",
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                magazine_data={},
                                fig_network=None,
                                fig_category=None,
                                fig_wordcloud=None,
                                fig_tfidf=None)


# app_modules.py의 NewsModule 클래스 업데이트

class NewsModule:
    """뉴스 분석 관련 기능을 담당하는 클래스"""
    
    def __init__(self):
        """초기화"""
        self.data_loader = NewsDataLoader()
        self.logger = logging.getLogger(__name__)
        
        # NewsAnalyzer 초기화
        from core.news_analyzer import NewsAnalyzer
        self.analyzer = NewsAnalyzer()
    
    def render_news(self, period='7일', start_date=None, end_date=None):
        """뉴스 분석 페이지 렌더링"""
        try:
            # 입력값 검증
            if period == 'custom':
                if not (start_date and end_date):
                    raise ValueError("직접 설정 시 시작일과 종료일이 필요합니다.")
                try:
                    start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
                except Exception as e:
                    raise ValueError(f"날짜 형식이 올바르지 않습니다: {e}")
                
                data = self.data_loader.load_data_by_date_range(start_date, end_date)
                display_period = f"{start_date} ~ {end_date}"
            else:
                if period not in ['7일', '2주', '1개월', '3개월', '6개월', '1년']:
                    self.logger.warning(f"지원하지 않는 기간: {period}, 기본값 '7일'로 설정")
                    period = '7일'
                data = self.data_loader.load_data_by_period(period)
                display_period = period

            if data is None or data.empty:
                return render_template('news.html',
                                    error="해당 기간에 데이터가 없습니다.",
                                    period=period,
                                    start_date=start_date,
                                    end_date=end_date,
                                    news_articles=[])

            # NewsAnalyzer에 데이터 설정
            self.analyzer.set_data(data)
            
            # 대시보드 데이터 생성
            dashboard_data = self.analyzer.generate_dashboard_data()
            
            # 최신 뉴스 기사
            latest_articles = data.sort_values('published', ascending=False).head(10).to_dict('records')
            
            # 상위 키워드 추출
            freq_results = self.analyzer.analyze_word_frequency()
            top_keywords = self.analyzer.get_top_words(freq_results, top_n=5)
            
            # 감성 분석
            sentiment_df = self.analyzer.calculate_article_sentiment()
            sentiment_results = self.analyzer.get_sentiment_distribution(sentiment_df)
            
            # 긍정/부정 기사
            positive_articles = sentiment_results['positive_articles'][:3] if sentiment_results else []
            negative_articles = sentiment_results['negative_articles'][:3] if sentiment_results else []
            
            return render_template('news.html',
                                period=period,
                                display_period=display_period,
                                start_date=start_date,
                                end_date=end_date,
                                latest_articles=latest_articles,
                                top_keywords=top_keywords,
                                keyword_trend=dashboard_data.get('keyword_trend'),
                                tfidf_wordcloud=dashboard_data.get('wordcloud'),
                                keyword_network=dashboard_data.get('keyword_network'),
                                positive_articles=positive_articles,
                                negative_articles=negative_articles)

        except ValueError as e:
            self.logger.error(f"입력값 오류: {e}")
            return render_template('news.html',
                                error=str(e),
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                news_articles=[])
        except Exception as e:
            self.logger.error(f"뉴스 렌더링 중 오류 발생: {e}", exc_info=True)
            return render_template('news.html',
                                error="데이터 처리 중 오류가 발생했습니다.",
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                news_articles=[])
    
    def _analyze_news(self, data):
        """뉴스 데이터 분석"""
        try:
            # 기본적인 뉴스 데이터 분석
            news_analysis = {
                'total_articles': len(data),
                'sources': data['source'].value_counts().to_dict() if 'source' in data.columns else {},
                'recent_date': data['date'].max() if 'date' in data.columns else None
            }
            return news_analysis
        except Exception as e:
            self.logger.error(f"뉴스 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _analyze_trends(self, data):
        """트렌드 분석"""
        try:
            # 날짜별 기사 수 계산
            if 'date' in data.columns:
                date_counts = data.groupby('date').size().to_dict()
            else:
                date_counts = {}
            
            trends = {
                'date_counts': date_counts
            }
            return trends
        except Exception as e:
            self.logger.error(f"트렌드 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _extract_keywords(self, data):
        """키워드 추출"""
        try:
            # 모든 토큰 추출
            all_tokens = []
            if 'tokens' in data.columns:
                for tokens in data['tokens']:
                    if isinstance(tokens, list):
                        all_tokens.extend(tokens)
                    
            # 빈도수 계산
            keyword_counts = pd.Series(all_tokens).value_counts().head(20).to_dict()
            
            return keyword_counts
        except Exception as e:
            self.logger.error(f"키워드 추출 중 오류: {e}", exc_info=True)
            return {}


# app_modules.py의 MusinsaModule 클래스 수정 (디버깅 코드 추가)
class MusinsaModule:
    """무신사 경쟁사 분석 관련 기능을 담당하는 클래스"""
    
    def __init__(self):
        self.data_dir = os.path.join('data')
        self.logger = logging.getLogger(__name__)
        
        # 직접 CSV 로더 사용
        from core.musinsa_module import MusinsaVisualizer
        self.visualizer = MusinsaVisualizer()
        self.logger.info(f"무신사 모듈 초기화: 데이터 디렉토리 = {os.path.abspath(self.data_dir)}")
        
    def render_musinsa(self, period='7일', start_date=None, end_date=None):
        """무신사 경쟁사 분석 페이지를 렌더링하는 함수"""
        try:
            # CSV 파일 직접 로드
            file_path = os.path.join(self.data_dir, 'musinsa_data.csv')
            self.logger.info(f"무신사 데이터 파일 경로: {os.path.abspath(file_path)}")
            
            if not os.path.exists(file_path):
                self.logger.error(f"무신사 데이터 파일을 찾을 수 없습니다: {file_path}")
                return render_template('musinsa.html', 
                                      error=f"데이터 파일을 찾을 수 없습니다: {file_path}",
                                      period=period)
            
            display_period = period
            if period == 'custom' and start_date and end_date:
                display_period = f"{start_date} ~ {end_date}"
            
            # 시각화 모듈을 통해 데이터 로드
            data = self.visualizer.load_data(file_path, period)
            self.logger.info(f"데이터 로드 완료: {len(data)}행")
            
            # 데이터 검증
            if data is None or data.empty:
                self.logger.warning(f"데이터가 없습니다: 기간 = {period}")
                return render_template('musinsa.html', 
                                      error="해당 기간에 대한 데이터가 없습니다.",
                                      period=period)
            
            # 데이터 분석 진행
            result = self._generate_musinsa_analysis(data, period)
            
            # 브랜드별 가격 범위 차트 생성
            try:
                price_range_chart = self.visualizer.generate_price_range_chart(data, period)
                # 결과에 추가
                result['price_range_chart'] = price_range_chart
            except Exception as chart_e:
                self.logger.error(f"가격 범위 차트 생성 중 오류: {chart_e}", exc_info=True)
            
            # 기본 정보 추가
            result['period'] = period
            result['start_date'] = start_date
            result['end_date'] = end_date
            result['display_period'] = display_period
            
            # 템플릿 렌더링
            return render_template('musinsa.html', **result)
            
        except Exception as e:
            self.logger.error(f"무신사 렌더링 중 오류: {e}", exc_info=True)
            return render_template('musinsa.html', 
                                  error=f"데이터 분석 중 오류가 발생했습니다: {str(e)}", 
                                  period=period)
    
    def _generate_musinsa_analysis(self, data, period):
        """무신사 분석 결과 생성 함수"""
        try:
            # 디버깅: 데이터 로드 정보
            self.logger.info(f"무신사 분석 시작: 데이터 크기 = {len(data)}")
            self.logger.info(f"컬럼 목록: {list(data.columns)}")
            self.logger.info(f"데이터 샘플:\n{data.head().to_string()}")
            self.logger.info(f"데이터 타입:\n{data.dtypes}")
            
            # 결과 객체 초기화
            result = {}
            
            # 기본 통계 정보 추가
            total_items = len(data)
            result['total_items'] = total_items
            
            # 브랜드 수
            if 'brand' in data.columns:
                total_brands = data['brand'].nunique()
                result['total_brands'] = total_brands
            else:
                result['total_brands'] = 0
            
            # 카테고리 수
            if 'category' in data.columns:
                total_categories = data['category'].nunique()
                result['total_categories'] = total_categories
            else:
                result['total_categories'] = 0
            
            # 평균 가격
            if 'price' in data.columns:
                try:
                    # 숫자로 변환 가능한 값만 추출
                    price_numeric = pd.to_numeric(data['price'].str.replace(',', '').str.replace('원', ''), errors='coerce')
                    avg_price = price_numeric.mean()
                    result['avg_price'] = avg_price
                except Exception as e:
                    self.logger.warning(f"가격 계산 중 오류: {e}")
                    result['avg_price'] = 0
            else:
                result['avg_price'] = 0
            
            # 카테고리 비율 및 증감률 차트 생성
            try:
                category_ratio_charts = self.visualizer.generate_category_ratio_charts(data, period)
                
                # 결과에 차트 경로 추가
                if category_ratio_charts:
                    self.logger.info(f"카테고리 비율 차트 생성 성공: {category_ratio_charts}")
                    result['category_ratio_charts'] = category_ratio_charts
            except Exception as e:
                self.logger.error(f"카테고리 비율 차트 생성 중 오류: {e}", exc_info=True)
            
            # 남성/여성 인기 아이템 데이터 추가
            try:
                # 남성/여성 인기 아이템 분리
                top_male_items = []
                top_female_items = []
                
                if 'gender' in data.columns and 'name' in data.columns:
                    # 남성 아이템
                    male_df = data[data['gender'] == '남성']
                    if not male_df.empty:
                        male_items = male_df['name'].value_counts().head(5)
                        top_male_items = [{'name': name, 'count': count} for name, count in male_items.items()]
                    
                    # 여성 아이템
                    female_df = data[data['gender'] == '여성']
                    if not female_df.empty:
                        female_items = female_df['name'].value_counts().head(5)
                        top_female_items = [{'name': name, 'count': count} for name, count in female_items.items()]
                
                # 결과에 추가
                result['top_male_items'] = top_male_items
                result['top_female_items'] = top_female_items
            except Exception as e:
                self.logger.error(f"인기 아이템 데이터 추가 중 오류: {e}")
                result['top_male_items'] = []
                result['top_female_items'] = []
            
            # 인기 브랜드 TOP 20
            try:
                if 'brand' in data.columns:
                    # 시각화를 위한 브랜드 랭킹 데이터 가져오기
                    top_brands = self.visualizer.get_popular_brands(data, top_n=20)
                    result['top_brands'] = top_brands
                    self.logger.info(f"인기 브랜드 TOP 20 추출 완료: {len(top_brands)}개")
                else:
                    result['top_brands'] = []
            except Exception as e:
                self.logger.error(f"인기 브랜드 추출 중 오류: {e}")
                result['top_brands'] = []
            
            # 디버깅 정보 추가
            result['debug_info'] = {
                'keys': list(result.keys()),
                'sample_data': {k: str(result[k])[:100] + '...' if isinstance(result[k], (dict, list, str)) and len(str(result[k])) > 100 else result[k] for k in result.keys()}
            }
            
            self.logger.info(f"무신사 분석 완료: 결과 키 = {list(result.keys())}")
            return result
            
        except Exception as e:
            self.logger.error(f"무신사 분석 결과 생성 중 오류: {e}", exc_info=True)
            return {}


class MagazineModule:
    """매거진 분석 관련 기능을 담당하는 클래스"""
    
    def __init__(self):
        self.data_loader = MagazineDataLoader()
        self.logger = logging.getLogger(__name__)
    
    def render_magazine(self, period='7일', start_date=None, end_date=None, selected_magazines=None):
        """매거진 분석 페이지 렌더링"""
        try:
            # 기본 매거진 리스트 설정
            all_magazines = ['jentestore', 'marieclaire', 'vogue', 'wkorea', 'wwdkorea']
            
            if selected_magazines is None:
                selected_magazines = all_magazines.copy()
            elif isinstance(selected_magazines, str):
                selected_magazines = [m.strip() for m in selected_magazines.split(',') if m.strip()]
            
            # selected_magazines가 비어있으면 모든 매거진 선택
            if not selected_magazines:
                selected_magazines = all_magazines.copy()
            
            # 로깅 추가
            self.logger.info(f"선택된 매거진: {selected_magazines}")
            
            # 입력값 검증
            if period == 'custom':
                if not (start_date and end_date):
                    raise ValueError("직접 설정 시 시작일과 종료일이 필요합니다.")
                try:
                    start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
                    end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')
                except Exception as e:
                    raise ValueError(f"날짜 형식이 올바르지 않습니다: {e}")
                
                data = self.data_loader.load_data_by_date_range(start_date, end_date)
                display_period = f"{start_date} ~ {end_date}"
            else:
                if period not in ['7일', '2주', '1개월', '3개월', '6개월', '1년']:
                    self.logger.warning(f"지원하지 않는 기간: {period}, 기본값 '7일'로 설정")
                    period = '7일'
                data = self.data_loader.load_data_by_period(period)
                display_period = period

            # magazine_data 초기화
            magazine_data = {}
            
            # 모든 카드뉴스를 담을 리스트
            all_card_news = []
            
            # 매거진별 카드뉴스 수집
            for magazine_name in selected_magazines:
                card_news = self.data_loader.get_card_news(magazine_name)
                
                # 로깅 추가
                self.logger.info(f"매거진 '{magazine_name}' 카드뉴스 수: {len(card_news) if card_news else 0}")
                
                if card_news:
                    # 카드뉴스의 매거진 정보 확인
                    for article in card_news:
                        source = article.get('source', '').lower()
                        title = article.get('title', '')[:30]
                        self.logger.debug(f"카드뉴스 추가: {title}... (출처: {source})")
                    
                    all_card_news.extend(card_news)
                
                # 키워드 데이터 가져오기
                keywords = self.data_loader.get_magazine_keywords(magazine_name)
                if keywords:
                    magazine_data[magazine_name] = {
                        'keywords': keywords
                    }
            
            # 매거진별 카드뉴스 현황 로깅
            magazine_counts = {}
            for article in all_card_news:
                source = article.get('source', '').lower()
                if source in magazine_counts:
                    magazine_counts[source] += 1
                else:
                    magazine_counts[source] = 1
            
            self.logger.info(f"매거진별 카드뉴스 수집 결과: {magazine_counts}")
            
            # 최신순 정렬
            all_card_news.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
            
            # 데이터 처리 및 시각화
            magazine_analysis = self._analyze_magazines(data) if hasattr(self, '_analyze_magazines') else {}
            content_trends = self._analyze_content_trends(data) if hasattr(self, '_analyze_content_trends') else {}
            topic_analysis = self._analyze_topics(data) if hasattr(self, '_analyze_topics') else {}
            
            # 공통 키워드 찾기
            common_keywords = []
            all_keywords = set()
            all_keywords_count = {}

            # 각 매거진에서 키워드 수집 및 카운트
            for magazine, info in magazine_data.items():
                if 'keywords' in info:
                    for keyword_item in info['keywords']:
                        keyword = keyword_item['keyword']
                        all_keywords.add(keyword)
                        if keyword in all_keywords_count:
                            all_keywords_count[keyword] += 1
                        else:
                            all_keywords_count[keyword] = 1

            # 모든 매거진에 공통된 키워드 찾기
            min_magazines = max(1, len(magazine_data) // 2)  # 최소한 절반 이상의 매거진에서 등장
            for keyword, count in all_keywords_count.items():
                if count >= min_magazines:
                    common_keywords.append(keyword)

            # 최대 5개만 사용
            common_keywords = common_keywords[:5]
            
            self.logger.info(f"공통 키워드 추출: {common_keywords}")
            
            # 시각화 생성
            try:
                visualizations = self.data_loader.generate_visualizations(
                    data=data,
                    selected_magazines=selected_magazines,
                    focus_keywords=common_keywords
                )
                
                fig_trend = visualizations.get('trend') if visualizations else None
                fig_wordcloud = visualizations.get('wordcloud') if visualizations else None
                fig_network = visualizations.get('network') if visualizations else None
                fig_category = visualizations.get('category') if visualizations else None
                
            except Exception as viz_error:
                self.logger.error(f"시각화 생성 중 오류: {viz_error}", exc_info=True)
                fig_trend = fig_wordcloud = fig_network = fig_category = None

            return render_template('magazine.html',
                                magazine_analysis=magazine_analysis,
                                content_trends=content_trends,
                                topic_analysis=topic_analysis,
                                period=period,
                                display_period=display_period,
                                start_date=start_date,
                                end_date=end_date,
                                magazine_data=magazine_data,
                                selected_magazines=selected_magazines,
                                common_keywords=common_keywords,
                                articles=all_card_news,
                                fig_trend=fig_trend,
                                fig_wordcloud=fig_wordcloud,
                                fig_network=fig_network,
                                fig_category=fig_category)

        except ValueError as e:
            self.logger.error(f"입력값 오류: {e}")
            return render_template('magazine.html',
                                error=str(e),
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                magazine_data={},
                                selected_magazines=selected_magazines if selected_magazines else [],
                                articles=[])
        except Exception as e:
            self.logger.error(f"매거진 렌더링 중 오류 발생: {e}", exc_info=True)
            return render_template('magazine.html',
                                error="데이터 처리 중 오류가 발생했습니다.",
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                magazine_data={},
                                selected_magazines=selected_magazines if selected_magazines else [],
                                articles=[])
    
    def _analyze_magazines(self, data):
        """매거진 데이터 분석"""
        try:
            magazine_analysis = {
                'total_articles': len(data),
                'publishers': data['source'].value_counts().to_dict()
            }
            return magazine_analysis
        except Exception as e:
            self.logger.error(f"매거진 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _analyze_content_trends(self, data):
        """콘텐츠 트렌드 분석"""
        try:
            # upload_date 컬럼이 있는지 확인
            if 'upload_date' not in data.columns:
                self.logger.warning("upload_date 컬럼이 없습니다.")
                return {}
            
            # datetime 형식으로 변환
            try:
                data = data.copy()
                data['upload_date'] = pd.to_datetime(data['upload_date'])
            except Exception as e:
                self.logger.error(f"날짜 변환 중 오류: {e}")
                return {}
            
            # 날짜별 집계
            daily_counts = data.groupby(data['upload_date'].dt.date).size().to_dict()
            
            content_trends = {
                'daily_counts': daily_counts
            }
            return content_trends
        except Exception as e:
            self.logger.error(f"콘텐츠 트렌드 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _analyze_topics(self, data):
        """토픽 분석"""
        try:
            # 모든 토큰 추출
            all_tokens = []
            for tokens in data['tokens']:
                if isinstance(tokens, list):
                    all_tokens.extend(tokens)
                    
            # 빈도수 계산
            topic_counts = pd.Series(all_tokens).value_counts().head(20).to_dict()
            
            topic_analysis = {
                'top_topics': topic_counts
            }
            return topic_analysis
        except Exception as e:
            self.logger.error(f"토픽 분석 중 오류: {e}", exc_info=True)
            return {}