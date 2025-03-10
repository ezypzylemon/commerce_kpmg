import React, { useState, useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Calendar, ChevronDown, Flag, Package, CreditCard, MessageSquare, Clock, DollarSign, AlertTriangle } from 'lucide-react';

interface Message {
  role: 'assistant' | 'user';
  content: string;
}

interface BrandData {
  brand: string;
  season: string;
  shipmentStatus: string;
  shipmentDate: string;
  paymentTerms: string;
  paymentStatus: string;
  paymentDueDate: string;
  totalAmount: number;
  currency: string;
  exchangeRate: number;
  amountKRW: number;
  documentDate: string;
  ocFile: string;
  invoiceFile: string | null;
  lastUpdated: string;
}

const IntegratedBuyingDashboard = () => {
  const [chatOpen, setChatOpen] = useState<boolean>(false);
  const [userInput, setUserInput] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: '안녕하세요! 구매 관리 어시스턴트입니다. 무엇을 도와드릴까요?' }
  ]);

  // OCR로 추출하여 DBMS에 저장된 브랜드별 입고/결제 정보 (샘플 데이터)
  const brandPaymentData: BrandData[] = [
    { 
      brand: 'TOGA VIRILIS', 
      season: '2024SS',
      shipmentStatus: '입고완료',
      shipmentDate: '2025-03-01',
      paymentTerms: '40% BEF. PROD - 60% AT 30 DAYS',
      paymentStatus: '결제대기',
      paymentDueDate: '2025-03-31',
      totalAmount: 5600.00,
      currency: 'EUR',
      exchangeRate: 1458.75,
      amountKRW: 8169000,
      documentDate: '2023-07-26',
      ocFile: 'oc_document.pdf',
      invoiceFile: 'invoice_document.pdf',
      lastUpdated: '2025-03-10'
    },
    { 
      brand: 'ATHLETICS FTWR', 
      season: '2024SS',
      shipmentStatus: '입고완료',
      shipmentDate: '2025-02-15',
      paymentTerms: '50% DEPOSIT - 50% BEFORE SHIPPING',
      paymentStatus: '결제대기',
      paymentDueDate: '2025-03-15',
      totalAmount: 8200.00,
      currency: 'USD',
      exchangeRate: 1342.50,
      amountKRW: 11008500,
      documentDate: '2023-08-05',
      ocFile: 'athletics_order.pdf',
      invoiceFile: 'athletics_invoice.pdf',
      lastUpdated: '2025-03-05'
    },
    { 
      brand: 'NOU NOU', 
      season: '2024SS',
      shipmentStatus: '입고중',
      shipmentDate: '2025-03-20',
      paymentTerms: '100% AFTER DELIVERY',
      paymentStatus: '결제예정',
      paymentDueDate: '2025-04-20',
      totalAmount: 4600000,
      currency: 'KRW',
      exchangeRate: 1,
      amountKRW: 4600000,
      documentDate: '2023-09-10',
      ocFile: 'nounou_order.pdf',
      invoiceFile: 'nounou_invoice.pdf',
      lastUpdated: '2025-03-08'
    },
    { 
      brand: 'WILD DONKEY', 
      season: '2024SS',
      shipmentStatus: '출고대기',
      shipmentDate: '2025-04-15',
      paymentTerms: '30% DEPOSIT - 70% ON DELIVERY',
      paymentStatus: '일부결제',
      paymentDueDate: '2025-04-30',
      totalAmount: 3500.00,
      currency: 'EUR',
      exchangeRate: 1458.75,
      amountKRW: 5105625,
      documentDate: '2023-10-02',
      ocFile: 'wilddonkey_order.pdf',
      invoiceFile: 'wilddonkey_invoice.pdf',
      lastUpdated: '2025-03-01'
    },
    { 
      brand: 'BASERANGE', 
      season: '2024SS',
      shipmentStatus: '입고지연',
      shipmentDate: '2025-04-10',
      paymentTerms: '50% ON ORDER - 50% ON DELIVERY',
      paymentStatus: '일부결제',
      paymentDueDate: '2025-04-15',
      totalAmount: 4200.00,
      currency: 'EUR',
      exchangeRate: 1458.75,
      amountKRW: 6126750,
      documentDate: '2023-09-15',
      ocFile: 'baserange_order.pdf',
      invoiceFile: 'baserange_invoice.pdf',
      lastUpdated: '2025-03-07'
    },
    { 
      brand: 'GARBSTORE', 
      season: '2024SS',
      shipmentStatus: '입고예정',
      shipmentDate: '2025-05-01',
      paymentTerms: 'NET 30 FROM INVOICE',
      paymentStatus: '미결제',
      paymentDueDate: '2025-06-01',
      totalAmount: 2800.00,
      currency: 'GBP',
      exchangeRate: 1702.30,
      amountKRW: 4766440,
      documentDate: '2023-11-04',
      ocFile: 'garbstore_order.pdf',
      invoiceFile: null,
      lastUpdated: '2025-02-28'
    }
  ];

  const today = useMemo(() => new Date(), []);
  
  const upcomingPayments = useMemo(() => 
    brandPaymentData
      .filter(brand => {
        const dueDate = new Date(brand.paymentDueDate);
        const diffTime = dueDate.getTime() - today.getTime();
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 14 && diffDays >= 0 && 
               ['결제대기', '일부결제', '결제예정'].includes(brand.paymentStatus);
      })
      .sort((a, b) => new Date(a.paymentDueDate).getTime() - new Date(b.paymentDueDate).getTime()),
    [brandPaymentData, today]
  );

  const recentShipments = useMemo(() => 
    brandPaymentData
      .filter(brand => {
        const shipDate = new Date(brand.shipmentDate);
        const diffTime = Math.abs(shipDate.getTime() - today.getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays <= 30;
      })
      .sort((a, b) => new Date(a.shipmentDate).getTime() - new Date(b.shipmentDate).getTime()),
    [brandPaymentData, today]
  );

  // 통화별 브랜드 수 및 금액 계산을 최적화
  const currencyChartData = useMemo(() => {
    const data = brandPaymentData.reduce((acc, brand) => {
      if (!acc[brand.currency]) {
        acc[brand.currency] = { name: brand.currency, value: 0, amount: 0 };
      }
      acc[brand.currency].value += 1;
      acc[brand.currency].amount += brand.amountKRW;
      return acc;
    }, {} as Record<string, { name: string; value: number; amount: number }>);
    
    return Object.values(data);
  }, [brandPaymentData]);

  // 결제 상태별 금액 비율
  const paymentStatusData = brandPaymentData.reduce((acc, brand) => {
    if (!acc[brand.paymentStatus]) {
      acc[brand.paymentStatus] = { name: brand.paymentStatus, value: 0 };
    }
    acc[brand.paymentStatus].value += brand.amountKRW;
    return acc;
  }, {});

  const paymentStatusChartData = Object.values(paymentStatusData);

  // 입고 상태별 브랜드 수
  const shipmentStatusData = brandPaymentData.reduce((acc, brand) => {
    if (!acc[brand.shipmentStatus]) {
      acc[brand.shipmentStatus] = { name: brand.shipmentStatus, value: 0 };
    }
    acc[brand.shipmentStatus].value += 1;
    return acc;
  }, {});

  const shipmentStatusChartData = Object.values(shipmentStatusData);

  // 브랜드별 금액 (KRW 기준)
  const brandAmountData = brandPaymentData.map(brand => ({
    name: brand.brand,
    amount: brand.amountKRW / 1000000, // 백만 원 단위로 변환
  })).sort((a, b) => b.amount - a.amount); // 금액 기준 내림차순 정렬

  // 챗봇 메시지 전송 함수
  const sendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userInput.trim()) return;
    
    setMessages(prev => [...prev, { role: 'user', content: userInput }]);
    
    // 에이전트 응답 시뮬레이션
    setTimeout(() => {
      let response = '';
      
      if (userInput.toLowerCase().includes('toga') || userInput.toLowerCase().includes('토가')) {
        response = 'TOGA VIRILIS의 결제 기한은 2025년 3월 31일이며, 결제 조건은 40% BEF. PROD - 60% AT 30 DAYS입니다. 총 금액은 EUR 5,600.00(약 8,169,000원)입니다.';
      } else if (userInput.toLowerCase().includes('wild') || userInput.toLowerCase().includes('와일드')) {
        response = 'WILD DONKEY 브랜드의 입고는 2025년 4월 15일에 예정되어 있습니다. 30% 선금은 이미 결제되었으며, 잔금 70%는 입고 시 결제 예정입니다.';
      } else if (userInput.toLowerCase().includes('입고') || userInput.toLowerCase().includes('shipment')) {
        response = '다음 달 입고 예정인 브랜드는 WILD DONKEY(4월 15일), BASERANGE(4월 10일, 지연 가능성 있음), GARBSTORE(5월 1일)가 있습니다.';
      } else if (userInput.toLowerCase().includes('결제') || userInput.toLowerCase().includes('payment')) {
        response = '2주 내 결제가 필요한 브랜드는 TOGA VIRILIS(3월 31일, EUR 5,600), ATHLETICS FTWR(3월 15일, USD 8,200)입니다.';
      } else {
        response = '죄송합니다. 구체적인 브랜드나 일정에 대해 문의해 주시면 더 정확한 정보를 제공해 드릴 수 있습니다.';
      }
      
      setMessages(prev => [...prev, { role: 'assistant', content: response }]);
    }, 1000);
    
    setUserInput('');
  };

  // 날짜 형식 변환 함수에 타입 추가
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
  };

  // 금액 형식 변환 함수에 타입 추가
  const formatCurrency = (amount: number, currency: string): string => {
    if (currency === 'KRW') {
      return `${amount.toLocaleString()}원`;
    } else {
      return `${currency} ${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
  };

  // 배경색 설정 함수
  const getStatusColor = (status: string): string => {
    switch (status) {
      case '입고완료': return 'bg-green-100 text-green-800';
      case '입고중': return 'bg-blue-100 text-blue-800';
      case '출고대기': return 'bg-yellow-100 text-yellow-800';
      case '입고예정': return 'bg-indigo-100 text-indigo-800';
      case '입고지연': return 'bg-red-100 text-red-800';
      case '결제완료': return 'bg-green-100 text-green-800';
      case '결제대기': return 'bg-yellow-100 text-yellow-800';
      case '일부결제': return 'bg-blue-100 text-blue-800';
      case '결제예정': return 'bg-indigo-100 text-indigo-800';
      case '미결제': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // 파이 차트 컬러 설정
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="bg-indigo-600 text-white p-4">
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold">★23SS BUYING MASTER AI</h1>
          <div className="flex items-center space-x-4">
            <button className="bg-white text-indigo-600 px-3 py-1 rounded">
              <Calendar className="h-4 w-4 inline mr-1" />
              일정
            </button>
            <button className="bg-white text-indigo-600 px-3 py-1 rounded">
              <CreditCard className="h-4 w-4 inline mr-1" />
              결제
            </button>
          </div>
        </div>
      </header>

      {/* 메인 콘텐츠 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 사이드바 */}
        <div className="w-48 bg-gray-800 text-white p-4">
          <nav>
            <ul className="space-y-2">
              <li className="p-2 bg-indigo-500 rounded">SHIPMENT DB</li>
              <li className="p-2 hover:bg-gray-700 rounded">BRAND LIST</li>
              <li className="p-2 hover:bg-gray-700 rounded">2023 매입</li>
              <li className="p-2 hover:bg-gray-700 rounded">ORDER</li>
              <li className="p-2 hover:bg-gray-700 rounded">코드체계</li>
              <li className="p-2 hover:bg-gray-700 rounded">문서 OCR 처리</li>
            </ul>
          </nav>
        </div>

        {/* 대시보드 내용 */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 결제 예정 브랜드 */}
            <div className="bg-white p-4 rounded shadow col-span-2">
              <h2 className="text-lg font-semibold mb-4">결제 예정 브랜드</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">브랜드</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">결제 기한</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">결제 조건</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">금액</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {upcomingPayments.map((brand, index) => {
                      const dueDate = new Date(brand.paymentDueDate);
                      const diffTime = dueDate - today;
                      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
                      const isUrgent = diffDays <= 3;
                      
                      return (
                        <tr key={index} className={isUrgent ? "bg-red-50" : "hover:bg-gray-50"}>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div className="font-medium text-gray-900">{brand.brand}</div>
                            <div className="text-xs text-gray-500">{brand.season}</div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div className={isUrgent ? "font-bold text-red-600" : ""}>
                              {formatDate(brand.paymentDueDate)}
                              {isUrgent && ` (${diffDays}일 남음)`}
                            </div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm">{brand.paymentTerms}</td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div>{formatCurrency(brand.totalAmount, brand.currency)}</div>
                            <div className="text-xs text-gray-500">약 {Math.round(brand.amountKRW / 10000).toLocaleString()}만원</div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(brand.paymentStatus)}`}>
                              {brand.paymentStatus}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 통화별 금액 */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-lg font-semibold mb-4">통화별 매입 금액 (백만원)</h2>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie
                    data={currencyChartData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="amount"
                    nameKey="name"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {currencyChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${(value/1000000).toFixed(1)}백만원`, '금액']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="mt-2 text-xs text-gray-500 text-center">총 매입액: {Math.round(brandPaymentData.reduce((sum, brand) => sum + brand.amountKRW, 0) / 10000).toLocaleString()}만원</div>
            </div>

            {/* 최근 및 예정 입고 */}
            <div className="bg-white p-4 rounded shadow col-span-2">
              <h2 className="text-lg font-semibold mb-4">입고 현황</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">브랜드</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">입고일</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">주문일</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">금액</th>
                      <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">상태</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {recentShipments.map((brand, index) => {
                      const shipDate = new Date(brand.shipmentDate);
                      const isUpcoming = shipDate > today;
                      
                      return (
                        <tr key={index} className={brand.shipmentStatus === '입고지연' ? "bg-red-50" : "hover:bg-gray-50"}>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div className="font-medium text-gray-900">{brand.brand}</div>
                            <div className="text-xs text-gray-500">{brand.season}</div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div className={isUpcoming ? "font-medium text-indigo-600" : ""}>
                              {formatDate(brand.shipmentDate)}
                              {isUpcoming && ` (D-${Math.ceil((shipDate - today) / (1000 * 60 * 60 * 24))})`}
                            </div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap text-sm">{formatDate(brand.documentDate)}</td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <div>{formatCurrency(brand.totalAmount, brand.currency)}</div>
                            <div className="text-xs text-gray-500">약 {Math.round(brand.amountKRW / 10000).toLocaleString()}만원</div>
                          </td>
                          <td className="px-4 py-2 whitespace-nowrap">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(brand.shipmentStatus)}`}>
                              {brand.shipmentStatus}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 브랜드별 금액 */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-lg font-semibold mb-4">브랜드별 매입 금액 (백만원)</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={brandAmountData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis />
                  <Tooltip formatter={(value) => [`${value.toFixed(1)}백만원`, '금액']} />
                  <Bar dataKey="amount" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* 알림 */}
            <div className="bg-white p-4 rounded shadow col-span-2">
              <h2 className="text-lg font-semibold mb-4">최근 알림</h2>
              <ul className="space-y-2">
                <li className="flex items-center p-2 border-l-4 border-red-500 bg-red-50">
                  <Flag className="text-red-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">BASERANGE 입고 지연</p>
                    <p className="text-sm text-gray-600">예상 입고일: {formatDate(brandPaymentData.find(b => b.brand === 'BASERANGE').shipmentDate)} (지연 가능성 있음)</p>
                  </div>
                </li>
                <li className="flex items-center p-2 border-l-4 border-yellow-500 bg-yellow-50">
                  <CreditCard className="text-yellow-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">ATHLETICS FTWR 결제 기한</p>
                    <p className="text-sm text-gray-600">결제 마감일: {formatDate(brandPaymentData.find(b => b.brand === 'ATHLETICS FTWR').paymentDueDate)} (5일 남음)</p>
                  </div>
                </li>
                <li className="flex items-center p-2 border-l-4 border-green-500 bg-green-50">
                  <Package className="text-green-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">NOU NOU 입고 진행중</p>
                    <p className="text-sm text-gray-600">예상 도착일: {formatDate(brandPaymentData.find(b => b.brand === 'NOU NOU').shipmentDate)}</p>
                  </div>
                </li>
                <li className="flex items-center p-2 border-l-4 border-blue-500 bg-blue-50">
                  <Clock className="text-blue-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">WILD DONKEY 출고 예정</p>
                    <p className="text-sm text-gray-600">예상 출고일: {formatDate(new Date(brandPaymentData.find(b => b.brand === 'WILD DONKEY').shipmentDate).setDate(new Date(brandPaymentData.find(b => b.brand === 'WILD DONKEY').shipmentDate).getDate() - 10))}</p>
                  </div>
                </li>
              </ul>
            </div>

            {/* 환율 정보 */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-lg font-semibold mb-4">환율 정보 (KRW)</h2>
              <ul className="space-y-3">
                <li className="flex justify-between items-center border-b pb-2">
                  <span className="flex items-center">
                    <DollarSign className="h-4 w-4 mr-1 text-blue-500" />
                    <span>USD</span>
                  </span>
                  <span className="font-mono">{brandPaymentData.find(b => b.currency === 'USD').exchangeRate.toFixed(2)} ↑</span>
                </li>
                <li className="flex justify-between items-center border-b pb-2">
                  <span className="flex items-center">
                    <span className="h-4 w-4 mr-1 text-blue-500 font-bold">€</span>
                    <span>EUR</span>
                  </span>
                  <span className="font-mono">{brandPaymentData.find(b => b.currency === 'EUR').exchangeRate.toFixed(2)} ↓</span>
                </li>
                <li className="flex justify-between items-center">
                  <span className="flex items-center">
                    <span className="h-4 w-4 mr-1 text-blue-500 font-bold">£</span>
                    <span>GBP</span>
                  </span>
                  <span className="font-mono">{brandPaymentData.find(b => b.currency === 'GBP').exchangeRate.toFixed(2)} ↑</span>
                </li>
              </ul>
              <div className="mt-4 text-xs text-right text-gray-500">마지막 업데이트: {formatDate(today)}</div>
            </div>
          </div>
        </main>

        {/* AI 어시스턴트 팝업 */}
        <div className={`fixed bottom-4 right-4 w-96 bg-white rounded-lg shadow-xl overflow-hidden transition-all duration-300 ${chatOpen ? 'h-96' : 'h-12'}`}>
          <div className="bg-indigo-600 text-white p-3 cursor-pointer flex justify-between items-center" onClick={() => setChatOpen(!chatOpen)}>
            <div className="flex items-center">
              <MessageSquare className="h-5 w-5 mr-2" />
              <span>AI 구매 어시스턴트</span>
            </div>
            <ChevronDown className={`h-5 w-5 transition-transform ${chatOpen ? 'transform rotate-180' : ''}`} />
          </div>

