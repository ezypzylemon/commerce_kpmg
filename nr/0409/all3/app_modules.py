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


class MusinsaModule:
    """무신사 경쟁사 분석 관련 기능을 담당하는 클래스"""
    
    def __init__(self):
        self.data_dir = os.path.join('data')
        self.logger = logging.getLogger(__name__)
        # 데이터 로더 추가
        from core.musinsa_data_loader import MusinsaDataLoader
        self.data_loader = MusinsaDataLoader()
    
    def render_musinsa(self, period='7일', start_date=None, end_date=None):
        """무신사 경쟁사 분석 페이지 렌더링"""
        try:
            # 데이터 파일 경로
            data_path = os.path.join(self.data_dir, 'musinsa_data.csv')
            display_period = period
            
            # 파일 기반 분석 사용
            try:
                if period == 'custom' and start_date and end_date:
                    # 날짜 형식 검증
                    try:
                        pd.to_datetime(start_date)
                        pd.to_datetime(end_date)
                    except Exception as e:
                        raise ValueError(f"날짜 형식이 올바르지 않습니다: {e}")
                    
                    result = generate_competitor_analysis_by_date(data_path, start_date, end_date)
                    display_period = f"{start_date} ~ {end_date}"
                else:
                    if period not in ['7일', '2주', '1개월', '3개월', '6개월', '1년']:
                        self.logger.warning(f"지원하지 않는 기간: {period}, 기본값 '1개월'로 설정")
                        period = '1개월'
                    
                    result = generate_competitor_analysis(data_path, period)
                    display_period = period
                
                if result is None:
                    error_message = "해당 기간에 데이터가 없습니다."
                    return render_template('musinsa.html', 
                                        error=error_message, 
                                        period=period,
                                        start_date=start_date,
                                        end_date=end_date,
                                        display_period=display_period)
                
                return render_template('musinsa.html',
                                    period=period,
                                    start_date=start_date,
                                    end_date=end_date,
                                    display_period=display_period,
                                    **result)
            except FileNotFoundError:
                self.logger.warning(f"무신사 데이터 파일({data_path})을 찾을 수 없습니다. 데이터베이스에서 로드를 시도합니다.")
                # 파일이 없는 경우 데이터베이스 로드 시도
                if period == 'custom' and start_date and end_date:
                    data = self.data_loader.load_data_by_date_range(start_date, end_date)
                    display_period = f"{start_date} ~ {end_date}"
                else:
                    data = self.data_loader.load_data_by_period(period)
                
                if data is None or data.empty:
                    return render_template('musinsa.html',
                                        error="해당 기간에 데이터가 없습니다.",
                                        period=period,
                                        start_date=start_date,
                                        end_date=end_date,
                                        display_period=display_period)
                
                # 데이터 처리 및 시각화
                competitor_analysis = self._analyze_competitors(data)
                market_trends = self._analyze_market_trends(data)
                product_insights = self._analyze_products(data)
                
                return render_template('musinsa.html',
                                    competitor_analysis=competitor_analysis,
                                    market_trends=market_trends,
                                    product_insights=product_insights,
                                    period=period,
                                    display_period=display_period,
                                    start_date=start_date,
                                    end_date=end_date)
            except Exception as e:
                self.logger.error(f"데이터 분석 중 오류 발생: {e}", exc_info=True)
                return render_template('musinsa.html',
                                    error=f"데이터 분석 중 오류가 발생했습니다: {str(e)}", 
                                    period=period,
                                    start_date=start_date,
                                    end_date=end_date,
                                    display_period=display_period)

        except ValueError as e:
            self.logger.error(f"입력값 오류: {e}")
            return render_template('musinsa.html',
                                error=str(e),
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                display_period=display_period)
        except Exception as e:
            self.logger.error(f"무신사 렌더링 중 오류 발생: {e}", exc_info=True)
            return render_template('musinsa.html',
                                error="데이터 처리 중 오류가 발생했습니다.",
                                period=period,
                                start_date=start_date,
                                end_date=end_date,
                                display_period=display_period)
    
    def _analyze_competitors(self, data):
        """경쟁사 분석"""
        try:
            return {'competitor_data': data.head(10).to_dict('records')}
        except Exception as e:
            self.logger.error(f"경쟁사 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _analyze_market_trends(self, data):
        """시장 트렌드 분석"""
        try:
            return {'trend_data': data.head(10).to_dict('records')}
        except Exception as e:
            self.logger.error(f"시장 트렌드 분석 중 오류: {e}", exc_info=True)
            return {}
    
    def _analyze_products(self, data):
        """제품 인사이트 분석"""
        try:
            return {'product_data': data.head(10).to_dict('records')}
        except Exception as e:
            self.logger.error(f"제품 인사이트 분석 중 오류: {e}", exc_info=True)
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