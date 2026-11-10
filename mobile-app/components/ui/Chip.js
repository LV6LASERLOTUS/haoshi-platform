import React from 'react';
import { Text, Pressable } from 'react-native';
import { useT } from '../../theme';

export default function Chip({ label, on, onPress, dashed }) {
  const c = useT();
  return (
    <Pressable
      onPress={onPress}
      style={{
        borderWidth: 2, borderColor: c.ol, borderStyle: dashed ? 'dashed' : 'solid', borderRadius: 999,
        paddingVertical: 4, paddingHorizontal: 14, backgroundColor: on ? c.yellow : c.surface,
      }}
    >
      <Text style={{ fontSize: 14, color: on ? '#25303b' : dashed ? c.muted : c.ink, fontWeight: on ? '700' : '400' }}>{label}</Text>
    </Pressable>
  );
}
