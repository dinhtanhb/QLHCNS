// Lucian UX/UI Prompt #040 · MIT License (c) 2026 Seokwoooo · https://lucianlabs.dev/uxui-prompt/#040
import { useEffect, useMemo, useRef, useState } from 'react';
import { AccessibilityInfo, Animated, Easing, Modal, Platform, Pressable, ScrollView, StyleSheet, Text, useWindowDimensions, View } from 'react-native';
import Ionicons from '@expo/vector-icons/Ionicons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { normalizeSearch } from './input-utils';
import { motion, radius, space, type } from './tokens';
import { useTheme } from './theme';
import { Field } from './ui';
import type { WorkspaceLink } from './workspace-types';

/** Overlay navigation shares the server's links; opening it never reloads the form beneath. */
export function NavigationDrawer({ open, items, currentPath, onClose, onNavigate }: {
  open: boolean; items: WorkspaceLink[]; currentPath?: string; onClose: () => void; onNavigate: (link: WorkspaceLink) => void;
}) {
  const t = useTheme(); const insets = useSafeAreaInsets(); const { width } = useWindowDimensions();
  const panelWidth = Math.min(360, width - space.x8 - space.x4);
  const [mounted, setMounted] = useState(open); const [reduced, setReduced] = useState(true);
  const [query, setQuery] = useState(''); const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [progress] = useState(() => new Animated.Value(0)); const closeRef = useRef<React.ElementRef<typeof View>>(null);
  useEffect(() => {
    let alive = true; let changed = false;
    void AccessibilityInfo.isReduceMotionEnabled().then(value => { if (alive && !changed) setReduced(value); }).catch(() => { /* Keep motion off if the preference is unavailable. */ });
    const listener = AccessibilityInfo.addEventListener('reduceMotionChanged', value => { changed = true; setReduced(value); });
    return () => { alive = false; listener.remove(); };
  }, []);
  useEffect(() => {
    const animation = Animated.timing(progress, { toValue: open ? 1 : 0, duration: reduced ? 0 : motion.panel,
      easing: Easing.out(Easing.cubic), useNativeDriver: Platform.OS !== 'web' });
    animation.start(({ finished }) => { if (finished && !open) { setMounted(false); setQuery(''); } });
    return () => animation.stop();
  }, [open, progress, reduced]);
  const groups = useMemo(() => {
    const filtered = items.filter(link => normalizeSearch(`${link.group || 'Nghiệp vụ'} ${link.label}`).includes(normalizeSearch(query)));
    return [...new Set(filtered.map(link => link.group || 'Nghiệp vụ'))].map(name => ({ name, links: filtered.filter(link => (link.group || 'Nghiệp vụ') === name) }));
  }, [items, query]);
  // Mount on an opening prop change; retain the modal until its exit animation completes.
  if (open && !mounted) setMounted(true);
  return <Modal visible={mounted} transparent animationType="none" onRequestClose={onClose}
    onShow={() => closeRef.current?.focus()} statusBarTranslucent navigationBarTranslucent>
    <View style={styles.fill}>
      <Animated.View style={[StyleSheet.absoluteFill, { backgroundColor: t.overlay, opacity: progress }]}>
        <Pressable style={styles.fill} onPress={onClose} accessible={false} focusable={false} />
      </Animated.View>
      <Animated.View accessibilityViewIsModal style={[styles.panel, { width: panelWidth, backgroundColor: t.surface,
        paddingTop: Math.max(insets.top, space.x4), paddingBottom: Math.max(insets.bottom, space.x4),
        transform: [{ translateX: progress.interpolate({ inputRange: [0, 1], outputRange: [-panelWidth, 0] }) }] }]}>
        <View style={styles.header}>
          <Text accessibilityRole="header" style={[styles.title, { color: t.text }]}>Danh mục nghiệp vụ</Text>
          <Pressable ref={closeRef} accessibilityRole="button" accessibilityLabel="Đóng danh mục" onPress={onClose}
            style={[styles.close, { borderColor: t.border }]}><Ionicons name="close-outline" size={24} color={t.text} /></Pressable>
        </View>
        <View style={styles.search}><Field label="Tìm trong danh mục" value={query} onChangeText={setQuery} autoCapitalize="none" /></View>
        <ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={styles.list}>
          {groups.map((group, index) => {
            const activeGroup = group.links.some(link => link.path === currentPath);
            const isExpanded = !!query.trim() || (expanded[group.name] ?? (activeGroup || index === 0));
            return <View key={group.name}>
              <Pressable accessibilityRole="button" accessibilityLabel={group.name} aria-expanded={isExpanded}
                onPress={() => setExpanded(value => ({ ...value, [group.name]: !isExpanded }))}
                style={[styles.row, { borderColor: t.cardBorder }]}>
                <Ionicons name="grid-outline" size={22} color={activeGroup ? t.brand : t.muted} />
                <Text style={[styles.label, { color: t.text, fontWeight: '600' }]}>{group.name}</Text>
                <Ionicons name={isExpanded ? 'chevron-up-outline' : 'chevron-down-outline'} size={20} color={t.muted} />
              </Pressable>
              {isExpanded ? group.links.map((link, i) => <Pressable key={`${link.path}-${i}`} accessibilityRole="button"
                accessibilityLabel={link.label} accessibilityState={{ selected: link.path === currentPath }}
                {...(Platform.OS === 'web' ? { 'aria-current': link.path === currentPath ? 'page' : undefined } : {})}
                onPress={() => { onClose(); onNavigate(link); }}
                style={[styles.link, { backgroundColor: link.path === currentPath ? t.bg : t.surface,
                  borderLeftColor: link.path === currentPath ? t.brand : t.cardBorder }]}>
                <Text style={[styles.label, { color: link.path === currentPath ? t.brand : t.text }]}>{link.label}</Text>
                <Ionicons name={link.external ? 'open-outline' : 'chevron-forward-outline'} size={18} color={t.muted} />
              </Pressable>) : null}
            </View>;
          })}
          {!groups.length ? <Text style={[styles.label, { color: t.muted }]}>Không tìm thấy nghiệp vụ. Thử từ khóa khác.</Text> : null}
        </ScrollView>
      </Animated.View>
    </View>
  </Modal>;
}

const styles = StyleSheet.create({
  fill: { flex: 1 }, panel: { height: '100%', gap: space.x3 },
  header: { flexDirection: 'row', alignItems: 'center', gap: space.x2, paddingHorizontal: space.x4 },
  title: { flex: 1, minWidth: 0, fontSize: type.title, lineHeight: 26, fontWeight: '600' },
  close: { minWidth: 48, minHeight: 48, borderWidth: 1, borderRadius: radius.control, alignItems: 'center', justifyContent: 'center' },
  search: { paddingHorizontal: space.x4 }, list: { padding: space.x4, gap: space.x2 },
  row: { flexDirection: 'row', gap: space.x3, alignItems: 'center', minHeight: 48, paddingVertical: space.x3, borderBottomWidth: 1 },
  link: { flexDirection: 'row', gap: space.x2, alignItems: 'center', minHeight: 48, marginLeft: space.x2, borderLeftWidth: 3, padding: space.x3 },
  label: { flexShrink: 1, flexGrow: 1, fontSize: type.body, lineHeight: 24 },
});
