import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useT } from '../../theme';
import Pop from './Pop';

export default function PopBtn({ onPress, bg, color, children, r = 12, off = 2, style, bold }) {
  const c = useT();
  return (
    <Pressable onPress={onPress} style={style}>
      {({ pressed }) => (
        <Pop r={r} off={off} bw={2} bg={bg} pressed={pressed}>
          <View style={{ paddingVertical: 8, paddingHorizontal: 14, alignItems: 'center' }}>
            <Text style={{ color: color || c.ink, fontSize: 14, fontWeight: bold ? '700' : '500' }}>{children}</Text>
          </View>
        </Pop>
      )}
    </Pressable>
  );
}
