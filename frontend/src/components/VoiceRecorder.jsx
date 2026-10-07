import React, { useState, useEffect, useRef } from 'react';

const VoiceRecorder = ({ onTranscriptionComplete, showToast, isPro, onOpenProModal }) => {
  const [isListening, setIsListening] = useState(false);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [supported, setSupported] = useState(true);
  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSupported(false);
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'tr-TR';

    recognition.onstart = () => {
      setIsListening(true);
      setLiveTranscript('');
    };

    recognition.onresult = (event) => {
      let current = '';
      for (let i = 0; i < event.results.length; i++) {
        current += event.results[i][0].transcript + ' ';
      }
      setLiveTranscript(current.trim());
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      if (event.error === 'not-allowed') {
        showToast?.('Mikrofon erişim izni verilmedi.', 'error');
      }
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (_) {}
    };
  }, [showToast]);

  const toggleListening = () => {
    if (!supported) {
      showToast?.('Tarayıcınız ses tanıma özelliğini desteklemiyor. Lütfen Chrome, Edge veya Safari kullanın.', 'warning');
      return;
    }

    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch (_) {}
      setIsListening(false);
      if (liveTranscript.trim()) {
        onTranscriptionComplete(liveTranscript.trim());
        showToast?.('🎙️ Sesli iç döküşünüz metne aktarıldı!', 'success');
      }
    } else {
      try {
        setLiveTranscript('');
        recognitionRef.current?.start();
        showToast?.('Sizi dinliyorum, lütfen iç döküşünüzü anlatın...', 'info');
      } catch (err) {
        console.error(err);
      }
    }
  };

  const handleApply = () => {
    if (isListening) {
      try {
        recognitionRef.current?.stop();
      } catch (_) {}
      setIsListening(false);
    }
    if (liveTranscript.trim()) {
      onTranscriptionComplete(liveTranscript.trim());
      showToast?.('🎙️ Sesli iç döküşünüz uygulandı!', 'success');
    }
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={toggleListening}
          className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer shadow-md ${
            isListening
              ? 'bg-rose-600 hover:bg-rose-500 text-white animate-pulse ring-2 ring-rose-400'
              : 'bg-gradient-to-r from-purple-600/30 to-pink-600/30 hover:from-purple-600/50 hover:to-pink-600/50 border border-purple-400/40 text-purple-200 hover:text-white'
          }`}
          title="Sesli İç Dökme (Mikrofon)"
        >
          <span className="text-sm">{isListening ? '🛑' : '🎙️'}</span>
          <span>{isListening ? 'Dinlemeyi Durdur' : 'Sesli Anlat'}</span>
        </button>

        {isListening && (
          <div className="flex items-center gap-1.5 px-3 py-1 bg-rose-950/60 border border-rose-500/40 rounded-xl text-[11px] text-rose-300">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping" />
            <span>Kayıt alınıyor...</span>
          </div>
        )}
      </div>

      {/* Canlı Dinleme Popover Paneli */}
      {isListening && (
        <div className="mt-3 p-3.5 rounded-2xl bg-[#140a28]/95 border border-purple-500/40 shadow-2xl animate-fadeIn space-y-2">
          <div className="flex items-center justify-between text-[11px] text-gray-400">
            <span className="text-purple-300 font-semibold flex items-center gap-1">
              <span>🔊</span> Canlı Dinleme
            </span>
            <span>Konuşmanız bitince durdurun</span>
          </div>

          <div className="min-h-12 max-h-24 overflow-y-auto p-2 bg-black/40 rounded-xl text-xs text-white leading-relaxed italic">
            {liveTranscript || 'Sesiniz bekleniyor... Konuşmaya başlayabilirsiniz.'}
          </div>

          <div className="flex justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleApply}
              disabled={!liveTranscript.trim()}
              className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition-all disabled:opacity-40 cursor-pointer"
            >
              Metne Aktar ✓
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default VoiceRecorder;
