import React from 'react';
import { Pressable } from 'react-native';
import Svg, { Path } from 'react-native-svg';
import { useT } from '../../theme';
import Pop from './Pop';

/* 卡通風圓形返回鍵 */
export default function BackButton({ onPress }) {
  const c = useT();
  return (
    <Pressable onPress={onPress} hitSlop={8} accessibilityRole="button" accessibilityLabel="返回">
      {({ pressed }) => (
        <Pop r={999} off={2} bw={2} pressed={pressed}>
          <Svg width={36} height={36} viewBox="0 0 36 36">
            <Path d="M21 11 L14 18 L21 25" fill="none" stroke={c.ink} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />
          </Svg>
        </Pop>
      )}
    </Pressable>
  );
}
