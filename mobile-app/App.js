// 好事大平台｜AI 智慧媒合 — React Native (Expo) 版本

import React, { useEffect, useRef, useState } from 'react';
import {
  View, SafeAreaView, StatusBar, Animated, Easing, BackHandler, Keyboard,
  useColorScheme, useWindowDimensions,
} from 'react-native';

import { LIGHT, DARK, ThemeCtx } from './theme';
import { ORGS, score } from './data/orgs';
import SearchScreen from './screens/SearchScreen';
import ResultsScreen from './screens/ResultsScreen';
import Toast, { useToast } from './components/ui/Toast';

/* ───────────── 主畫面：兩頁 + 滑動轉場 ───────────── */
export default function App() {
  const system = useColorScheme();
  const [override, setOverride] = useState(null);
  const c = (override ?? system) === 'dark' ? DARK : LIGHT;
  const { width } = useWindowDimensions();

  // 搜尋條件
  const [q, setQ] = useState('');
  const [cat, setCat] = useState('');
  const [area, setArea] = useState('不限');
  const [budget, setBudget] = useState('不限');

  // 結果
  const [loading, setLoading] = useState(false);
  const [res, setRes] = useState(null);
  const [submitted, setSubmitted] = useState('');
  const [runId, setRunId] = useState(0); // 每次新搜尋重置結果頁（排序、收藏）

  // 頁面轉場：0 = 搜尋頁，1 = 結果頁
  const [page, setPage] = useState('search');
  const nav = useRef(new Animated.Value(0)).current;
  const { show: toast, msg, opacity } = useToast();

  const goTo = (target) => {
    setPage(target);
    Animated.timing(nav, {
      toValue: target === 'results' ? 1 : 0,
      duration: 320,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  };

  // Android 實體返回鍵：結果頁時回到搜尋頁
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (page === 'results') { goTo('search'); return true; }
      return false;
    });
    return () => sub.remove();
  }, [page]);

  const run = (text = q) => {
    const query = text.trim();
    if (!query && !cat) return toast('請先描述需求，或選擇服務對象');
    Keyboard.dismiss();
    setSubmitted(query || cat);
    setRunId((n) => n + 1);
    setLoading(true);
    setRes(null);
    goTo('results');
    setTimeout(() => {
      const f = { cat, area, budget };
      setRes(ORGS.map((o) => ({ ...o, p: score(o, query, f) })).sort((a, b) => b.p - a.p).slice(0, 4));
      setLoading(false);
    }, 900); // ← 換成真正的 API 呼叫
  };

  // 搜尋頁往左微移（視差），結果頁從右側滑入
  const searchStyle = {
    opacity: nav.interpolate({ inputRange: [0, 1], outputRange: [1, 0.6] }),
    transform: [{ translateX: nav.interpolate({ inputRange: [0, 1], outputRange: [0, -width * 0.3] }) }],
  };
  const resultsStyle = {
    transform: [{ translateX: nav.interpolate({ inputRange: [0, 1], outputRange: [width, 0] }) }],
  };
  const fill = { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: c.bg };

  return (
    <ThemeCtx.Provider value={c}>
      <SafeAreaView style={{ flex: 1, backgroundColor: c.bg }}>
        <StatusBar barStyle={c.dark ? 'light-content' : 'dark-content'} />
        <View style={{ flex: 1, overflow: 'hidden' }}>
          <Animated.View style={[fill, searchStyle]} pointerEvents={page === 'search' ? 'auto' : 'none'}>
            <SearchScreen
              q={q} setQ={setQ} cat={cat} setCat={setCat}
              area={area} setArea={setArea} budget={budget} setBudget={setBudget}
              onRun={run} onToggleTheme={() => setOverride(c.dark ? 'light' : 'dark')} toast={toast}
            />
          </Animated.View>

          <Animated.View style={[fill, resultsStyle]} pointerEvents={page === 'results' ? 'auto' : 'none'}>
            <ResultsScreen
              key={runId}
              query={submitted} loading={loading} res={res}
              onBack={() => goTo('search')} toast={toast}
            />
          </Animated.View>
        </View>

        <Toast msg={msg} opacity={opacity} bottom={page === 'results' ? 100 : 40} />
      </SafeAreaView>
    </ThemeCtx.Provider>
  );
}
