import React from 'react';
import {
  Globe,
  BookOpen,
  Users,
  FileText,
  Presentation,
  Video,
  GraduationCap
} from 'lucide-react';

export const AILearningEngineVisual: React.FC = () => {
  return (
    <div className="relative w-full h-full min-h-[660px] lg:min-h-full flex items-center justify-center overflow-hidden select-none bg-transparent">
      {/* ================================================================= */}
      {/* 1. BACKGROUND GLOWS & CIRCUIT TRACES                              */}
      {/* ================================================================= */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden">
        {/* Central Core Ambient Glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[550px] bg-gradient-to-tr from-blue-600/30 via-cyan-500/25 to-indigo-600/25 blur-[120px] rounded-full" />
        <div className="absolute top-1/4 right-1/4 w-[320px] h-[320px] bg-cyan-400/20 blur-[90px] rounded-full" />
        <div className="absolute bottom-1/4 left-1/4 w-[350px] h-[350px] bg-blue-600/25 blur-[100px] rounded-full" />

        {/* Floating 3D Glass Perspective Rectangles (Static & Clean) */}
        {/* Top-Left Floating Glass Plate */}
        <div className="absolute top-16 left-8 w-24 h-16 rounded-xl bg-blue-500/10 border border-blue-400/30 shadow-[0_0_15px_rgba(59,130,246,0.2)] transform -rotate-12 skew-x-6 backdrop-blur-xs" />
        {/* Mid-Left Floating Glass Plate */}
        <div className="absolute top-1/3 left-4 w-28 h-20 rounded-xl bg-indigo-500/10 border border-cyan-400/25 shadow-[0_0_20px_rgba(6,182,212,0.15)] transform -rotate-6 skew-y-3 backdrop-blur-xs" />
        {/* Lower-Left Floating Glass Plate */}
        <div className="absolute bottom-20 left-12 w-32 h-20 rounded-xl bg-blue-600/10 border border-blue-400/25 shadow-[0_0_15px_rgba(59,130,246,0.2)] transform rotate-6 -skew-x-6 backdrop-blur-xs" />

        {/* Right Floating Glass Plate */}
        <div className="absolute top-1/4 right-8 w-24 h-18 rounded-xl bg-cyan-500/10 border border-cyan-400/30 shadow-[0_0_18px_rgba(56,189,248,0.2)] transform rotate-12 skew-y-6 backdrop-blur-xs" />
        {/* Lower-Right Floating Glass Plate */}
        <div className="absolute bottom-24 right-10 w-28 h-36 rounded-xl bg-blue-500/10 border border-indigo-400/25 shadow-[0_0_20px_rgba(99,102,241,0.2)] transform -rotate-6 skew-x-3 backdrop-blur-xs" />
        {/* Bottom Center Floating Plate */}
        <div className="absolute bottom-10 left-1/3 w-36 h-20 rounded-xl bg-indigo-500/10 border border-cyan-400/20 shadow-[0_0_15px_rgba(6,182,212,0.15)] transform rotate-3 -skew-y-3 backdrop-blur-xs" />

        {/* Vertical and Angled Cyber Circuit Traces with Terminal Nodes */}
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          {/* Left Circuit Lines */}
          <path d="M 60 120 L 140 120 L 170 150" fill="none" stroke="#00D4FF" strokeWidth="1.2" strokeOpacity="0.4" />
          <circle cx="60" cy="120" r="2.5" fill="#00F0FF" />
          <path d="M 40 280 L 110 280 L 140 250" fill="none" stroke="#38BDF8" strokeWidth="1.2" strokeOpacity="0.35" />
          <circle cx="40" cy="280" r="2.5" fill="#38BDF8" />
          <path d="M 70 420 L 130 420 L 160 390" fill="none" stroke="#818CF8" strokeWidth="1.2" strokeOpacity="0.4" />
          <circle cx="70" cy="420" r="2.5" fill="#818CF8" />

          {/* Right Circuit Lines */}
          <path d="M 420 160 L 460 160 L 490 190" fill="none" stroke="#00D4FF" strokeWidth="1.2" strokeOpacity="0.4" />
          <circle cx="490" cy="190" r="2.5" fill="#00F0FF" />
          <path d="M 430 320 L 480 320 L 510 350" fill="none" stroke="#38BDF8" strokeWidth="1.2" strokeOpacity="0.35" />
          <circle cx="510" cy="350" r="2.5" fill="#38BDF8" />
          <path d="M 390 440 L 440 440 L 470 470" fill="none" stroke="#818CF8" strokeWidth="1.2" strokeOpacity="0.4" />
          <circle cx="470" cy="470" r="2.5" fill="#818CF8" />

          {/* Vertical Data Bus Lines */}
          <line x1="480" y1="80" x2="480" y2="240" stroke="#00D4FF" strokeWidth="1" strokeDasharray="3 6" strokeOpacity="0.3" />
          <circle cx="480" cy="80" r="2" fill="#00F0FF" />
          <line x1="100" y1="360" x2="100" y2="520" stroke="#818CF8" strokeWidth="1" strokeDasharray="3 6" strokeOpacity="0.3" />
          <circle cx="100" cy="520" r="2" fill="#818CF8" />
        </svg>
      </div>

      {/* ================================================================= */}
      {/* 2. CIRCULAR HUD MATRIX WITH CENTRAL CHIP & 6 SATELLITE NODES      */}
      {/* ================================================================= */}
      <div className="relative w-[500px] h-[500px] sm:w-[560px] sm:h-[560px] flex items-center justify-center">
        {/* SVG Live Circuit Connections & Radial HUD Rings */}
        <svg
          className="absolute inset-0 w-full h-full pointer-events-none"
          viewBox="0 0 560 560"
          xmlns="http://www.w3.org/2000/svg"
        >
          <defs>
            <linearGradient id="neonCyanGlow" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.95" />
              <stop offset="50%" stopColor="#3B82F6" stopOpacity="0.9" />
              <stop offset="100%" stopColor="#818CF8" stopOpacity="0.95" />
            </linearGradient>

            <radialGradient id="chipAura" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#00F0FF" stopOpacity="0.45" />
              <stop offset="40%" stopColor="#2563EB" stopOpacity="0.3" />
              <stop offset="80%" stopColor="#4F46E5" stopOpacity="0.1" />
              <stop offset="100%" stopColor="transparent" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Central Radial Light Aura */}
          <circle cx="280" cy="280" r="160" fill="url(#chipAura)" />

          {/* Concentric HUD Rings */}
          {/* Ring 1: Inner Solid Cyan Ring */}
          <circle
            cx="280"
            cy="280"
            r="86"
            fill="none"
            stroke="#00F0FF"
            strokeWidth="1.5"
            strokeOpacity="0.5"
          />

          {/* Ring 2: Dotted HUD Track (Static, Clean) */}
          <circle
            cx="280"
            cy="280"
            r="120"
            fill="none"
            stroke="#38BDF8"
            strokeWidth="1.8"
            strokeDasharray="3 5"
            strokeOpacity="0.5"
          />

          {/* Ring 3: Segmented Outer HUD Ring with Tick Marks (Static, Clean) */}
          <circle
            cx="280"
            cy="280"
            r="165"
            fill="none"
            stroke="#818CF8"
            strokeWidth="1.5"
            strokeDasharray="18 36 6 36"
            strokeOpacity="0.4"
          />

          {/* Ring 4: Large Outer Orbital Path Ring */}
          <circle
            cx="280"
            cy="280"
            r="200"
            fill="none"
            stroke="#00D4FF"
            strokeWidth="1.2"
            strokeDasharray="2 12"
            strokeOpacity="0.35"
          />

          {/* ============================================================= */}
          {/* CONNECTING CIRCUIT TRACES FROM CHIP TO THE 6 NODES            */}
          {/* Center: (280, 280), Radius: ~200px                            */}
          {/* 1. Top (Globe): (280, 80)                                     */}
          {/* 2. Top-Right (Book): (425, 160)                               */}
          {/* 3. Mid-Right (People): (480, 280)                             */}
          {/* 4. Bottom-Right (Video): (425, 400)                           */}
          {/* 5. Bottom-Left (Document): (135, 400)                         */}
          {/* 6. Mid-Left (Presentation): (80, 240)                         */}
          {/* ============================================================= */}

          {/* Trace 1 -> Top Node (Globe) */}
          <line x1="280" y1="215" x2="280" y2="110" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="280" cy="150" r="3" fill="#00F0FF" />

          {/* Trace 2 -> Top-Right Node (Book) */}
          <line x1="330" y1="235" x2="415" y2="185" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="375" cy="210" r="3" fill="#38BDF8" />

          {/* Trace 3 -> Mid-Right Node (People) */}
          <line x1="345" y1="280" x2="445" y2="280" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="395" cy="280" r="3" fill="#00F0FF" />

          {/* Trace 4 -> Bottom-Right Node (Video) */}
          <line x1="330" y1="325" x2="415" y2="375" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="375" cy="350" r="3" fill="#818CF8" />

          {/* Trace 5 -> Bottom-Left Node (Document) */}
          <line x1="230" y1="325" x2="155" y2="375" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="190" cy="350" r="3" fill="#38BDF8" />

          {/* Trace 6 -> Mid-Left Node (Presentation) */}
          <line x1="215" y1="260" x2="125" y2="240" stroke="url(#neonCyanGlow)" strokeWidth="2.5" />
          <circle cx="170" cy="250" r="3" fill="#00F0FF" />

          {/* Peripheral Circuit Branches & Glowing Dots */}
          <path d="M 445 280 L 490 280 L 515 255" fill="none" stroke="#00F0FF" strokeWidth="1.2" strokeOpacity="0.5" />
          <circle cx="515" cy="255" r="2.5" fill="#00F0FF" />
          <path d="M 125 240 L 75 240 L 55 215" fill="none" stroke="#38BDF8" strokeWidth="1.2" strokeOpacity="0.5" />
          <circle cx="55" cy="215" r="2.5" fill="#38BDF8" />
        </svg>

        {/* =============================================================== */}
        {/* 3. CENTRAL GLOWING AI EDUCATION CHIP                            */}
        {/* =============================================================== */}
        <div className="relative z-30 flex items-center justify-center">
          {/* Outer Neon Radial Bloom (Static) */}
          <div className="absolute w-36 h-36 rounded-3xl bg-gradient-to-tr from-cyan-400 via-blue-600 to-indigo-600 blur-xl opacity-60" />

          {/* Metallic Contact Pins on 4 Sides (6 pins per side = 24 pins total) */}
          {/* Top Pins */}
          <div className="absolute -top-3.5 flex space-x-1.5 pointer-events-none">
            {[...Array(6)].map((_, i) => (
              <div key={`p-top-${i}`} className="w-1.5 h-3.5 bg-gradient-to-b from-cyan-300 via-cyan-400 to-slate-900 rounded-xs shadow-[0_0_6px_#00F0FF]" />
            ))}
          </div>
          {/* Bottom Pins */}
          <div className="absolute -bottom-3.5 flex space-x-1.5 pointer-events-none">
            {[...Array(6)].map((_, i) => (
              <div key={`p-bot-${i}`} className="w-1.5 h-3.5 bg-gradient-to-t from-cyan-300 via-cyan-400 to-slate-900 rounded-xs shadow-[0_0_6px_#00F0FF]" />
            ))}
          </div>
          {/* Left Pins */}
          <div className="absolute -left-3.5 flex flex-col space-y-1.5 pointer-events-none">
            {[...Array(6)].map((_, i) => (
              <div key={`p-left-${i}`} className="w-3.5 h-1.5 bg-gradient-to-r from-cyan-300 via-cyan-400 to-slate-900 rounded-xs shadow-[0_0_6px_#00F0FF]" />
            ))}
          </div>
          {/* Right Pins */}
          <div className="absolute -right-3.5 flex flex-col space-y-1.5 pointer-events-none">
            {[...Array(6)].map((_, i) => (
              <div key={`p-right-${i}`} className="w-3.5 h-1.5 bg-gradient-to-l from-cyan-300 via-cyan-400 to-slate-900 rounded-xs shadow-[0_0_6px_#00F0FF]" />
            ))}
          </div>

          {/* Chip Body */}
          <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-3xl bg-gradient-to-br from-[#0B1E48] via-[#0D1C44] to-[#121038] border-2 border-[#00E5FF] shadow-[0_0_40px_rgba(0,229,255,0.6)] flex flex-col items-center justify-center p-3 backdrop-blur-md group hover:scale-105 transition-transform duration-300 cursor-default">
            {/* Inner Glowing Recessed Circuit Surface */}
            <div className="w-full h-full rounded-2xl bg-gradient-to-br from-[#06112C] to-[#0A173A] border border-cyan-400/40 flex flex-col items-center justify-center relative overflow-hidden">
              {/* Corner tech notch accents */}
              <div className="absolute top-1 left-1 w-1.5 h-1.5 border-t border-l border-cyan-400" />
              <div className="absolute top-1 right-1 w-1.5 h-1.5 border-t border-r border-cyan-400" />
              <div className="absolute bottom-1 left-1 w-1.5 h-1.5 border-b border-l border-cyan-400" />
              <div className="absolute bottom-1 right-1 w-1.5 h-1.5 border-b border-r border-cyan-400" />

              {/* Glowing Graduation Cap Mortarboard in Center */}
              <GraduationCap className="w-12 h-12 text-white drop-shadow-[0_0_12px_rgba(255,255,255,0.9)]" />
            </div>
          </div>
        </div>

        {/* =============================================================== */}
        {/* 4. THE SIX CONNECTED ORBITAL ICON PODS (Clean & Stationary)     */}
        {/*    (Globe, Presentation, Book, People, Document, Video)         */}
        {/* =============================================================== */}

        {/* NODE 1: GLOBE ICON (Top / 12 o'clock) */}
        <div className="absolute top-8 left-1/2 -translate-x-1/2 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-cyan-400 shadow-[0_0_25px_rgba(0,240,255,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <Globe className="w-7 h-7 text-white drop-shadow-[0_0_8px_#00F0FF] group-hover:rotate-12 transition-transform" />
          </div>
        </div>

        {/* NODE 2: BOOK ICON (Top-Right / 2 o'clock) */}
        <div className="absolute top-22 right-10 sm:right-12 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-blue-400 shadow-[0_0_25px_rgba(59,130,246,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <BookOpen className="w-7 h-7 text-white drop-shadow-[0_0_8px_#38BDF8] group-hover:scale-110 transition-transform" />
          </div>
        </div>

        {/* NODE 3: PEOPLE / USERS ICON (Mid-Right / 3:30 o'clock) */}
        <div className="absolute top-1/2 -translate-y-1/2 right-2 sm:right-4 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-cyan-400 shadow-[0_0_25px_rgba(0,240,255,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <Users className="w-7 h-7 text-white drop-shadow-[0_0_8px_#00F0FF] group-hover:scale-110 transition-transform" />
          </div>
        </div>

        {/* NODE 4: VIDEO / MULTIMEDIA ICON (Bottom-Right / 5:30 o'clock) */}
        <div className="absolute bottom-20 right-12 sm:right-14 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-indigo-400 shadow-[0_0_25px_rgba(99,102,241,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <Video className="w-6 h-6 text-white drop-shadow-[0_0_8px_#818CF8] group-hover:scale-110 transition-transform" />
          </div>
        </div>

        {/* NODE 5: DOCUMENT ICON (Bottom-Left / 7:30 o'clock) */}
        <div className="absolute bottom-20 left-12 sm:left-14 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-cyan-400 shadow-[0_0_25px_rgba(0,240,255,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <FileText className="w-7 h-7 text-white drop-shadow-[0_0_8px_#00F0FF] group-hover:scale-110 transition-transform" />
          </div>
        </div>

        {/* NODE 6: PRESENTATION / WHITEBOARD ICON (Mid-Left / 9:30 o'clock) */}
        <div className="absolute top-1/2 -translate-y-1/2 left-4 sm:left-6 z-30">
          <div className="w-14 h-14 sm:w-16 sm:h-16 rounded-full bg-[#061434]/90 border-2 border-blue-400 shadow-[0_0_25px_rgba(59,130,246,0.5)] flex items-center justify-center text-white hover:scale-110 transition-transform cursor-pointer group">
            <Presentation className="w-7 h-7 text-white drop-shadow-[0_0_8px_#38BDF8] group-hover:scale-110 transition-transform" />
          </div>
        </div>
      </div>
    </div>
  );
};
