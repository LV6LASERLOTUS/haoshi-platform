import React, { useEffect, useState } from 'react';
import { View, Text, Pressable, Animated } from 'react-native';
import { useT } from '../theme';
import { AVATARS } from '../data/orgs';
import Pop from './ui/Pop';
import PopBtn from './ui/PopBtn';
import Ring from './ui/Ring';
import { Row } from './ui/Layout';

/* ───────────── 結果卡片 ───────────── */
export default function ResultCard({ o, i, top, saved, onSave, onFeedback, toast }) {
  const c = useT();
  const [open, setOpen] = useState(false);
  const [fade] = useState(() => new Animated.Value(0));
  useEffect(() => { Animated.timing(fade, { toValue: 1, duration: 350, delay: i * 70, useNativeDriver: true }).start(); }, [fade, i]);
  return (
    <Animated.View style={{ opacity: fade, marginBottom: 16, transform: [{ translateY: fade.interpolate({ inputRange: [0, 1], outputRange: [8, 0] }) }] }}>
      <Pop r={22} bg={top ? c.primarySoft : c.surface}>
        <View style={{ padding: 16 }}>
          <View style={{ flexDirection: 'row', gap: 12, alignItems: 'flex-start' }}>
            <View style={{ width: 46, height: 46, borderRadius: 23, borderWidth: 2.5, borderColor: c.ol, backgroundColor: AVATARS[i % 4], alignItems: 'center', justifyContent: 'center' }}>
              <Text style={{ fontSize: 18, fontWeight: '800', color: '#25303b' }}>{o.n[0]}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={{ alignSelf: 'flex-start', backgroundColor: c.yellow, borderColor: c.ol, borderWidth: 2, borderRadius: 999, paddingHorizontal: 10 }}>
                <Text style={{ fontSize: 12, fontWeight: '700', color: '#25303b' }}>#{i + 1}{top ? ' 最推薦' : ''}</Text>
              </View>
              <Text style={{ color: c.ink, fontSize: 18, fontWeight: '700', marginTop: 4 }}>{o.n}</Text>
              <Text style={{ color: c.muted, fontSize: 13 }}>✓ 自律聯盟會員 · {o.c} · {o.a}</Text>
            </View>
            <Ring p={o.p} />
          </View>

          <Row style={{ marginVertical: 10, gap: 6 }}>
            {o.t.map((t) => (
              <Text key={t} style={{ fontSize: 12, fontWeight: '600', color: c.primary, backgroundColor: c.primarySoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 2, overflow: 'hidden' }}>{t}</Text>
            ))}
            {o.w.map((t) => (
              <Text key={t} style={{ fontSize: 12, fontWeight: '600', color: c.warn, backgroundColor: c.accentSoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 2, overflow: 'hidden' }}>⚠ {t}</Text>
            ))}
          </Row>

          <View style={{ backgroundColor: c.surface, borderWidth: 2, borderStyle: 'dashed', borderColor: c.muted, borderRadius: 14, padding: 12 }}>
            <Text style={{ color: c.primary, fontSize: 12, fontWeight: '700' }}>✦ AI 推薦原因</Text>
            <Text style={{ color: c.ink, fontSize: 14, lineHeight: 21 }}>{o.why}</Text>
          </View>

          {open && (
            <View style={{ marginTop: 12 }}>
              {Object.entries(o.s).map(([k, v]) => (
                <View key={k} style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginVertical: 5 }}>
                  <Text style={{ width: 40, color: c.muted, fontSize: 13 }}>{k}</Text>
                  <View style={{ flex: 1, height: 6, borderRadius: 6, backgroundColor: c.line }}>
                    <View style={{ width: `${v}%`, height: 6, borderRadius: 6, backgroundColor: c.primary }} />
                  </View>
                  <Text style={{ width: 28, textAlign: 'right', color: c.muted, fontSize: 13 }}>{v}</Text>
                </View>
              ))}
            </View>
          )}

          <View style={{ flexDirection: 'row', gap: 8, marginTop: 12 }}>
            <PopBtn style={{ flex: 1 }} bg={c.primary} color={c.primaryInk} bold onPress={() => toast(`已為你開啟「${o.n}」的聯絡方式（示意）`)}>聯絡此單位</PopBtn>
            <PopBtn bg={saved ? c.accentSoft : c.surface} color={saved ? c.accent : c.ink} onPress={onSave}>{saved ? '★ 已收藏' : '☆ 收藏'}</PopBtn>
            <PopBtn onPress={() => setOpen(!open)}>{open ? '收合' : '比對細節'}</PopBtn>
          </View>

          <Pressable onPress={onFeedback} accessibilityRole="button" style={{ alignSelf: 'flex-end', paddingVertical: 8 }}>
            <Text style={{ color: c.muted, fontSize: 13, textDecorationLine: 'underline' }}>💬 回饋修正</Text>
          </Pressable>
        </View>
      </Pop>
    </Animated.View>
  );
}
