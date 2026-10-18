import React, { useCallback, useState } from 'react';
import { RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { colors, fontMono, spacing } from '../../theme/tokens';
import { useAuth } from '../../hooks/useAuth';
import { useDevices } from '../../hooks/useDevices';
import { useDeviceLive } from '../../hooks/useDeviceLive';
import { useDeviceControls } from '../../hooks/useDeviceControls';
import { DevicePicker } from '../../components/DevicePicker';
import { ConnectionPill } from '../../components/ConnectionPill';
import { SoilGauge } from '../../components/SoilGauge';
import { StatTile } from '../../components/StatTile';
import { Sparkline } from '../../components/Sparkline';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { askAdvisor } from '../../lib/advisor';
import type { ConnectionState } from '../../lib/types';

const DRY = 40; // same DRY cutoff as the dashboard gauge
const VERY_DRY = 25;
const WET = 85;
const POLL_MIN = 1 / 6; // ESP32 reports every 10s

function timeAgo(ms: number | null): string {
  if (!ms) return '--';
  const diff = Math.max(0, Date.now() - ms);
  if (diff < 5000) return 'Just now';
  if (diff < 60000) return `${Math.floor(diff / 1000)}s ago`;
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  return `${Math.floor(diff / 3600000)}h ago`;
}

interface AdviceInput {
  moisture: number;
  slopePerMin: number; // % per minute, + = getting wetter
  raining: boolean;
  pumpOn: boolean;
  probeOk: boolean;
  cs: ConnectionState;
}
interface Advice {
  title: string;
  body: string;
  color: string;
}

export function soilAdvice(i: AdviceInput): Advice {
  if (i.cs === 'NO_DEVICE' || i.cs === 'OFFLINE')
    return { title: 'Device offline', body: 'No recent data. Check power and Wi-Fi on the node.', color: colors.textMuted };
  if (!i.probeOk)
    return { title: 'Probe not reporting', body: 'Check the soil sensor wiring (GPIO 34).', color: colors.rose };
  if (i.pumpOn)
    return { title: 'Watering in progress', body: 'Let the pump run until it reaches the stop threshold.', color: colors.blue };
  if (i.moisture < DRY && i.raining)
    return { title: 'Dry, but rain detected', body: 'Hold off on watering. Rain should top the soil up.', color: colors.blue };
  if (i.moisture < VERY_DRY)
    return { title: 'Very dry: water now', body: `Moisture is ${Math.round(i.moisture)}%. Plants may be stressed.`, color: colors.rose };
  if (i.moisture < DRY) {
    const mins = i.slopePerMin < -0.01 ? (i.moisture - VERY_DRY) / -i.slopePerMin : null;
    const eta = mins !== null && mins < 600 ? ` At this rate it hits ${VERY_DRY}% in ~${Math.round(mins)} min.` : '';
    return { title: 'Getting dry: water soon', body: `Moisture is ${Math.round(i.moisture)}%.${eta}`, color: colors.amber };
  }
  if (i.moisture > WET)
    return { title: 'Waterlogged: stop watering', body: 'Soil is saturated. Check drainage and skip the next watering.', color: colors.blue };
  return { title: 'Optimal: no action needed', body: `Moisture is ${Math.round(i.moisture)}%, within the healthy range.`, color: colors.green };
}

if (__DEV__) {
  const base: AdviceInput = { moisture: 60, slopePerMin: 0, raining: false, pumpOn: false, probeOk: true, cs: 'LIVE' };
  console.assert(soilAdvice({ ...base, cs: 'OFFLINE' }).title === 'Device offline');
  console.assert(soilAdvice({ ...base, probeOk: false }).title === 'Probe not reporting');
  console.assert(soilAdvice({ ...base, pumpOn: true }).title === 'Watering in progress');
  console.assert(soilAdvice({ ...base, moisture: 30, raining: true }).title === 'Dry, but rain detected');
  console.assert(soilAdvice({ ...base, moisture: 20 }).title === 'Very dry: water now');
  console.assert(soilAdvice({ ...base, moisture: 30 }).title === 'Getting dry: water soon');
  console.assert(soilAdvice({ ...base, moisture: 90 }).title === 'Waterlogged: stop watering');
  console.assert(soilAdvice(base).title === 'Optimal: no action needed');
}

export default function SoilScreen() {
  const { session } = useAuth();
  const { devices, activeDevice, activeDeviceIndex, setActiveDeviceIndex, fetchDevices } = useDevices();
  const deviceId = activeDevice?.id ?? null;
  const live = useDeviceLive(deviceId);
  const controls = useDeviceControls(deviceId);

  const [refreshing, setRefreshing] = useState(false);
  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([fetchDevices(), live.refresh(), controls.refreshControls()]);
    setRefreshing(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchDevices, live.refresh, controls.refreshControls]);

  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [aiLoading, setAiLoading] = useState(false);
  async function askAi() {
    if (!session) return;
    setAiLoading(true);
    try {
      setAiAnswer(
        await askAdvisor(
          'Based on my soil moisture readings, what should I do right now?',
          deviceId,
          [],
          session.access_token
        )
      );
    } catch (err: any) {
      setAiAnswer(err?.message ?? 'Advisor unavailable.');
    } finally {
      setAiLoading(false);
    }
  }

  const cs = live.connectionState;
  const muted = cs === 'OFFLINE' || cs === 'NO_DEVICE';
  const probeOk = !muted && live.presence.sensorFlags.soil !== false;
  const moisture = live.telemetry.soilMoisture;

  const h = live.history.soil;
  const hasStats = probeOk && h.length > 0;
  const min = hasStats ? Math.min(...h) : 0;
  const max = hasStats ? Math.max(...h) : 0;
  const avg = hasStats ? Math.round(h.reduce((a, b) => a + b, 0) / h.length) : 0;
  // % per minute across the whole window (ticks are ~10s apart)
  const slopePerMin = h.length > 1 ? (h[h.length - 1] - h[0]) / ((h.length - 1) * POLL_MIN) : 0;
  const trend = slopePerMin > 0.05 ? 'Rising' : slopePerMin < -0.05 ? 'Drying' : 'Stable';
  const trendColor = trend === 'Rising' ? colors.blue : trend === 'Drying' ? colors.amber : colors.green;

  const advice = soilAdvice({
    moisture,
    slopePerMin,
    raining: live.telemetry.rainDetected,
    pumpOn: controls.pumpState === 'RUNNING',
    probeOk,
    cs,
  });

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={colors.green} />}
      >
        <View style={styles.header}>
          <DevicePicker devices={devices} activeIndex={activeDeviceIndex} onSelect={setActiveDeviceIndex} />
          <ConnectionPill state={cs} />
        </View>

        <View style={styles.gaugeWrap}>
          <SoilGauge
            size={220}
            value={probeOk ? moisture : 0}
            muted={!probeOk}
            stateLabel={muted ? 'NO DATA' : !probeOk ? 'NO PROBE' : moisture < DRY ? 'DRY' : moisture > WET ? 'WET' : 'OPTIMAL'}
          />
        </View>

        <Text style={styles.sectionTitle}>WHAT TO DO</Text>
        <Card style={[styles.adviceCard, { borderColor: advice.color }]}>
          <Text style={[styles.adviceTitle, { color: advice.color }]}>{advice.title}</Text>
          <Text style={styles.adviceBody}>{advice.body}</Text>
          <Button label="ASK ADVISOR FOR MORE" variant="secondary" onPress={askAi} loading={aiLoading} disabled={!deviceId} />
          {aiAnswer ? <Text style={styles.aiAnswer}>{aiAnswer}</Text> : null}
        </Card>

        <Text style={styles.sectionTitle}>MOISTURE HISTORY</Text>
        <Card style={styles.block}>
          <Sparkline label="Soil Moisture" values={h} color={colors.green} unit="%" min={0} max={100} height={160} />
        </Card>

        <Text style={styles.sectionTitle}>STATS (LAST {h.length} READINGS)</Text>
        <View style={styles.statRow}>
          <StatTile label="Min" value={hasStats ? `${min}` : '--'} unit="%" />
          <StatTile label="Avg" value={hasStats ? `${avg}` : '--'} unit="%" />
          <StatTile label="Max" value={hasStats ? `${max}` : '--'} unit="%" />
        </View>
        <View style={styles.statRow}>
          <StatTile
            label="Trend"
            value={hasStats ? trend : '--'}
            color={hasStats ? trendColor : colors.textMuted}
            subtitle={hasStats ? `${slopePerMin >= 0 ? '+' : ''}${slopePerMin.toFixed(2)} %/min` : undefined}
          />
        </View>

        <Text style={styles.sectionTitle}>DETAILS</Text>
        <Card>
          <Row label="Last reading" value={timeAgo(live.telemetry.lastDataMs)} />
          <Row
            label="Soil probe"
            value={live.presence.sensorFlags.soil === false ? 'FAIL' : deviceId ? 'OK' : '--'}
            color={live.presence.sensorFlags.soil === false ? colors.rose : colors.green}
          />
          <Row label="Rain" value={muted ? '--' : live.telemetry.rainDetected ? 'Detected' : 'Clear'} />
          <Row label="Pump" value={controls.pumpState} />
          <Row label="Automation" value={controls.automationMode} />
          <Row
            label="Start / stop at"
            value={`${controls.thresholds.startThreshold}% / ${controls.thresholds.stopThreshold}%`}
          />
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
}

function Row({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <View style={styles.row}>
      <Text style={styles.rowLabel}>{label}</Text>
      <Text style={[styles.rowValue, color ? { color } : null]}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bgMain },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xxl * 2 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.lg },
  gaugeWrap: { alignItems: 'center', marginBottom: spacing.lg },
  sectionTitle: {
    color: colors.textSecondary,
    fontSize: 12,
    fontFamily: fontMono,
    letterSpacing: 1,
    marginBottom: spacing.sm,
    marginTop: spacing.sm,
  },
  adviceCard: { borderWidth: 1, marginBottom: spacing.lg, gap: spacing.sm },
  adviceTitle: { fontSize: 18, fontWeight: '700' },
  adviceBody: { color: colors.textSecondary, fontSize: 13 },
  aiAnswer: { color: colors.textPrimary, fontSize: 13, marginTop: spacing.sm },
  block: { marginBottom: spacing.lg },
  statRow: { flexDirection: 'row', gap: spacing.md, marginBottom: spacing.md },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderMuted,
  },
  rowLabel: { color: colors.textSecondary, fontSize: 12 },
  rowValue: { color: colors.textPrimary, fontSize: 12, fontFamily: fontMono, fontWeight: '700' },
});
