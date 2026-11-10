import React from 'react';
import Svg, { Rect } from 'react-native-svg';

export default function Logo() {
  return (
    <Svg width={36} height={36} viewBox="0 0 36 36" fill="none" strokeWidth={3.5}>
      <Rect x={3} y={3} width={18} height={18} rx={2} stroke="#e0524b" />
      <Rect x={12} y={9} width={18} height={18} rx={2} stroke="#2f7ab5" />
      <Rect x={17} y={15} width={16} height={16} rx={2} stroke="#f0b83f" />
    </Svg>
  );
}
