/**
 * components/charts/ActivityHeatmap.jsx
 * SVG-based heatmap showing user activity by hour-of-day and day-of-week.
 * Each cell's color intensity reflects activity count.
 */
import { useMemo } from 'react';

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

const formatHour = (h) => {
  if (h === 0) return '12a';
  if (h === 12) return '12p';
  return h < 12 ? `${h}a` : `${h - 12}p`;
};

const riskColor = (count, maxCount) => {
  if (count === 0) return 'rgba(255,255,255,0.03)';
  const intensity = count / maxCount;
  if (intensity < 0.25) return `rgba(99,102,241,${0.15 + intensity * 0.4})`;
  if (intensity < 0.5) return `rgba(245,158,11,${0.3 + intensity * 0.4})`;
  if (intensity < 0.75) return `rgba(249,115,22,${0.5 + intensity * 0.3})`;
  return `rgba(239,68,68,${0.6 + intensity * 0.35})`;
};

export default function ActivityHeatmap({ heatmap = {}, loading = false }) {
  const maxCount = useMemo(() => {
    return Math.max(1, ...Object.values(heatmap).map(v => v.count || 0));
  }, [heatmap]);

  const getCell = (day, hour) => {
    const key = `${day}-${hour}`;
    return heatmap[key] || { count: 0, risk_sum: 0 };
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 160 }}>
        <div className="spinner" style={{ width: 24, height: 24 }} />
      </div>
    );
  }

  const cellSize = 16;
  const cellGap = 2;
  const colWidth = cellSize + cellGap;

  return (
    <div style={{ overflowX: 'auto' }}>
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', minWidth: 'max-content' }}>
        {/* Day labels */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: cellGap, paddingTop: 18 }}>
          {DAYS.map(d => (
            <div key={d} style={{
              height: cellSize, lineHeight: `${cellSize}px`,
              fontSize: 10, color: '#475569', fontWeight: 600,
              width: 28, textAlign: 'right', paddingRight: 6,
            }}>
              {d}
            </div>
          ))}
        </div>

        {/* Hours + cells */}
        <div>
          {/* Hour labels */}
          <div style={{ display: 'flex', gap: cellGap, marginBottom: 4 }}>
            {HOURS.map(h => (
              <div key={h} style={{
                width: cellSize, fontSize: 7, color: '#334155',
                textAlign: 'center', fontWeight: 600,
                // Only show every 4 hours
                opacity: h % 4 === 0 ? 1 : 0,
              }}>
                {formatHour(h)}
              </div>
            ))}
          </div>

          {/* Cells grid */}
          {DAYS.map((_, dayIdx) => (
            <div key={dayIdx} style={{ display: 'flex', gap: cellGap, marginBottom: cellGap }}>
              {HOURS.map(hour => {
                const cell = getCell(dayIdx, hour);
                const isAfterHours = hour < 7 || hour >= 21;
                const bg = riskColor(cell.count, maxCount);
                return (
                  <div
                    key={hour}
                    title={`${DAYS[dayIdx]} ${formatHour(hour)}: ${cell.count} events, risk +${cell.risk_sum.toFixed(0)}`}
                    style={{
                      width: cellSize,
                      height: cellSize,
                      borderRadius: 2,
                      background: bg,
                      border: isAfterHours && cell.count > 0
                        ? '1px solid rgba(239,68,68,0.4)'
                        : '1px solid rgba(255,255,255,0.03)',
                      cursor: cell.count > 0 ? 'pointer' : 'default',
                      transition: 'transform 0.1s, border-color 0.2s',
                      boxSizing: 'border-box',
                    }}
                    onMouseEnter={e => { if (cell.count > 0) e.currentTarget.style.transform = 'scale(1.3)'; }}
                    onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; }}
                  />
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 10 }}>
        <span style={{ fontSize: 10, color: '#475569' }}>Low</span>
        {[0, 0.25, 0.5, 0.75, 1].map((v, i) => (
          <div key={i} style={{
            width: 14, height: 14, borderRadius: 2,
            background: riskColor(v * maxCount, maxCount),
            border: '1px solid rgba(255,255,255,0.06)',
          }} />
        ))}
        <span style={{ fontSize: 10, color: '#475569' }}>High</span>
        <span style={{ fontSize: 10, color: '#ef4444', marginLeft: 12 }}>
          ■ After-hours boundary
        </span>
      </div>
    </div>
  );
}
