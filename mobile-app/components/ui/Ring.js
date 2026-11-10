import React from 'react';
import { View, Text } from 'react-native';
import Svg, { Circle } from 'react-native-svg';
import { useT } from '../../theme';

/* 分數圓環 */
export default function Ring({ p }) {
  const c = useT();
  const size = 64, r = 25, circ = 2 * Math.PI * r;
  return (
    <View style={{ width: size, height: size, borderRadius: size / 2, borderWidth: 2.5, borderColor: c.ol, backgroundColor: c.surface, alignItems: 'center', justifyContent: 'center' }}>
      <Svg width={size - 5} height={size - 5} viewBox="0 0 59 59" style={{ position: 'absolute' }}>
        <Circle cx={29.5} cy={29.5} r={r} stroke={c.line} strokeWidth={5} fill="none" />
        <Circle cx={29.5} cy={29.5} r={r} stroke={c.primary} strokeWidth={5} fill="none" strokeLinecap="round"
          strokeDasharray={`${(circ * p) / 100} ${circ}`} rotation={-90} origin="29.5, 29.5" />
      </Svg>
      <Text style={{ color: c.ink, fontSize: 15, fontWeight: '800', lineHeight: 17 }}>{p}%</Text>
      <Text style={{ color: c.muted, fontSize: 9 }}>符合</Text>
    </View>
  );
}
