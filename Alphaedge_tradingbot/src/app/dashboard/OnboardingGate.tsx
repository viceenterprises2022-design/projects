'use client';

import { useState } from 'react';

// Shown to signed-in users awaiting approval. Collects onboarding answers
// (stored against the session email) so the desk operator can approve with
// full context from the Access Control panel — no external forms, no re-keying.

const LEVEL_OPTIONS = [
  { value: 'demo', label: 'Demo — just watching' },
  { value: 'level-1', label: 'Level 1 · $5K lane' },
  { value: 'level-2', label: 'Level 2 · $10K lane' },
  { value: 'level-3', label: 'Level 3 · $25K+ lane' },
  { value: 'undecided', label: 'Not sure yet' },
];
const CAPITAL_OPTIONS = [
  { value: 'under-5k', label: 'Under $5K' },
  { value: '5k-10k', label: '$5K – $10K' },
  { value: '10k-25k', label: '$10K – $25K' },
  { value: '25k-plus', label: '$25K+' },
  { value: 'exploring', label: 'Just exploring' },
];
const EXPERIENCE_OPTIONS = [
  { value: 'new', label: 'New to trading' },
  { value: 'casual', label: 'Casual — trade occasionally' },
  { value: 'active', label: 'Active — trade weekly' },
  { value: 'professional', label: 'Professional / full-time' },
];

const fieldStyle: React.CSSProperties = {
  width: '100%', boxSizing: 'border-box', background: 'rgba(255,255,255,0.04)',
  border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, color: 'var(--ivory)',
  padding: '10px 12px', fontSize: 13, outline: 'none',
};
const labelStyle: React.CSSProperties = {
  display: 'block', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase',
  color: 'var(--ivory-faint)', margin: '14px 0 6px',
};

export default function OnboardingGate({ email, defaultName, existing }: {
  email: string;
  defaultName: string;
  existing: { fullName: string; levelInterest: string; capitalBand: string; experience: string; note: string | null } | null;
}) {
  const [submitted, setSubmitted] = useState(!!existing);
  const [editing, setEditing] = useState(false);
  const [fullName, setFullName] = useState(existing?.fullName || defaultName || '');
  const [levelInterest, setLevelInterest] = useState(existing?.levelInterest || 'undecided');
  const [capitalBand, setCapitalBand] = useState(existing?.capitalBand || 'exploring');
  const [experience, setExperience] = useState(existing?.experience || 'casual');
  const [note, setNote] = useState(existing?.note || '');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const res = await fetch('/api/onboarding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fullName, levelInterest, capitalBand, experience, note }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Submission failed');
      setSubmitted(true); setEditing(false);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  if (submitted && !editing) {
    return (
      <div>
        <div className="f-serif-grad" style={{ fontSize: 21, marginBottom: 10 }}>application received</div>
        <p style={{ margin: '0 0 8px', fontSize: 12.5, lineHeight: 1.7, color: 'var(--ivory-dim)' }}>
          Thanks{fullName ? `, ${fullName.split(' ')[0]}` : ''} — your request is with the desk operator.
          Access is typically granted within a few hours. This page unlocks automatically once approved,
          just sign in again with <b style={{ color: 'var(--azure)' }}>{email}</b>.
        </p>
        <button type="button" className="f-btn" style={{ padding: '8px 18px', fontSize: 10.5, marginTop: 10 }}
          onClick={() => setEditing(true)}>
          EDIT ANSWERS
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={submit} style={{ textAlign: 'left' }}>
      <div className="f-serif-grad" style={{ fontSize: 21, marginBottom: 6, textAlign: 'center' }}>request desk access</div>
      <p style={{ margin: '0 0 4px', fontSize: 12, lineHeight: 1.6, color: 'var(--ivory-dim)', textAlign: 'center' }}>
        Signed in as <b style={{ color: 'var(--azure)' }}>{email}</b>. A few quick questions and the
        desk operator will approve your access.
      </p>

      <label style={labelStyle}>Full name</label>
      <input style={fieldStyle} value={fullName} onChange={e => setFullName(e.target.value)}
        placeholder="Your name" required minLength={2} maxLength={80} />

      <label style={labelStyle}>Which level interests you?</label>
      <select style={fieldStyle} value={levelInterest} onChange={e => setLevelInterest(e.target.value)}>
        {LEVEL_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>

      <label style={labelStyle}>Capital you would consider deploying</label>
      <select style={fieldStyle} value={capitalBand} onChange={e => setCapitalBand(e.target.value)}>
        {CAPITAL_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>

      <label style={labelStyle}>Trading experience</label>
      <select style={fieldStyle} value={experience} onChange={e => setExperience(e.target.value)}>
        {EXPERIENCE_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>

      <label style={labelStyle}>Anything you want to see in the demo? (optional)</label>
      <textarea style={{ ...fieldStyle, minHeight: 64, resize: 'vertical' }} value={note}
        onChange={e => setNote(e.target.value)} maxLength={500} placeholder="Optional" />

      {error && <p style={{ color: 'var(--oxide)', fontSize: 12, margin: '10px 0 0' }}>{error}</p>}

      <button type="submit" className="f-btn primary" disabled={busy}
        style={{ width: '100%', padding: '11px 18px', fontSize: 11, marginTop: 16 }}>
        {busy ? 'SUBMITTING…' : 'SUBMIT REQUEST'}
      </button>
    </form>
  );
}
