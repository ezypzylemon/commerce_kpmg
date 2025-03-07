import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Calendar, ChevronDown, Flag, Package, CreditCard, MessageSquare } from 'lucide-react';

const BuyingManagerDashboard = () => {
  const [chatOpen, setChatOpen] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState([
    { role: 'assistant', content: '안녕하세요! 구매 관리 어시스턴트입니다. 무엇을 도와드릴까요?' }
  ]);

  const sendMessage = (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;
    
    // 사용자 메시지 추가
    setMessages([...messages, { role: 'user', content: userInput }]);
    
    // 에이전트 응답 시뮬레이션 (실제로는 API 호출)
    setTimeout(() => {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '23SS WILD DONKEY 브랜드의 입고는 4월 15일에 예정되어 있습니다. EUR로 결제 예정이며, 현재 환율로 계산 시 약 3,250,000원입니다.' 
      }]);
    }, 1000);
    
    setUserInput('');
  };

  // 샘플 데이터
  const brandData = [
    { name: 'ATHLETICS FTWR', currency: 'USD', status: '입고완료', payment: '결제대기' },
    { name: 'NOU NOU', currency: 'KRW', status: '입고중', payment: '결제완료' },
    { name: 'WILD DONKEY', currency: 'EUR', status: '출고대기', payment: '미결제' },
    { name: 'GARBSTORE', currency: 'GBP', status: '입고예정', payment: '미결제' },
    { name: 'BASERANGE', currency: 'EUR', status: '입고지연', payment: '미결제' },
  ];

  const currencyData = [
    { name: 'USD', value: 4 },
    { name: 'EUR', value: 7 },
    { name: 'GBP', value: 2 },
    { name: 'KRW', value: 3 },
  ];

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
            </ul>
          </nav>
        </div>

        {/* 대시보드 내용 */}
        <main className="flex-1 p-6 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* 브랜드 현황 */}
            <div className="bg-white p-4 rounded shadow col-span-2">
              <h2 className="text-lg font-semibold mb-4">브랜드 입고 현황</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">브랜드</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">통화</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">입고 상태</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">결제 상태</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {brandData.map((brand, index) => (
                      <tr key={index} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">{brand.name}</td>
                        <td className="px-6 py-4 whitespace-nowrap">{brand.currency}</td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${brand.status === '입고완료' ? 'bg-green-100 text-green-800' : 
                              brand.status === '입고중' ? 'bg-blue-100 text-blue-800' : 
                              brand.status === '입고지연' ? 'bg-red-100 text-red-800' : 
                              'bg-yellow-100 text-yellow-800'}`}>
                            {brand.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${brand.payment === '결제완료' ? 'bg-green-100 text-green-800' : 
                              brand.payment === '결제대기' ? 'bg-yellow-100 text-yellow-800' : 
                              'bg-gray-100 text-gray-800'}`}>
                            {brand.payment}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* 통화별 현황 */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-lg font-semibold mb-4">통화별 브랜드 수</h2>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={currencyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="value" fill="#8884d8" />
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
                    <p className="text-sm text-gray-600">예상 도착일: 3일 후</p>
                  </div>
                </li>
                <li className="flex items-center p-2 border-l-4 border-yellow-500 bg-yellow-50">
                  <CreditCard className="text-yellow-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">ATHLETICS FTWR 결제 기한</p>
                    <p className="text-sm text-gray-600">결제 마감일: 2일 후</p>
                  </div>
                </li>
                <li className="flex items-center p-2 border-l-4 border-green-500 bg-green-50">
                  <Package className="text-green-500 mr-2 h-5 w-5" />
                  <div>
                    <p className="font-medium">NOU NOU 입고 완료</p>
                    <p className="text-sm text-gray-600">오늘 오전 11:30</p>
                  </div>
                </li>
              </ul>
            </div>

            {/* 환율 정보 */}
            <div className="bg-white p-4 rounded shadow">
              <h2 className="text-lg font-semibold mb-4">환율 정보 (KRW)</h2>
              <ul className="space-y-3">
                <li className="flex justify-between">
                  <span>USD</span>
                  <span className="font-mono">1,342.50 ↑</span>
                </li>
                <li className="flex justify-between">
                  <span>EUR</span>
                  <span className="font-mono">1,458.75 ↓</span>
                </li>
                <li className="flex justify-between">
                  <span>GBP</span>
                  <span className="font-mono">1,702.30 ↑</span>
                </li>
              </ul>
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
          
          {chatOpen && (
            <>
              <div className="p-3 h-64 overflow-y-auto">
                {messages.map((msg, index) => (
                  <div key={index} className={`mb-3 ${msg.role === 'user' ? 'text-right' : ''}`}>
                    <div className={`inline-block rounded-lg px-3 py-2 ${msg.role === 'user' ? 'bg-indigo-100' : 'bg-gray-100'}`}>
                      {msg.content}
                    </div>
                  </div>
                ))}
              </div>
              <form onSubmit={sendMessage} className="border-t p-3">
                <div className="flex">
                  <input
                    type="text"
                    className="flex-1 border rounded-l px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="질문을 입력하세요..."
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                  />
                  <button type="submit" className="bg-indigo-600 text-white px-4 py-2 rounded-r">전송</button>
                </div>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default BuyingManagerDashboard;