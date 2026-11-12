import React, { useEffect, useState } from 'react';
import { Animated } from 'react-native';
import { useT } from '../../theme';

export default function Skeleton() {
  const c = useT();
  const [v] = useState(() => new Animated.Value(0.4));
  useEffect(() => {
    const a = Animated.loop(Animated.sequence([
      Animated.timing(v, { toValue: 1, duration: 600, useNativeDriver: true }),
      Animated.timing(v, { toValue: 0.4, duration: 600, useNativeDriver: true }),
    ]));
    a.start();
    return () => a.stop();
  }, [v]);
  return <Animated.View style={{ opacity: v, height: 150, borderRadius: 22, backgroundColor: c.line, marginBottom: 12 }} />;
}
