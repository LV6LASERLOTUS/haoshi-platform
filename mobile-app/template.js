// 好事大平台｜AI 智慧媒合 — React Native (Expo) 版本
// 安裝：npx expo install react-native-svg
// 之後把 App.js 放到 Expo 專案根目錄即可執行。

import React, { useContext, useEffect, useRef, useState } from 'react';
import {
  View, Text, TextInput, Pressable, ScrollView, Animated,
  SafeAreaView, StatusBar, useColorScheme,
} from 'react-native';
import Svg, { Rect, Path, Circle, G, Text as SText } from 'react-native-svg';

/* ───────────── Theme ───────────── */
const LIGHT = {
  dark: false, bg: '#edf3f8', surface: '#ffffff', ink: '#1f2a37', muted: '#5d6b78', line: '#cfdde9',
  ol: '#25303b', hero: '#2f7ab5', yellow: '#f0b83f', primary: '#2f7ab5', primaryInk: '#ffffff',
  primarySoft: '#dcebf6', accent: '#e0524b', accentSoft: '#fde4e1', warn: '#a85a00',
};
const DARK = {
  dark: true, bg: '#0f1a24', surface: '#17232f', ink: '#eef3f7', muted: '#9fb1c0', line: '#2b3e50',
  ol: '#05090d', hero: '#2b6a9e', yellow: '#f0b83f', primary: '#5aa7dd', primaryInk: '#06121c',
  primarySoft: '#183247', accent: '#ff7a72', accentSoft: '#40201f', warn: '#f5c15a',
};
const ThemeCtx = React.createContext(LIGHT);
const useT = () => useContext(ThemeCtx);

/* ───────────── Mock data（之後換成你的後端 API）───────────── */
const ORGS = [
  { n: '台灣偏鄉教育協會', c: '兒童 & 青少年', a: '中部', b: '5–20 萬', s: { 領域: 95, 地區: 96, 預算: 92, 經驗: 88 }, t: ['偏鄉教育', '科技營隊', '志工充足'], w: [], why: '過去 5 次偏鄉科技營隊經驗，且活動預算區間與你的需求完全吻合。', k: '營隊 科技 偏鄉 國小 教育' },
  { n: '青年夢想協進會', c: '兒童 & 青少年', a: '北部', b: '5–20 萬', s: { 領域: 90, 地區: 62, 預算: 88, 經驗: 84 }, t: ['青少年發展', '課後陪伴'], w: ['志工調度需提前 2 週'], why: '領域高度契合，但據點在北部，需留意志工調度時間與交通安排。', k: '青少年 夢想 營隊 陪伴' },
  { n: '陽光科普推廣中心', c: '一般民眾', a: '南部', b: '20 萬以上', s: { 領域: 82, 地區: 55, 預算: 70, 經驗: 90 }, t: ['科普教學', '大型活動'], w: ['報價高於預算'], why: '科普教學背景強、活動規模符合期待，但預算上限略高。', k: '科普 科學 科技 教學' },
  { n: '銀髮長照關懷協會', c: '老人', a: '北部', b: '5 萬以下', s: { 領域: 92, 地區: 80, 預算: 95, 經驗: 86 }, t: ['長者陪伴', '居家關懷'], w: [], why: '長期深耕長者陪伴服務，與你的服務對象高度一致。', k: '老人 長者 長照 陪伴 關懷' },
  { n: '身心障礙者共融工坊', c: '身心障礙者', a: '中部', b: '5–20 萬', s: { 領域: 90, 地區: 90, 預算: 85, 經驗: 80 }, t: ['共融活動', '職能訓練'], w: [], why: '提供多元共融活動設計，並有中部在地服務據點。', k: '身心障礙 共融 職能 活動' },
  { n: '山海環境守護團', c: '環境保護 & 動物保護', a: '東部', b: '5 萬以下', s: { 領域: 88, 地區: 50, 預算: 93, 經驗: 82 }, t: ['淨灘', '環境教育'], w: ['位於東部'], why: '環境教育與戶外活動經驗豐富，適合規劃生態類課程。', k: '環境 淨灘 生態 戶外 動物' },
];
const CATS = ['兒童 & 青少年', '老人', '身心障礙者', '婦女', '疾病患者', '環境保護 & 動物保護', '一般民眾'];
const AREAS = ['不限', '北部', '中部', '南部', '東部'];
const BUDGETS = ['不限', '5 萬以下', '5–20 萬', '20 萬以上'];
const EXAMPLES = ['中部偏鄉國小科技營隊', '長者陪伴志工', '身障者共融活動', '淨灘環境教育'];
const AVATARS = ['#8cc0e6', '#f0b83f', '#f29b95', '#b9c98a'];
const SORTS = [['match', '符合度'], ['area', '地區'], ['budget', '預算']];

function score(o, q, f) {
  const v = Object.values(o.s);
  let base = v.reduce((a, b) => a + b, 0) / v.length;
  const hits = q.split(/[\s，,、]+/).filter((w) => w && o.k.includes(w)).length;
  if (f.cat && o.c === f.cat) base += 6;
  if (f.area !== '不限' && o.a === f.area) base += 4;
  if (f.budget !== '不限' && o.b === f.budget) base += 4;
  return Math.min(98, Math.round(base - 6 + hits * 3));
}

/* ───────────── 卡通風 UI 基礎元件 ───────────── */
// 跨平台的「硬陰影」：用一個偏移的深色 View 疊在後面（Android 不支援實色 shadow）
function Pop({ r = 16, off = 3, bw = 2.5, bg, sc, style, children, pressed }) {
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

function PopBtn({ onPress, bg, color, children, r = 12, off = 2, style, bold }) {
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

function Chip({ label, on, onPress, dashed }) {
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

const Label = ({ children }) => {
  const c = useT();
  return <Text style={{ fontSize: 13, color: c.muted, fontWeight: '600', marginTop: 16, marginBottom: 8 }}>{children}</Text>;
};
const Row = ({ children, style }) => <View style={[{ flexDirection: 'row', flexWrap: 'wrap', gap: 8 }, style]}>{children}</View>;

/* ───────────── SVG：Logo、Hero 插畫、分數圓環 ───────────── */
function Logo() {
  return (
    <Svg width={36} height={36} viewBox="0 0 36 36" fill="none" strokeWidth={3.5}>
      <Rect x={3} y={3} width={18} height={18} rx={2} stroke="#e0524b" />
      <Rect x={12} y={9} width={18} height={18} rx={2} stroke="#2f7ab5" />
      <Rect x={17} y={15} width={16} height={16} rx={2} stroke="#f0b83f" />
    </Svg>
  );
}

function HeroArt() {
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

function Ring({ p }) {
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

/* ───────────── 結果卡片 ───────────── */
function Card({ o, i, top, saved, onSave, toast }) {
  const c = useT();
  const [open, setOpen] = useState(false);
  const [fb, setFb] = useState(false);
  const fade = useRef(new Animated.Value(0)).current;
  useEffect(() => { Animated.timing(fade, { toValue: 1, duration: 350, delay: i * 70, useNativeDriver: true }).start(); }, []);
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

          <Pressable onPress={() => setFb(!fb)} style={{ alignSelf: 'flex-end', paddingVertical: 8 }}>
            <Text style={{ color: c.muted, fontSize: 13, textDecorationLine: 'underline' }}>💬 回饋修正</Text>
          </Pressable>

          {fb && (
            <View style={{ padding: 12, borderWidth: 1.5, borderStyle: 'dashed', borderColor: c.line, borderRadius: 12 }}>
              <Text style={{ color: c.muted, fontSize: 13, marginBottom: 8 }}>哪裡不太對？選擇後我們會重新調整推薦</Text>
              <Row>
                {['領域不符', '地區太遠', '預算不合', '規模不對', '其他'].map((x) => (
                  <Chip key={x} label={x} onPress={() => { setFb(false); toast(`謝謝回饋，已記錄「${x}」`); }} />
                ))}
              </Row>
            </View>
          )}
        </View>
      </Pop>
    </Animated.View>
  );
}

function Skeleton() {
  const c = useT();
  const v = useRef(new Animated.Value(0.4)).current;
  useEffect(() => {
    const a = Animated.loop(Animated.sequence([
      Animated.timing(v, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(v, { toValue: 0.4, duration: 600, useNativeDriver: true }),
    ]));
    a.start();
    return () => a.stop();
  }, []);
  return <Animated.View style={{ opacity: v, height: 150, borderRadius: 22, backgroundColor: c.line, marginBottom: 12 }} />;
}

/* ───────────── 主畫面 ───────────── */
export default function App() {
  const system = useColorScheme();
  const [override, setOverride] = useState(null);
  const c = (override ?? system) === 'dark' ? DARK : LIGHT;

  const [q, setQ] = useState('');
  const [cat, setCat] = useState('');
  const [area, setArea] = useState('不限');
  const [budget, setBudget] = useState('不限');
  const [adv, setAdv] = useState(false);
  const [focus, setFocus] = useState(false);
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [sort, setSort] = useState('match');
  const [saved, setSaved] = useState({});
  const [msg, setMsg] = useState('');

  const scroll = useRef(null);
  const resY = useRef(0);
  const toastV = useRef(new Animated.Value(0)).current;
  const timer = useRef(null);

  const toast = (m) => {
    setMsg(m);
    Animated.timing(toastV, { toValue: 1, duration: 200, useNativeDriver: true }).start();
    clearTimeout(timer.current);
    timer.current = setTimeout(() => Animated.timing(toastV, { toValue: 0, duration: 200, useNativeDriver: true }).start(), 2200);
  };

  const run = (text = q) => {
    const query = text.trim();
    if (!query && !cat) return toast('請先描述需求，或選擇服務對象');
    setLoading(true);
    setRes(null);
    setTimeout(() => {
      const f = { cat, area, budget };
      setRes(ORGS.map((o) => ({ ...o, p: score(o, query, f) })).sort((a, b) => b.p - a.p).slice(0, 4));
      setLoading(false);
      setTimeout(() => scroll.current?.scrollTo({ y: resY.current, animated: true }), 50);
    }, 900); // ← 換成真正的 API 呼叫
  };

  let list = res ? [...res] : [];
  if (sort === 'budget') list.sort((a, b) => b.s.預算 - a.s.預算);
  if (sort === 'area') list.sort((a, b) => b.s.地區 - a.s.地區);
  const savedCount = Object.values(saved).filter(Boolean).length;

  return (
    <ThemeCtx.Provider value={c}>
      <SafeAreaView style={{ flex: 1, backgroundColor: c.bg }}>
        <StatusBar barStyle={c.dark ? 'light-content' : 'dark-content'} />
        <ScrollView ref={scroll} keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: 16, paddingBottom: 110, maxWidth: 720, width: '100%', alignSelf: 'center' }}>
          {/* Header */}
          <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 12 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
              <Logo />
              <Text style={{ color: c.ink, fontSize: 18, fontWeight: '700' }}>好事大平台</Text>
            </View>
            <Pressable onPress={() => setOverride(c.dark ? 'light' : 'dark')} style={{ borderWidth: 2, borderColor: c.ol, borderRadius: 999, backgroundColor: c.surface, paddingHorizontal: 12, paddingVertical: 5 }}>
              <Text style={{ color: c.muted, fontSize: 14 }}>◐ 外觀</Text>
            </Pressable>
          </View>

          {/* Hero */}
          <Pop r={26} bg={c.hero}>
            <View style={{ flexDirection: 'row', alignItems: 'center', paddingVertical: 20, paddingLeft: 18, paddingRight: 8 }}>
              <View style={{ flex: 1 }}>
                <Text style={{ color: '#fff', fontSize: 30, fontWeight: '800', textShadowColor: 'rgba(0,0,0,.25)', textShadowOffset: { width: 2, height: 2 }, textShadowRadius: 0 }}>好事大平台</Text>
                <Text style={{ color: '#fff', fontSize: 15, fontWeight: '600', marginTop: 6, lineHeight: 22 }}>AI 智慧媒合助理{'\n'}說說需求，幫你找到對的夥伴</Text>
                <Row style={{ marginTop: 14, gap: 6 }}>
                  {['280 家認證組織', '財務透明・良善治理'].map((t) => (
                    <Text key={t} style={{ backgroundColor: c.yellow, color: '#25303b', borderColor: c.ol, borderWidth: 2, borderRadius: 999, paddingHorizontal: 10, fontSize: 12, fontWeight: '700', overflow: 'hidden' }}>{t}</Text>
                  ))}
                </Row>
              </View>
              <HeroArt />
            </View>
          </Pop>

          {/* 輸入區 */}
          <Pop r={22} sc={focus ? c.yellow : c.ol} style={{ marginTop: 20 }}>
            <TextInput
              value={q} onChangeText={setQ} multiline onFocus={() => setFocus(true)} onBlur={() => setFocus(false)}
              placeholder="例如：我們想找中部偏鄉國小舉辦科技營隊，預算 10 萬內，約 60 位學生…"
              placeholderTextColor={c.muted}
              style={{ color: c.ink, fontSize: 16, minHeight: 96, padding: 16, paddingBottom: 4, textAlignVertical: 'top', lineHeight: 24 }}
            />
            <View style={{ flexDirection: 'row', alignItems: 'center', flexWrap: 'wrap', gap: 8, padding: 12 }}>
              {[['⚙ 進階條件', () => setAdv(!adv), adv], ['🖼 照片', () => toast('接上 expo-image-picker（示意）')], ['📎 檔案', () => toast('接上 expo-document-picker（示意）')]].map(([t, fn, on]) => (
                <Pressable key={t} onPress={fn} style={{ backgroundColor: on ? c.primarySoft : c.bg, borderRadius: 10, paddingHorizontal: 12, paddingVertical: 7 }}>
                  <Text style={{ color: on ? c.primary : c.muted, fontSize: 14 }}>{t}</Text>
                </Pressable>
              ))}
              <PopBtn style={{ marginLeft: 'auto' }} bg={c.primary} color={c.primaryInk} bold r={14} onPress={() => run()}>開始媒合</PopBtn>
            </View>
            {adv && (
              <View style={{ paddingHorizontal: 12, paddingBottom: 12 }}>
                <Text style={{ fontSize: 12, color: c.muted, marginBottom: 6 }}>地區</Text>
                <Row>{AREAS.map((a) => <Chip key={a} label={a} on={area === a} onPress={() => setArea(a)} />)}</Row>
                <Text style={{ fontSize: 12, color: c.muted, marginTop: 10, marginBottom: 6 }}>預算</Text>
                <Row>{BUDGETS.map((b) => <Chip key={b} label={b} on={budget === b} onPress={() => setBudget(b)} />)}</Row>
              </View>
            )}
          </Pop>

          <Label>服務對象</Label>
          <Row>{CATS.map((x) => <Chip key={x} label={x} on={cat === x} onPress={() => setCat(cat === x ? '' : x)} />)}</Row>
          <Label>試試看</Label>
          <Row>{EXAMPLES.map((x) => <Chip key={x} dashed label={x} onPress={() => { setQ(x); run(x); }} />)}</Row>

          {/* 結果 */}
          <View onLayout={(e) => { resY.current = e.nativeEvent.layout.y; }} style={{ marginTop: 28 }}>
            {loading && (
              <>
                <Text style={{ color: c.ink, fontSize: 17, fontWeight: '700', marginBottom: 12 }}>AI 正在分析需求…</Text>
                <Skeleton /><Skeleton />
              </>
            )}
            {res && !loading && (
              <>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                  <View>
                    <Text style={{ color: c.ink, fontSize: 17, fontWeight: '700' }}>找到 {list.length} 個推薦單位</Text>
                    <Text style={{ color: c.muted, fontSize: 13 }}>已依你的需求計算符合度</Text>
                  </View>
                  <View style={{ flexDirection: 'row', backgroundColor: c.line, borderRadius: 10, padding: 3 }}>
                    {SORTS.map(([k, t]) => (
                      <Pressable key={k} onPress={() => setSort(k)} style={{ borderRadius: 8, paddingHorizontal: 12, paddingVertical: 4, backgroundColor: sort === k ? c.surface : 'transparent' }}>
                        <Text style={{ fontSize: 13, color: sort === k ? c.ink : c.muted, fontWeight: sort === k ? '600' : '400' }}>{t}</Text>
                      </Pressable>
                    ))}
                  </View>
                </View>
                {list.map((o, i) => (
                  <Card key={o.n} o={o} i={i} top={i === 0 && sort === 'match'} saved={!!saved[o.n]}
                    onSave={() => { setSaved({ ...saved, [o.n]: !saved[o.n] }); toast(saved[o.n] ? '已取消收藏' : '已收藏'); }} toast={toast} />
                ))}
              </>
            )}
          </View>
        </ScrollView>

        {/* 收藏列 */}
        {savedCount > 0 && (
          <View style={{ position: 'absolute', left: 0, right: 0, bottom: 0, backgroundColor: c.surface, borderTopWidth: 2.5, borderColor: c.ol, padding: 12, paddingBottom: 24, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
            <Text style={{ color: c.ink, fontSize: 14 }}>已收藏 {savedCount} 個單位</Text>
            <PopBtn bg={c.primary} color={c.primaryInk} bold onPress={() => toast('比較功能（示意）')}>比較已收藏</PopBtn>
          </View>
        )}

        {/* Toast */}
        <Animated.View pointerEvents="none" style={{ position: 'absolute', alignSelf: 'center', bottom: savedCount ? 100 : 40, opacity: toastV, backgroundColor: c.ink, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8 }}>
          <Text style={{ color: c.bg, fontSize: 14 }}>{msg}</Text>
        </Animated.View>
      </SafeAreaView>
    </ThemeCtx.Provider>
  );
}
