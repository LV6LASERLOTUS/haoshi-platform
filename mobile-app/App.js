// 好事大平台｜AI 智慧媒合 — React Native (Expo) 版本

import React, { useCallback, useEffect, useRef, useState } from 'react';
import {
  View, SafeAreaView, StatusBar, Animated, Easing, BackHandler, Keyboard,
  useColorScheme, useWindowDimensions,
} from 'react-native';

import { LIGHT, DARK, ThemeCtx } from './theme';
import { fetchMatches } from './api/match';
import { submitFeedback, makeQuestionId } from './api/feedback';
import SearchScreen from './screens/SearchScreen';
import ResultsScreen from './screens/ResultsScreen';
import Toast, { useToast } from './components/ui/Toast';
import FeedbackSheet from './components/FeedbackSheet';

/* ───────────── 主畫面：兩頁 + 滑動轉場 ───────────── */
export default function App() {
  const systemColorScheme = useColorScheme();
  const [themeOverride, setThemeOverride] = useState(null);
  const theme = (themeOverride ?? systemColorScheme) === 'dark' ? DARK : LIGHT;
  const { width: screenWidth } = useWindowDimensions();

  // 搜尋條件
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [area, setArea] = useState('不限');
  const [budget, setBudget] = useState('不限');

  // 結果
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [submittedQuery, setSubmittedQuery] = useState('');
  const [searchId, setSearchId] = useState(0); // 每次新搜尋重置結果頁（排序、收藏）
  const latestSearchId = useRef(0); // 忽略較舊搜尋的延遲回應
  const [questionId, setQuestionId] = useState(''); // 回饋用的問題 ID（每次搜尋一個）

  // 回饋修正面板：要回饋的那一筆推薦（關閉時保留資料，避免滑出動畫時內容變空白）
  const [feedbackOrg, setFeedbackOrg] = useState(null);
  const [feedbackVisible, setFeedbackVisible] = useState(false);
  const openFeedback = useCallback((org) => { setFeedbackOrg(org); setFeedbackVisible(true); }, []);

  // 頁面轉場：0 = 搜尋頁，1 = 結果頁
  const [page, setPage] = useState('search');
  const [pageTransition] = useState(() => new Animated.Value(0));
  const { show: showToast, msg: toastMessage, opacity: toastOpacity } = useToast();

  const navigateTo = useCallback((targetPage) => {
    setPage(targetPage);
    Animated.timing(pageTransition, {
      toValue: targetPage === 'results' ? 1 : 0,
      duration: 320,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    }).start();
  }, [pageTransition]);

  // Android 實體返回鍵：結果頁時回到搜尋頁
  useEffect(() => {
    const backHandlerSubscription = BackHandler.addEventListener('hardwareBackPress', () => {
      if (page === 'results') { navigateTo('search'); return true; }
      return false;
    });
    return () => backHandlerSubscription.remove();
  }, [page, navigateTo]);

  const runSearch = (searchText = query) => {
    const trimmedQuery = searchText.trim();
    if (!trimmedQuery && !category) return showToast('請先描述需求，或選擇服務對象');
    Keyboard.dismiss();
    const requestText = trimmedQuery || category; // 後端 request_text 為必填
    const currentSearchId = latestSearchId.current + 1;
    latestSearchId.current = currentSearchId;
    const isLatestSearch = () => latestSearchId.current === currentSearchId;

    setSubmittedQuery(requestText);
    setSearchId(currentSearchId);
    setQuestionId(makeQuestionId(currentSearchId));
    setFeedbackVisible(false);
    setLoading(true);
    setResults(null);
    navigateTo('results');

    fetchMatches({ text: requestText, category, area, budget })
      .then((matches) => { if (isLatestSearch()) setResults(matches); })
      .catch(() => {
        if (!isLatestSearch()) return;
        showToast('連線失敗，請稍後再試');
        setResults([]);
      })
      .finally(() => { if (isLatestSearch()) setLoading(false); });
  };

  // 搜尋頁往左微移（視差），結果頁從右側滑入
  const searchPageStyle = {
    opacity: pageTransition.interpolate({ inputRange: [0, 1], outputRange: [1, 0.6] }),
    transform: [{ translateX: pageTransition.interpolate({ inputRange: [0, 1], outputRange: [0, -screenWidth * 0.3] }) }],
  };
  const resultsPageStyle = {
    transform: [{ translateX: pageTransition.interpolate({ inputRange: [0, 1], outputRange: [screenWidth, 0] }) }],
  };
  const fullScreenStyle = { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: theme.bg };

  return (
    <ThemeCtx.Provider value={theme}>
      <SafeAreaView style={{ flex: 1, backgroundColor: theme.bg }}>
        <StatusBar barStyle={theme.dark ? 'light-content' : 'dark-content'} />
        <View style={{ flex: 1, overflow: 'hidden' }}>
          <Animated.View style={[fullScreenStyle, searchPageStyle]} pointerEvents={page === 'search' ? 'auto' : 'none'}>
            <SearchScreen
              query={query} setQuery={setQuery} category={category} setCategory={setCategory}
              area={area} setArea={setArea} budget={budget} setBudget={setBudget}
              onSearch={runSearch} onToggleTheme={() => setThemeOverride(theme.dark ? 'light' : 'dark')} toast={showToast}
            />
          </Animated.View>

          <Animated.View style={[fullScreenStyle, resultsPageStyle]} pointerEvents={page === 'results' ? 'auto' : 'none'}>
            <ResultsScreen
              key={searchId}
              query={submittedQuery} loading={loading} res={results}
              onBack={() => navigateTo('search')} onFeedback={openFeedback} toast={showToast}
            />
          </Animated.View>
        </View>

        <FeedbackSheet
          visible={feedbackVisible}
          onClose={() => setFeedbackVisible(false)}
          theme={theme}
          questionId={questionId}
          questionText={submittedQuery}
          aiSummary={feedbackOrg?.why ?? ''}
          onSubmit={submitFeedback}
        />

        <Toast msg={toastMessage} opacity={toastOpacity} bottom={page === 'results' ? 100 : 40} />
      </SafeAreaView>
    </ThemeCtx.Provider>
  );
}
