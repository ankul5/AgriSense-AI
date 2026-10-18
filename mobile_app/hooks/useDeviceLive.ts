import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { supabase } from '../lib/supabase';
import { computeConnectionState } from '../lib/connection';
import type {
  ConnectionState,
  DeviceStatusRow,
  History,
  Presence,
  TelemetryRow,
  TelemetrySnapshot,
} from '../lib/types';

const HISTORY_LENGTH = 40;

const emptyPresence: Presence = {
  lastSeenMs: null,
  sensorsOk: false,
  sensorFlags: {},
  firmwareVersion: null,
  ipAddress: null,
  rssi: null,
};

const emptyTelemetry: TelemetrySnapshot = {
  hasData: false,
  lastDataMs: null,
  soilMoisture: 0,
  temperature: 0,
  humidity: 0,
  soilTemp: 0,
  rainDetected: false,
};

const emptyHistory: History = { soil: [], temp: [], humid: [] };

function applyStatusRow(row: DeviceStatusRow): Presence {
  return {
    lastSeenMs: row.last_seen_at ? new Date(row.last_seen_at).getTime() : Date.now(),
    sensorsOk: !!row.sensors_ok,
    sensorFlags: row.sensor_flags || {},
    firmwareVersion: row.firmware_version ?? null,
    ipAddress: row.ip_address ?? null,
    rssi: row.rssi ?? null,
  };
}

function telemetryFromRow(row: TelemetryRow): TelemetrySnapshot {
  return {
    hasData: true,
    lastDataMs: Date.now(),
    soilMoisture: row.soil_moisture ?? 0,
    temperature: row.temperature ?? 0,
    humidity: row.humidity ?? 0,
    soilTemp: row.soil_temp ?? 0,
    rainDetected: !!row.rain_detected,
  };
}

export function useDeviceLive(deviceId: string | null) {
  // Dashboard and Soil tabs both mount this hook; supabase-js returns the
  // existing channel for a repeated topic, so each instance needs its own name.
  const uid = useId();
  const [presence, setPresence] = useState<Presence>(emptyPresence);
  const [telemetry, setTelemetry] = useState<TelemetrySnapshot>(emptyTelemetry);
  const [history, setHistory] = useState<History>(emptyHistory);
  const [loading, setLoading] = useState(false);
  const [tick, setTick] = useState(0); // forces a re-render every 5s so OFFLINE is caught

  const channelsRef = useRef<{ telemetry?: any; status?: any }>({});

  // `silent` skips the loading flag so the background poll below doesn't
  // flicker the UI on every refetch.
  const seed = useCallback(async (id: string, silent = false) => {
    if (!silent) setLoading(true);

    const [{ data: statusRow }, { data: latestRow }, { data: historyRows }] = await Promise.all([
      supabase
        .from('device_status')
        .select('*')
        .eq('device_id', id)
        .maybeSingle(),
      supabase
        .from('telemetry_data')
        .select('*')
        .eq('device_id', id)
        .order('created_at', { ascending: false })
        .limit(1)
        .maybeSingle(),
      supabase
        .from('telemetry_data')
        .select('*')
        .eq('device_id', id)
        .order('created_at', { ascending: false })
        .limit(HISTORY_LENGTH),
    ]);

    if (statusRow) setPresence(applyStatusRow(statusRow as DeviceStatusRow));
    if (latestRow) setTelemetry(telemetryFromRow(latestRow as TelemetryRow));

    const chronological = ((historyRows as TelemetryRow[]) ?? []).slice().reverse();
    setHistory({
      soil: chronological.map((r) => Math.round(r.soil_moisture ?? 0)),
      temp: chronological.map((r) => Number((r.temperature ?? 0).toFixed(1))),
      humid: chronological.map((r) => Math.round(r.humidity ?? 0)),
    });

    if (!silent) setLoading(false);
  }, []);

  useEffect(() => {
    // Reset — we don't know the new device's live state until the one-shot
    // fetch below returns, or a heartbeat/telemetry event arrives.
    setPresence(emptyPresence);
    setTelemetry(emptyTelemetry);
    setHistory(emptyHistory);

    if (channelsRef.current.telemetry) supabase.removeChannel(channelsRef.current.telemetry);
    if (channelsRef.current.status) supabase.removeChannel(channelsRef.current.status);
    channelsRef.current = {};

    if (!deviceId) return;

    seed(deviceId);

    channelsRef.current.telemetry = supabase
      .channel(`telemetry-${deviceId}-${uid}`)
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'telemetry_data', filter: `device_id=eq.${deviceId}` },
        (payload) => {
          const row = payload.new as TelemetryRow;
          setTelemetry(telemetryFromRow(row));
          setHistory((prev) => ({
            soil: [...prev.soil, Math.round(row.soil_moisture ?? 0)].slice(-HISTORY_LENGTH),
            temp: [...prev.temp, Number((row.temperature ?? 0).toFixed(1))].slice(-HISTORY_LENGTH),
            humid: [...prev.humid, Math.round(row.humidity ?? 0)].slice(-HISTORY_LENGTH),
          }));
        }
      )
      .subscribe();

    channelsRef.current.status = supabase
      .channel(`status-${deviceId}-${uid}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'device_status', filter: `device_id=eq.${deviceId}` },
        (payload) => {
          if (payload.new) setPresence(applyStatusRow(payload.new as DeviceStatusRow));
        }
      )
      .subscribe();

    return () => {
      if (channelsRef.current.telemetry) supabase.removeChannel(channelsRef.current.telemetry);
      if (channelsRef.current.status) supabase.removeChannel(channelsRef.current.status);
      channelsRef.current = {};
    };
  }, [deviceId, seed]);

  // Going offline produces no database event — only elapsed time reveals it.
  useEffect(() => {
    const interval = setInterval(() => setTick((t) => t + 1), 5000);
    return () => clearInterval(interval);
  }, []);

  // Polling fallback. Realtime above is the fast path, but it can silently
  // deliver nothing — the channel may subscribe before realtime.setAuth()
  // has applied the user's token (RLS then rejects it), and the socket can
  // drop on background/foreground without recovering. Re-seeding on a timer
  // means the screen is never more than one ESP32 tick stale, which is what
  // stops "I have to pull-to-refresh to see new values".
  useEffect(() => {
    if (!deviceId) return;
    const poll = setInterval(() => seed(deviceId, true), 10000);  // ESP32 sends every 10s
    return () => clearInterval(poll);
  }, [deviceId, seed]);

  const connectionState: ConnectionState = computeConnectionState({
    hasDevice: !!deviceId,
    lastSeenMs: presence.lastSeenMs,
    sensorsOk: presence.sensorsOk,
  });
  void tick; // referenced only to force recomputation on the 5s ticker

  return {
    presence,
    telemetry,
    history,
    connectionState,
    loading,
    refresh: () => (deviceId ? seed(deviceId) : Promise.resolve()),
  };
}
