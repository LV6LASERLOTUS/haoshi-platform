// FeedbackSheet.js — 好事大平台「回饋修正」底部面板（React Native / Expo）
// 依賴：react-native-svg（App.js 已安裝）
//
// 用法：
//   <FeedbackSheet
//     visible={open}
//     onClose={() => setOpen(false)}
//     theme={c}                       // App.js 的 LIGHT / DARK 色票物件
//     questionId="Q-20261113-0042"    // 問題ID
//     questionText={query}            // 問題文字
//     aiSummary={o.why}               // Ai內容
//     onSubmit={async (payload) => { await fetch(...); }}
//   />

import React, { useEffect, useRef, useState } from 'react';
import {
  Modal, View, Text, TextInput, Pressable, ScrollView, Animated,
  KeyboardAvoidingView, Keyboard, Platform, ActivityIndicator,
} from 'react-native';
import Svg, { Path } from 'react-native-svg';

const TYPES = [
  { v: '推薦符合需求', e: '👍' },
  { v: '推薦與需求不符', e: '👎' },
  { v: '組織資訊有誤', e: '⚠️' },
  { v: '缺少關鍵資訊', e: '🔍' },
  { v: '推薦理由不充分', e: '💭' },
  { v: '資料已過時', e: '🕒' },
  { v: '其他建議', e: '💡' },
];
const HINT = {
  推薦符合需求: '哪裡讓你覺得很合適？（選填）',
  推薦與需求不符: '哪裡跟你的需求不一樣？例如地區、預算、領域…（選填）',
  組織資訊有誤: '哪一項資訊不正確？正確的內容是什麼？（選填）',
  缺少關鍵資訊: '你還想知道這個組織的哪些資訊？（選填）',
  推薦理由不充分: 'AI 的說明哪裡不夠清楚或不夠有說服力？（選填）',
  資料已過時: '哪些資料已經改變了？（選填）',
  其他建議: '請告訴我們你的想法',
};
const RATE_LABEL = ['', '很不滿意', '不太滿意', '普通', '不錯', '非常滿意'];
const OTHER = '其他建議';
const DD_MAX_HEIGHT = 220; // 下拉選單最大高度，超過時可捲動

/* 卡通風硬陰影（Android 也能顯示實色偏移陰影） */
function Pop({ c, r = 16, off = 3, bw = 2.5, bg, pressed, style, children }) {
  return (
    <View style={[{ paddingRight: off, paddingBottom: off }, style]}>
      {!pressed && <View style={{ position: 'absolute', top: off, left: off, right: 0, bottom: 0, borderRadius: r, backgroundColor: c.ol }} />}
      <View style={{
        backgroundColor: bg || c.surface, borderColor: c.ol, borderWidth: bw, borderRadius: r,
        transform: pressed ? [{ translateX: off }, { translateY: off }] : [],
      }}>{children}</View>
    </View>
  );
}

/* 欄位外框：錯誤時抖動 + 顯示錯誤訊息 */
function Field({ c, label, required, optionalTag, bad, shake, error, style, children }) {
  const [x] = useState(() => new Animated.Value(0));
  useEffect(() => {
    if (!shake) return;
    Animated.sequence([-4, 4, -4, 0].map((v) => Animated.timing(x, { toValue: v, duration: 60, useNativeDriver: true }))).start();
  }, [shake, x]);
  return (
    <View style={[{ marginBottom: 16 }, style]}>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', gap: 6, marginBottom: 8 }}>
        <Text style={{ color: c.ink, fontWeight: '700', fontSize: 16 }}>{label}</Text>
        {required && <Text style={{ color: c.accent, fontWeight: '700' }}>*</Text>}
        {optionalTag && <Text style={{ color: optionalTag === '必填' ? c.accent : c.muted, fontSize: 12 }}>{optionalTag}</Text>}
      </View>
      <Animated.View style={{ transform: [{ translateX: x }] }}>{children}</Animated.View>
      {bad && <Text style={{ color: c.accent, fontSize: 13, fontWeight: '600', marginTop: 6 }}>{error}</Text>}
    </View>
  );
}

function Star({ on, c, onPress, n }) {
  return (
    <Pressable onPress={onPress} hitSlop={4} accessibilityRole="radio" accessibilityState={{ selected: on }} accessibilityLabel={`${n} 顆星`}>
      <Svg width={42} height={42} viewBox="0 0 24 24">
        <Path d="M12 2.8l2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2 6.3 20.3l1.2-6.4L2.8 9.5l6.4-.8z"
          fill={on ? c.yellow : c.surface} stroke={c.ol} strokeWidth={1.8} strokeLinejoin="round" />
      </Svg>
    </Pressable>
  );
}

export default function FeedbackSheet({
  visible, onClose, theme: c, questionId, questionText, aiSummary, onSubmit,
  showDevPreview = typeof __DEV__ !== 'undefined' && __DEV__,
}) {
  const [rate, setRate] = useState(0);
  const [type, setType] = useState('');
  const [text, setText] = useState('');
  const [ddOpen, setDdOpen] = useState(false);
  const [aiOpen, setAiOpen] = useState(false);
  const [bad, setBad] = useState({});
  const [shakeN, setShakeN] = useState(0);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null); // 送出後的 payload
  const [err, setErr] = useState('');
  const [focus, setFocus] = useState(false);
  const scroll = useRef(null);

  // 鍵盤彈出且輸入框聚焦時，自動捲動到底部避免被鍵盤遮住
  useEffect(() => {
    if (!focus) return;
    const evt = Platform.OS === 'ios' ? 'keyboardWillShow' : 'keyboardDidShow';
    const sub = Keyboard.addListener(evt, () => {
      setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 80);
    });
    return () => sub.remove();
  }, [focus]);

  // 每次開啟都重置（在 render 期間依 visible 變化調整 state，避免 effect 內 setState）
  const [prevVisible, setPrevVisible] = useState(visible);
  if (visible !== prevVisible) {
    setPrevVisible(visible);
    if (visible) {
      setRate(0); setType(''); setText(''); setDdOpen(false); setAiOpen(false);
      setBad({}); setBusy(false); setDone(null); setErr(''); setFocus(false);
    }
  }

  const needText = type === OTHER;
  const ready = rate > 0 && !!type && (!needText || !!text.trim());

  const submit = async () => {
    const b = { rate: !rate, type: !type, text: needText && !text.trim() };
    setBad(b);
    if (b.rate || b.type || b.text) { setShakeN((n) => n + 1); scroll.current?.scrollTo({ y: 180, animated: true }); return; }
    const payload = {
      question_id: questionId,
      question_text: questionText,
      ai_summary: aiSummary,
      rating: rate,
      feedback_type: type,
      feedback_content: text.trim(),
    };
    try {
      setBusy(true); setErr('');
      await onSubmit?.(payload);
      setDone(payload);
    } catch {
      setErr('送出失敗，請稍後再試一次');
    } finally {
      setBusy(false);
    }
  };

  const sel = TYPES.find((t) => t.v === type);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={{ flex: 1, justifyContent: 'flex-end', alignItems: 'center' }}>
        <Pressable onPress={onClose} style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: 'rgba(10,20,30,.55)' }} accessibilityLabel="關閉" />
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : 'height'} style={{ width: '100%', maxWidth: 560, maxHeight: '94%' }}>
          <View style={{ backgroundColor: c.bg, borderColor: c.ol, borderWidth: 2.5, borderBottomWidth: 0, borderTopLeftRadius: 26, borderTopRightRadius: 26, maxHeight: '100%' }}>
            <View style={{ alignSelf: 'center', width: 44, height: 5, borderRadius: 5, backgroundColor: c.line, marginTop: 8 }} />

            {/* Header（固定在上方） */}
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 16, paddingTop: 12, paddingBottom: 12 }}>
              <View style={{ width: 46, height: 46, borderRadius: 23, backgroundColor: c.yellow, borderColor: c.ol, borderWidth: 2.5, alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ fontSize: 22 }}>💬</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={{ color: c.ink, fontSize: 20, fontWeight: '800' }}>回饋修正</Text>
                <Text style={{ color: c.muted, fontSize: 13 }}>你的意見會幫助 AI 推薦得更準確</Text>
              </View>
              <Pressable onPress={onClose} accessibilityLabel="關閉" style={{ width: 36, height: 36, borderRadius: 18, borderWidth: 2, borderColor: c.ol, backgroundColor: c.surface, alignItems: 'center', justifyContent: 'center' }}>
                <Text style={{ color: c.ink, fontSize: 16 }}>✕</Text>
              </Pressable>
            </View>

            <ScrollView ref={scroll} keyboardShouldPersistTaps="handled" contentContainerStyle={{ paddingHorizontal: 16, paddingBottom: 32 }}>
              {done ? (
                /* ───── 成功畫面 ───── */
                <View style={{ alignItems: 'center', paddingTop: 20 }}>
                  <View style={{ width: 84, height: 84, borderRadius: 42, backgroundColor: c.accentSoft, borderColor: c.ol, borderWidth: 2.5, alignItems: 'center', justifyContent: 'center', marginBottom: 12 }}>
                    <Text style={{ fontSize: 40 }}>💛</Text>
                  </View>
                  <Text style={{ color: c.ink, fontSize: 20, fontWeight: '800' }}>謝謝你的回饋！</Text>
                  <Text style={{ color: c.muted, marginTop: 4, marginBottom: 16 }}>我們會用它來讓下一次推薦更貼心。</Text>
                  {showDevPreview && (
                    <View style={{ alignSelf: 'stretch', borderWidth: 2, borderStyle: 'dashed', borderColor: c.muted, borderRadius: 12, padding: 10, marginBottom: 16 }}>
                      <Text style={{ color: c.muted, fontSize: 12, marginBottom: 4 }}>送出內容預覽（僅開發模式顯示）</Text>
                      <Text style={{ color: c.ink, fontSize: 12 }}>{JSON.stringify(done, null, 2)}</Text>
                    </View>
                  )}
                  <Pressable onPress={onClose} style={{ alignSelf: 'stretch' }}>
                    {({ pressed }) => (
                      <Pop c={c} r={16} pressed={pressed} bg={c.primary}>
                        <Text style={{ color: c.primaryInk, fontWeight: '800', fontSize: 16, textAlign: 'center', padding: 13 }}>完成</Text>
                      </Pop>
                    )}
                  </Pressable>
                </View>
              ) : (
                <>
                  {/* ───── 自動帶入的資料（唯讀） ───── */}
                  <Pop c={c} r={20} style={{ marginBottom: 16 }}>
                    <View style={{ padding: 14 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                        <Text style={{ color: c.muted, fontSize: 13, fontWeight: '700' }}>📋 這筆推薦的資料</Text>
                        <Text style={{ marginLeft: 'auto', fontSize: 11, color: c.primary, backgroundColor: c.primarySoft, borderRadius: 999, paddingHorizontal: 8, overflow: 'hidden' }}>自動帶入・不可編輯</Text>
                      </View>

                      <Text style={{ color: c.muted, fontSize: 12, fontWeight: '700', marginBottom: 2 }}>問題 ID</Text>
                      <Text selectable style={{ alignSelf: 'flex-start', fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace', fontWeight: '600', fontSize: 13, color: c.primary, backgroundColor: c.primarySoft, borderColor: c.primary, borderWidth: 1.5, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 4, overflow: 'hidden', marginBottom: 12 }}>{questionId}</Text>

                      <Text style={{ color: c.muted, fontSize: 12, fontWeight: '700', marginBottom: 2 }}>問題文字</Text>
                      <View style={{ borderLeftWidth: 4, borderLeftColor: c.yellow, paddingLeft: 10, marginBottom: 12 }}>
                        <Text style={{ color: c.ink, fontSize: 15, lineHeight: 22 }}>{questionText}</Text>
                      </View>

                      <Text style={{ color: c.muted, fontSize: 12, fontWeight: '700', marginBottom: 2 }}>AI 內容</Text>
                      <View style={{ borderWidth: 2, borderStyle: 'dashed', borderColor: c.muted, borderRadius: 14, padding: 10 }}>
                        <Text numberOfLines={aiOpen ? undefined : 2} style={{ color: c.ink, fontSize: 14, lineHeight: 21 }}>{aiSummary}</Text>
                      </View>
                      <Pressable onPress={() => setAiOpen(!aiOpen)} style={{ paddingTop: 6 }}>
                        <Text style={{ color: c.primary, fontSize: 13, fontWeight: '600' }}>{aiOpen ? '收合 ▴' : '展開全文 ▾'}</Text>
                      </Pressable>
                    </View>
                  </Pop>

                  {/* ───── 評級 ───── */}
                  <Field c={c} label="評級" required bad={bad.rate} shake={bad.rate ? shakeN : 0} error="請先給個評分">
                    <View accessibilityRole="radiogroup" style={{ flexDirection: 'row', gap: 6 }}>
                      {[1, 2, 3, 4, 5].map((n) => (
                        <Star key={n} n={n} c={c} on={n <= rate} onPress={() => { setRate(n); setBad((b) => ({ ...b, rate: false })); }} />
                      ))}
                    </View>
                    <Text style={{ color: c.muted, fontWeight: '600', fontSize: 14, marginTop: 6, minHeight: 22 }}>
                      {rate ? `${rate} 分・${RATE_LABEL[rate]}` : '點星星為這筆推薦評分'}
                    </Text>
                  </Field>

                  {/* ───── 回饋類型（下拉選單） ───── */}
                  <Field c={c} label="回饋類型" required bad={bad.type} shake={bad.type ? shakeN : 0} error="請選擇一個回饋類型" style={{ zIndex: ddOpen ? 10 : 0 }}>
                    <View>
                      <Pressable onPress={() => setDdOpen(!ddOpen)} accessibilityRole="button" accessibilityState={{ expanded: ddOpen }}>
                        {({ pressed }) => (
                          <Pop c={c} r={14} off={2} pressed={pressed}>
                            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 11, paddingHorizontal: 14, borderRadius: 12, backgroundColor: bad.type ? c.accentSoft : c.surface }}>
                              <Text style={{ flex: 1, color: sel ? c.ink : c.muted, fontSize: 16 }}>{sel ? `${sel.e}  ${sel.v}` : '請選擇回饋類型'}</Text>
                              <Text style={{ color: c.ink }}>{ddOpen ? '▴' : '▾'}</Text>
                            </View>
                          </Pop>
                        )}
                      </Pressable>
                      {/* 浮在下方欄位之上、可捲動，不會把「回饋內容」往下推 */}
                      {ddOpen && (
                        <Pop c={c} r={16} style={{ position: 'absolute', top: '100%', left: 0, right: 0, marginTop: 8, zIndex: 10, elevation: 10 }}>
                          <ScrollView style={{ maxHeight: DD_MAX_HEIGHT }} contentContainerStyle={{ padding: 6 }} nestedScrollEnabled keyboardShouldPersistTaps="handled" persistentScrollbar>
                            {TYPES.map((t, i) => {
                              const on = t.v === type;
                              return (
                                <View key={t.v}>
                                  {i === TYPES.length - 1 && <View style={{ borderTopWidth: 2, borderStyle: 'dashed', borderColor: c.line, marginVertical: 4, marginHorizontal: 6 }} />}
                                  <Pressable
                                    onPress={() => { setType(t.v); setDdOpen(false); setBad((b) => ({ ...b, type: false, text: false })); }}
                                    accessibilityRole="menuitem" accessibilityState={{ selected: on }}
                                    style={{ flexDirection: 'row', alignItems: 'center', gap: 10, padding: 10, borderRadius: 10, backgroundColor: on ? c.yellow : 'transparent' }}
                                  >
                                    <Text style={{ fontSize: 18, width: 26, textAlign: 'center' }}>{t.e}</Text>
                                    <Text style={{ color: on ? '#25303b' : c.ink, fontWeight: on ? '700' : '400', fontSize: 15 }}>{t.v}</Text>
                                  </Pressable>
                                </View>
                              );
                            })}
                          </ScrollView>
                        </Pop>
                      )}
                    </View>
                  </Field>

                  {/* ───── 回饋內容 ───── */}
                  <Field c={c} label="回饋內容" optionalTag={needText ? '必填' : '選填'} bad={bad.text} shake={bad.text ? shakeN : 0} error="選擇「其他建議」時，請簡單說明你的想法">
                    <TextInput
                      value={text}
                      onChangeText={(v) => { setText(v); if (v.trim()) setBad((b) => ({ ...b, text: false })); }}
                      onFocus={() => {
                        setFocus(true);
                        setDdOpen(false);
                        setTimeout(() => scroll.current?.scrollToEnd({ animated: true }), 150);
                      }}
                      onBlur={() => setFocus(false)}
                      onContentSizeChange={() => {
                        if (focus) scroll.current?.scrollToEnd({ animated: true });
                      }}
                      multiline maxLength={500}
                      placeholder={type ? HINT[type] : '還有什麼想告訴我們的嗎？'}
                      placeholderTextColor={c.muted}
                      style={{
                        minHeight: 110, textAlignVertical: 'top', color: c.ink, fontSize: 16, lineHeight: 24,
                        backgroundColor: c.surface, borderRadius: 14, padding: 12, paddingTop: 12,
                        borderWidth: 2.5, borderColor: bad.text ? c.accent : focus ? c.yellow : c.ol,
                      }}
                    />
                    <Text style={{ textAlign: 'right', color: c.muted, fontSize: 12, marginTop: 4 }}>{text.length} / 500</Text>
                  </Field>

                  {/* ───── 送出 ───── */}
                  {!!err && <Text style={{ color: c.accent, fontWeight: '600', textAlign: 'center', marginBottom: 8 }}>{err}</Text>}
                  <Pressable onPress={submit} disabled={busy} accessibilityRole="button" accessibilityState={{ disabled: !ready }}>
                    {({ pressed }) => (
                      <Pop c={c} r={16} pressed={pressed || !ready} bg={ready ? c.primary : c.line}>
                        <View style={{ padding: 13, alignItems: 'center', justifyContent: 'center', minHeight: 50 }}>
                          {busy
                            ? <ActivityIndicator color={c.primaryInk} />
                            : <Text style={{ color: ready ? c.primaryInk : c.muted, fontWeight: '800', fontSize: 16 }}>送出回饋</Text>}
                        </View>
                      </Pop>
                    )}
                  </Pressable>
                  <Text style={{ textAlign: 'center', color: c.muted, fontSize: 12, marginTop: 10 }}>送出後會連同上方的問題與 AI 內容一併記錄</Text>
                </>
              )}
            </ScrollView>
          </View>
        </KeyboardAvoidingView>
      </View>
    </Modal>
  );
}
