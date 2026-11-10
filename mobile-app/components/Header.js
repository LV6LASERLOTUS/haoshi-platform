import React from 'react';
import { View, Text, Pressable } from 'react-native';
import { useT } from '../theme';
import Logo from './art/Logo';

export default function Header({ onToggleTheme }) {
  const c = useT();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12 }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
        <Logo />
        <Text style={{ color: c.ink, fontSize: 18, fontWeight: '700' }}>好事大平台</Text>
      </View>
      <Pressable onPress={onToggleTheme} style={{ borderWidth: 2, borderColor: c.ol, borderRadius: 999, backgroundColor: c.surface, paddingHorizontal: 12, paddingVertical: 5 }}>
        <Text style={{ color: c.muted, fontSize: 14 }}>◐ 外觀</Text>
      </Pressable>
    </View>
  );
}
