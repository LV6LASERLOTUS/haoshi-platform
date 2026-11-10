import React from 'react';
import Svg, { Rect, Path, Circle, G, Text as SText } from 'react-native-svg';

export default function HeroArt() {
  const sp = { stroke: '#25303b', strokeWidth: 2.5, strokeLinejoin: 'round', strokeLinecap: 'round' };
  return (
    <Svg width={150} height={97.5} viewBox="0 0 200 130">
      <G rotation={-8} origin="38, 28"><Rect x={18} y={10} width={40} height={30} fill="#fff" {...sp} /><SText x={38} y={33} fontSize={20} textAnchor="middle" fill="#2f7ab5">♡</SText></G>
      <G rotation={7} origin="166, 28"><Rect x={145} y={8} width={42} height={32} fill="#fff" {...sp} /><SText x={166} y={32} fontSize={22} textAnchor="middle" fill="#e0524b">♥</SText></G>
      <Path d="M44 112 Q32 84 40 50" fill="none" stroke="#b9c98a" strokeWidth={9} strokeLinecap="round" />
      <Path d="M156 112 Q168 84 160 50" fill="none" stroke="#b9c98a" strokeWidth={9} strokeLinecap="round" />
      <Path d="M34 122 Q56 92 78 122Z" fill="#b9c98a" {...sp} /><Circle cx={56} cy={82} r={15} fill="#25303b" {...sp} /><Circle cx={57} cy={85} r={10} fill="#fff" {...sp} />
      <Path d="M122 122 Q144 92 166 122Z" fill="#f0b83f" {...sp} /><Circle cx={144} cy={82} r={15} fill="#25303b" {...sp} /><Circle cx={143} cy={85} r={10} fill="#fff" {...sp} />
      <Path d="M60 122 Q100 74 140 122Z" fill="#e0524b" {...sp} /><Circle cx={100} cy={66} r={28} fill="#25303b" {...sp} /><Circle cx={100} cy={72} r={18} fill="#fff" {...sp} />
      <Circle cx={93} cy={70} r={1.6} fill="#25303b" /><Circle cx={107} cy={70} r={1.6} fill="#25303b" />
      <Path d="M93 78 Q100 84 107 78" fill="none" stroke="#25303b" strokeWidth={2} strokeLinecap="round" />
      <Path d="M70 44 L62 38M130 44 L138 38M100 30 L100 20" stroke="#f6a8a2" strokeWidth={3} strokeLinecap="round" />
      <G rotation={-2} origin="100, 118"><Rect x={26} y={106} width={148} height={22} rx={4} fill="#f0b83f" {...sp} /><SText x={100} y={122} fontSize={12} fontWeight="700" textAnchor="middle" fill="#fff">台灣公益團體自律聯盟！</SText></G>
    </Svg>
  );
}
