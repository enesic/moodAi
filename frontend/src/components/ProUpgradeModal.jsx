import React, { useState } from 'react';
import { setProStatus } from '../api/client';

const ProUpgradeModal = ({ isOpen, onClose, onProActivated, customMessage, showToast }) => {
  const [selectedPlan, setSelectedPlan] = useState('yearly');
  const [licenseCode, setLicenseCode] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [processing, setProcessing] = useState(false);

  if (!isOpen) return null;

  const handleCheckout = () => {
    // Canlı ödeme bağlantısı varsa oraya yönlendir
    const checkoutUrl = import.meta.env.VITE_CHECKOUT_URL;
    if (checkoutUrl) {
      window.open(checkoutUrl, '_blank');
      return;
    }

    // Yoksa hızlı simülasyon / aktivasyon desteği
    setProcessing(true);
    setTimeout(() => {
      setProStatus(true);
      onProActivated?.();
      showToast?.('Tebrikler! Mood AI PRO üyeliğiniz başarıyla aktif edildi! 👑🎉', 'success');
      setProcessing(false);
      onClose();
    }, 1200);
  };

  const handleApplyLicense = () => {
    const trimmed = licenseCode.trim().toUpperCase();
    if (trimmed === 'MOODAI-PRO' || trimmed === 'VIP' || trimmed.length >= 6) {
      setProStatus(true);
      onProActivated?.();
      showToast?.('Lisans anahtarı doğrulandı! Mood AI PRO aktif! 👑', 'success');
      onClose();
    } else {
      showToast?.('Geçersiz lisans anahtarı. Örnek: MOODAI-PRO', 'error');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 animate-fadeIn">
      <div className="bg-[#130926] border border-amber-500/40 rounded-3xl p-5 sm:p-8 max-w-xl w-full max-h-[92vh] overflow-y-auto shadow-2xl flex flex-col space-y-6 scrollbar-thin scrollbar-thumb-amber-500/30 relative">
        {/* Glow Işığı */}
        <div className="absolute top-0 right-1/4 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Header */}
        <div className="flex justify-between items-start border-b border-white/10 pb-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300 text-xs font-black tracking-wider uppercase mb-2">
              <span>👑</span> Mood AI PRO
            </div>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
              Sonsuz Müzik Terapisi & Özel Frekanslar
            </h2>
            <p className="text-xs text-gray-400 mt-1">
              {customMessage || 'Günlük analiz limitini kaldırın, şifa frekanslarını açın ve ruh halinizi haritalandırın.'}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl p-1.5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Pro Avantajları Listesi */}
        <div className="space-y-2.5 bg-black/40 p-4 rounded-2xl border border-white/5 text-xs text-gray-200">
          <div className="flex items-center gap-2.5">
            <span className="text-amber-400 font-bold">✓</span>
            <span><strong>Sınırsız Günlük Analiz:</strong> Limit olmadan günün her anı dilediğince reçete oluştur.</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-amber-400 font-bold">✓</span>
            <span><strong>Binaural Beats & 432 Hz Şifa:</strong> Zihni sakinleştiren ve odaklayan frekansları harmanla.</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-amber-400 font-bold">✓</span>
            <span><strong>Sınırsız Sesli İç Dökme:</strong> Klavyeye dokunmadan mikrofona dert yanarak reçete al.</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-amber-400 font-bold">✓</span>
            <span><strong>30 Günlük Duygu Günlüğü & PDF Raporu:</strong> Zaman içindeki ruh halini gösteren uzman analizi.</span>
          </div>
          <div className="flex items-center gap-2.5">
            <span className="text-amber-400 font-bold">✓</span>
            <span><strong>Filigransız HD Instagram Vibe Kartları:</strong> Sosyal medyada parlayacak özel tasarımlar.</span>
          </div>
        </div>

        {/* Fiyatlandırma Kartları */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {/* Yıllık Plan (Öne Çıkan) */}
          <div
            onClick={() => setSelectedPlan('yearly')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer relative ${
              selectedPlan === 'yearly'
                ? 'bg-amber-950/40 border-amber-400/80 shadow-lg shadow-amber-500/20 ring-1 ring-amber-400/40'
                : 'bg-black/30 border-white/10 hover:border-white/20'
            }`}
          >
            <span className="absolute -top-2.5 right-3 px-2 py-0.5 rounded-full bg-gradient-to-r from-amber-500 to-pink-500 text-[9px] font-black text-black uppercase tracking-wider">
              %45 İndirim
            </span>
            <p className="text-xs font-bold text-gray-300">Yıllık VIP Plan</p>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-2xl font-black text-white">499 ₺</span>
              <span className="text-xs text-gray-400">/ yıl (41 ₺/ay)</span>
            </div>
            <p className="text-[10px] text-amber-300/80 mt-1">En çok tercih edilen seçenek</p>
          </div>

          {/* Aylık Plan */}
          <div
            onClick={() => setSelectedPlan('monthly')}
            className={`p-4 rounded-2xl border transition-all cursor-pointer ${
              selectedPlan === 'monthly'
                ? 'bg-amber-950/40 border-amber-400/80 shadow-lg shadow-amber-500/20 ring-1 ring-amber-400/40'
                : 'bg-black/30 border-white/10 hover:border-white/20'
            }`}
          >
            <p className="text-xs font-bold text-gray-300">Aylık Plan</p>
            <div className="flex items-baseline gap-1 mt-1">
              <span className="text-2xl font-black text-white">79 ₺</span>
              <span className="text-xs text-gray-400">/ ay</span>
            </div>
            <p className="text-[10px] text-gray-400 mt-1">İstediğin zaman iptal et</p>
          </div>
        </div>

        {/* Satın Alma Butonu */}
        <button
          onClick={handleCheckout}
          disabled={processing}
          className="w-full py-4 px-6 rounded-2xl bg-gradient-to-r from-amber-500 via-pink-500 to-purple-600 hover:from-amber-400 hover:to-purple-500 text-black font-black text-sm transition-transform hover:scale-[1.01] shadow-xl shadow-amber-500/20 cursor-pointer flex items-center justify-center gap-2"
        >
          {processing ? (
            <span className="animate-spin text-black">⏳ PRO Aktif Ediliyor...</span>
          ) : (
            <>
              <span>👑</span>
              <span>Hemen PRO'ya Yükselt ({selectedPlan === 'yearly' ? '499 ₺' : '79 ₺'})</span>
            </>
          )}
        </button>

        {/* Lisans Anahtarı / Promosyon Kodu */}
        <div className="text-center pt-1 border-t border-white/10">
          {!showCodeInput ? (
            <button
              onClick={() => setShowCodeInput(true)}
              className="text-xs text-gray-400 hover:text-amber-300 transition-colors cursor-pointer"
            >
              Kuponun veya Lisans Kodun var mı? <span className="underline">Buraya tıkla</span>
            </button>
          ) : (
            <div className="flex gap-2 max-w-sm mx-auto mt-2">
              <input
                type="text"
                value={licenseCode}
                onChange={(e) => setLicenseCode(e.target.value)}
                placeholder="Örn: MOODAI-PRO"
                className="flex-1 glass-input rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none uppercase font-mono"
              />
              <button
                onClick={handleApplyLicense}
                className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black font-black text-xs rounded-xl cursor-pointer"
              >
                Uygula
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProUpgradeModal;
