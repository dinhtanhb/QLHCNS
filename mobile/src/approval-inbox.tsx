import { createContext, PropsWithChildren, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { useSession } from './session';
import type { Leave, Page } from './types';

type ApprovalInbox = { count: number | null; updateCount: (count: number) => void; refreshCount: () => Promise<void> };
const Context = createContext<ApprovalInbox | null>(null);

/** One count for the tab badge and Home. Server permissions remain authoritative. */
export function ApprovalInboxProvider({ children }: PropsWithChildren) {
  const { me, request } = useSession();
  const [count, setCount] = useState<number | null>(null);
  const sequence = useRef(0);
  const updateCount = useCallback((value: number) => { sequence.current += 1; setCount(value); }, []);
  const refreshCount = useCallback(async () => {
    const current = ++sequence.current;
    if (!me?.can_approve) return;
    try {
      const page = await request<Page<Leave>>('approvals/');
      if (current === sequence.current) setCount(page.count);
    } catch { /* Preserve the last known count; the screen reports load failures. */ }
  }, [me?.can_approve, request]);
  useEffect(() => () => { sequence.current += 1; }, []);
  const value = useMemo(() => ({ count, updateCount, refreshCount }), [count, updateCount, refreshCount]);
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useApprovalInbox() {
  const value = useContext(Context);
  if (!value) throw new Error('ApprovalInboxProvider is required');
  return value;
}
