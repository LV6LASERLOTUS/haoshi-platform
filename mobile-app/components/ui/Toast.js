import React, { useCallback, useRef, useState } from 'react';
import { Animated, Text } from 'react-native';
import { useT } from '../../theme';

/* Toast hook：回傳 show(msg) 與要渲染的 props */
export function useToast() {
  const [msg, setMsg] = useState('');
  const [opacity] = useState(() => new Animated.Value(0));
  const timer = useRef(null);

  const show = useCallback((m) => {
    setMsg(m);
    Animated.timing(opacity, { toValue: 1, duration: 200, useNativeDriver: true }).start();
    clearTimeout(timer.current);
    timer.current = setTimeout(() => Animated.timing(opacity, { toValue: 0, duration: 200, useNativeDriver: true }).start(), 2200);
  }, [opacity]);

  return { show, msg, opacity };
}

export default function Toast({ msg, opacity, bottom = 40 }) {
  const c = useT();
  return (
    <Animated.View pointerEvents="none" style={{ position: 'absolute', alignSelf: 'center', bottom, opacity, backgroundColor: c.ink, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 8 }}>
      <Text style={{ color: c.bg, fontSize: 14 }}>{msg}</Text>
    </Animated.View>
  );
}
