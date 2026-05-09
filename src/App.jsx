import React, { useState, useRef, useEffect } from 'react';
import { PenTool, Users, Settings, Trash2, Clock, User, AlignLeft, RefreshCw, Printer, Loader2, Link, ShieldCheck, ExternalLink } from 'lucide-react';
import { initializeApp } from 'firebase/app';
import { getAuth, signInWithCustomToken, signInAnonymously, onAuthStateChanged } from 'firebase/auth';
import { getFirestore, doc, setDoc, onSnapshot, updateDoc } from 'firebase/firestore';

const firebaseConfig = JSON.parse(__firebase_config);
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);
const appId = typeof __app_id !== 'undefined' ? __app_id : 'meeting-signature-final';

const isValidSignature = (sig) => typeof sig === 'string' && sig.startsWith('data:image');

const SignaturePad = ({ onSignatureChange, onClearRef }) => {
  const canvasRef = useRef(null);
  const [isEmpty, setIsEmpty] = useState(true);
  const drawState = useRef({ isDrawing: false, lastX: 0, lastY: 0, lastTime: 0, lastWidth: 3 });

  const initCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    const ratio = Math.max(window.devicePixelRatio || 1, 1);
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    context.lineCap = 'round';
    context.lineJoin = 'round';
  };

  useEffect(() => {
    initCanvas();
    window.addEventListener('resize', initCanvas);
    return () => window.removeEventListener('resize', initCanvas);
  }, []);

  useEffect(() => {
    if (onClearRef) onClearRef.current = clearCanvas;
  }, [onClearRef]);

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const context = canvas.getContext('2d');
    context.save();
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, canvas.width, canvas.height);
    context.restore();
    setIsEmpty(true);
    onSignatureChange(null);
  };

  const getCoordinates = (e) => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    let clientX, clientY;
    if (e.touches && e.touches.length > 0) {
      clientX = e.touches[0].clientX;
      clientY = e.touches[0].clientY;
    } else {
      clientX = e.clientX;
      clientY = e.clientY;
    }
    return { x: clientX - rect.left, y: clientY - rect.top };
  };

  const startDrawing = (e) => {
    e.preventDefault();
    if (isEmpty) setIsEmpty(false);
    const { x, y } = getCoordinates(e);
    drawState.current = { isDrawing: true, lastX: x, lastY: y, lastTime: Date.now(), lastWidth: 2.5 };
  };

  const draw = (e) => {
    if (!drawState.current.isDrawing) return;
    e.preventDefault();
    const { x, y } = getCoordinates(e);
    const state = drawState.current;
    const currentTime = Date.now();
    const context = canvasRef.current.getContext('2d');
    const distance = Math.sqrt(Math.pow(x - state.lastX, 2) + Math.pow(y - state.lastY, 2));
    const time = currentTime - state.lastTime || 1;
    const velocity = distance / time;
    const targetWidth = Math.max(1.0, Math.min(4.5, 4.5 - velocity * 1.5));
    const lineWidth = state.lastWidth + (targetWidth - state.lastWidth) * 0.2;
    context.lineWidth = lineWidth;
    context.strokeStyle = '#1e3a8a';
    context.beginPath();
    context.moveTo(state.lastX, state.lastY);
    context.lineTo(x, y);
    context.stroke();
    drawState.current = { ...state, lastX: x, lastY: y, lastTime: currentTime, lastWidth: lineWidth };
  };

  const stopDrawing = () => {
    if (drawState.current.isDrawing) {
      drawState.current.isDrawing = false;
      onSignatureChange(canvasRef.current.toDataURL('image/png'));
    }
  };

  return (
    <div className="relative border-2 border-dashed border-gray-300 rounded-xl overflow-hidden bg-white shadow-inner">
      <canvas ref={canvasRef} className="w-full h-48 sm:h-64 cursor-crosshair touch-none bg-slate-50/20" onMouseDown={startDrawing} onMouseMove={draw} onMouseUp={stopDrawing} onMouseLeave={stopDrawing} onTouchStart={startDrawing} onTouchMove={draw} onTouchEnd={stopDrawing} />
      {isEmpty && <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-40"><span className="text-slate-500 font-medium italic text-center px-4">이곳에 성함을 정자로 서명해 주세요</span></div>}
    </div>
  );
};

export default function App() {
  return <div>Use provided component body here.</div>;
}
