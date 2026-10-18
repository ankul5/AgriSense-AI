import { useCallback, useEffect, useId, useRef, useState } from 'react';
import { supabase } from '../lib/supabase';
import * as controls from '../lib/controls';
import type { AutomationMode, DeviceConfigRow, Timer } from '../lib/types';
import { useAuth } from './useAuth';

const COMMAND_PENDING_TIMEOUT_MS = 10000;

const defaultThresholds = { startThreshold: 70, stopThreshold: 85, maxRuntimeMins: 20 };

export function useDeviceControls(deviceId: string | null) {
  // Dashboard and Soil tabs both mount this hook; supabase-js returns the
  // existing channel for a repeated topic, so each instance needs its own name.
  const uid = useId();
  const { session } = useAuth();
  const [pumpState, setPumpState] = useState<'RUNNING' | 'OFF'>('OFF');
  const [automationMode, setAutomationModeState] = useState<AutomationMode>('NONE');
  const [thresholds, setThresholds] = useState(defaultThresholds);
  const [timers, setTimers] = useState<Timer[]>([]);
  const [controlsLoading, setControlsLoading] = useState(false);
  const [commandPending, setCommandPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const pendingTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const channelRef = useRef<any>(null);

  const clearPendingTimeout = () => {
    if (pendingTimeoutRef.current) {
      clearTimeout(pendingTimeoutRef.current);
      pendingTimeoutRef.current = null;
    }
  };

  const applyConfigRow = useCallback((row: DeviceConfigRow) => {
    setPumpState(row.pump_on ? 'RUNNING' : 'OFF');
    setAutomationModeState(row.automation_mode);
    setThresholds({
      startThreshold: row.start_threshold,
      stopThreshold: row.stop_threshold,
      maxRuntimeMins: row.max_runtime_mins,
    });
    setCommandPending(false);
    clearPendingTimeout();
  }, []);

  const refreshTimers = useCallback(async () => {
    if (!deviceId || !session?.access_token) return;
    const list = await controls.loadTimers(deviceId, session.access_token);
    setTimers(list);
  }, [deviceId, session?.access_token]);

  const refreshControls = useCallback(async () => {
    if (!deviceId || !session?.access_token) return;
    setControlsLoading(true);
    setError(null);
    try {
      const state = await controls.getAutomationState(deviceId, session.access_token);
      setPumpState(state.pump_on ? 'RUNNING' : 'OFF');
      setAutomationModeState(state.automation_mode);
      setThresholds({
        startThreshold: state.start_threshold,
        stopThreshold: state.stop_threshold,
        maxRuntimeMins: state.max_runtime_mins,
      });
      await refreshTimers();
    } catch (err: any) {
      setError(err.message ?? 'Failed to load controls');
    } finally {
      setControlsLoading(false);
    }
  }, [deviceId, session?.access_token, refreshTimers]);

  useEffect(() => {
    setPumpState('OFF');
    setAutomationModeState('NONE');
    setThresholds(defaultThresholds);
    setTimers([]);
    setCommandPending(false);
    clearPendingTimeout();

    if (channelRef.current) {
      supabase.removeChannel(channelRef.current);
      channelRef.current = null;
    }

    if (!deviceId) return;

    refreshControls();

    // device_config is Realtime-enabled and RLS-scoped to the owning user —
    // this is what proves a pump/automation change actually took effect,
    // whether it came from this app, the website, a timer, or automation.
    channelRef.current = supabase
      .channel(`config-${deviceId}-${uid}`)
      .on(
        'postgres_changes',
        { event: '*', schema: 'public', table: 'device_config', filter: `device_id=eq.${deviceId}` },
        (payload) => {
          if (payload.new) applyConfigRow(payload.new as DeviceConfigRow);
        }
      )
      .subscribe();

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current);
        channelRef.current = null;
      }
      clearPendingTimeout();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [deviceId]);

  const armPendingTimeout = () => {
    clearPendingTimeout();
    pendingTimeoutRef.current = setTimeout(() => {
      setCommandPending(false);
      setError('No confirmation received from the device backend — command may not have applied.');
    }, COMMAND_PENDING_TIMEOUT_MS);
  };

  const runCommand = useCallback(async (fn: () => Promise<unknown>) => {
    if (commandPending || !deviceId) return;
    setCommandPending(true);
    setError(null);
    armPendingTimeout();
    try {
      await fn();
      // pumpState/automationMode update from the device_config Realtime
      // subscription above, not optimistically here.
    } catch (err: any) {
      setCommandPending(false);
      clearPendingTimeout();
      setError(err.message ?? 'Command failed');
      throw err;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [commandPending, deviceId]);

  const turnPumpOn = useCallback(
    () =>
      runCommand(() =>
        controls.sendPumpCommand(deviceId as string, 'PUMP_ON', session?.access_token as string)
      ),
    [runCommand, deviceId, session?.access_token]
  );
  const turnPumpOff = useCallback(
    () =>
      runCommand(() =>
        controls.sendPumpCommand(deviceId as string, 'PUMP_OFF', session?.access_token as string)
      ),
    [runCommand, deviceId, session?.access_token]
  );
  const forceStop = useCallback(
    () => runCommand(() => controls.forceStop(deviceId as string, session?.access_token as string)),
    [runCommand, deviceId, session?.access_token]
  );
  const setAutomationMode = useCallback(
    (mode: AutomationMode) =>
      runCommand(() =>
        controls.setAutomationMode(deviceId as string, mode, thresholds, session?.access_token as string)
      ),
    [runCommand, deviceId, thresholds, session?.access_token]
  );

  const createTimer = useCallback(
    async (payload: { startTime: string; durationMins: number; activeDays: string[] }) => {
      if (!deviceId || !session?.access_token) return;
      await controls.saveTimer(
        { deviceId, startTime: payload.startTime, durationMins: payload.durationMins, activeDays: payload.activeDays },
        session.access_token
      );
      await refreshTimers();
    },
    [deviceId, session?.access_token, refreshTimers]
  );

  const updateTimer = useCallback(
    async (timer: Timer, changes: { startTime: string; durationMins: number; activeDays: string[] }) => {
      if (!session?.access_token) return;
      await controls.updateTimer(timer, changes, session.access_token);
      await refreshTimers();
    },
    [session?.access_token, refreshTimers]
  );

  const deleteTimerById = useCallback(
    async (id: number) => {
      if (!session?.access_token) return;
      await controls.deleteTimer(id, session.access_token);
      await refreshTimers();
    },
    [session?.access_token, refreshTimers]
  );

  const toggleTimerActive = useCallback(
    async (id: number, isActive: boolean) => {
      if (!session?.access_token) return;
      setTimers((prev) => prev.map((t) => (t.id === id ? { ...t, is_active: isActive } : t)));
      try {
        await controls.toggleTimer(id, isActive, session.access_token);
      } catch (err) {
        await refreshTimers(); // revert to server truth
        throw err;
      }
    },
    [session?.access_token, refreshTimers]
  );

  return {
    pumpState,
    automationMode,
    thresholds,
    timers,
    controlsLoading,
    commandPending,
    error,
    turnPumpOn,
    turnPumpOff,
    setAutomationMode,
    createTimer,
    updateTimer,
    deleteTimer: deleteTimerById,
    toggleTimer: toggleTimerActive,
    forceStop,
    refreshControls,
  };
}
