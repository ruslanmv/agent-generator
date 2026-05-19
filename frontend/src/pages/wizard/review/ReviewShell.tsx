// Shared chrome for every Review v2 sub-page: substep tab nav at the
// top, scrollable body in the middle, sticky footer action bar at the
// bottom. One primary action per page lives in the footer.

import type { ReactNode } from 'react';
import { tokens } from '@/styles/tokens';
import { REVIEW_STEPS, useReviewSub } from './state';

interface Props {
  title?: ReactNode;
  subtitle?: ReactNode;
  /** Footer slot. Put the sticky action bar contents here. */
  footer: ReactNode;
  children: ReactNode;
  /** When `true` the substep tab nav is omitted. Used on the final
   * Generate page so the wizard's main stepper is the only navigation
   * visible — avoids the "wizard inside a wizard" feeling. */
  hideTabs?: boolean;
}

export function ReviewShell({ title, subtitle, footer, children, hideTabs = false }: Props) {
  const { active, go } = useReviewSub();
  const activeIndex = REVIEW_STEPS.findIndex((s) => s.id === active);

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: 'calc(100vh - 200px)',
      }}
    >
      {/* Substep nav — sticky just under the wizard's main step strip.
          Hidden on the final Generate sub-page so the wizard stepper
          is the only navigation showing. */}
      {!hideTabs && (
      <div
        role="tablist"
        aria-label="Review sections"
        style={{
          display: 'flex',
          borderBottom: `1px solid ${tokens.border}`,
          background: '#fff',
          padding: '0 40px',
          flexShrink: 0,
          overflowX: 'auto',
          position: 'sticky',
          top: 0,
          zIndex: 4,
        }}
      >
        {REVIEW_STEPS.map((s, i) => {
          const on = s.id === active;
          const done = i < activeIndex;
          return (
            <button
              key={s.id}
              type="button"
              role="tab"
              aria-selected={on}
              onClick={() => go(s.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 8,
                padding: '14px 16px',
                color: on ? tokens.ink : done ? tokens.ink2 : tokens.muted,
                borderTop: 'none',
                borderLeft: 'none',
                borderRight: 'none',
                borderBottom: `2px solid ${on ? tokens.accent : 'transparent'}`,
                marginBottom: -1,
                background: 'transparent',
                cursor: 'pointer',
                fontFamily: 'inherit',
                whiteSpace: 'nowrap',
              }}
            >
              <span
                aria-hidden
                style={{
                  width: 18,
                  height: 18,
                  background: done ? tokens.ok : on ? tokens.ink : '#fff',
                  border: `1px solid ${
                    done ? tokens.ok : on ? tokens.ink : tokens.borderStrong
                  }`,
                  color: done || on ? '#fff' : tokens.muted,
                  fontFamily: tokens.mono,
                  fontSize: 10,
                  fontWeight: 600,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}
              >
                {done ? '✓' : i + 1}
              </span>
              <span style={{ fontSize: 13, fontWeight: on ? 600 : 400 }}>{s.label}</span>
            </button>
          );
        })}
      </div>
      )}

      {/* Body */}
      <div style={{ flex: 1, minHeight: 0 }}>
        <div style={{ padding: '36px 80px 28px', maxWidth: 1120, margin: '0 auto' }}>
          {title && (
            <>
              <h2 className="ag-h2" style={{ marginBottom: 6 }}>
                {title}
              </h2>
              {subtitle && (
                <p
                  className="ag-body"
                  style={{ color: tokens.ink3, marginBottom: 28, maxWidth: 680 }}
                >
                  {subtitle}
                </p>
              )}
            </>
          )}
          {children}
        </div>
      </div>

      {/* Sticky footer action bar */}
      <div
        style={{
          minHeight: 64,
          borderTop: `1px solid ${tokens.border}`,
          background: '#fff',
          display: 'flex',
          alignItems: 'center',
          padding: '12px 40px',
          gap: 12,
          flexShrink: 0,
          flexWrap: 'wrap',
          position: 'sticky',
          bottom: 0,
          zIndex: 4,
        }}
      >
        {footer}
      </div>
    </div>
  );
}
