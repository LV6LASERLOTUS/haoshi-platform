import React from 'react';
import { View } from 'react-native';
import { useT } from '../../theme';

/* ───────────── 卡通風 UI 基礎元件 ───────────── */
// 跨平台的「硬陰影」：用一個偏移的深色 View 疊在後面（Android 不支援實色 shadow）
export default function Pop({ r = 16, off = 3, bw = 2.5, bg, sc, style, children, pressed }) {
  const c = useT();
  return (
    <View style={[{ paddingRight: off, paddingBottom: off }, style]}>
      {!pressed && (
        <View style={{ position: 'absolute', top: off, left: off, right: 0, bottom: 0, borderRadius: r, backgroundColor: sc || c.ol }} />
      )}
      <View
        style={{
          backgroundColor: bg || c.surface, borderColor: c.ol, borderWidth: bw, borderRadius: r, overflow: 'hidden',
          transform: pressed ? [{ translateX: off }, { translateY: off }] : [],
        }}
      >
        {children}
      </View>
    </View>
  );
}
