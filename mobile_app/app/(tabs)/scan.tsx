import React, { useState } from 'react';
import { Alert, Image, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';
import Feather from '@expo/vector-icons/Feather';
import { colors, fontMono, radius, spacing } from '../../theme/tokens';
import { Card } from '../../components/Card';
import { Button } from '../../components/Button';
import { Badge } from '../../components/Badge';
import { ComingSoon } from '../../components/ComingSoon';
import { useAuth } from '../../hooks/useAuth';
import { diagnosePlant } from '../../lib/plant';
import type { PlantDiagnosis, PlantSeverity } from '../../lib/types';

// Lower JPEG quality keeps the upload small (faster over mobile data) while
// leaf lesions stay clearly visible to the model.
const PHOTO_QUALITY = 0.5;

function formatLabel(value: string | null | undefined): string {
  if (!value) return 'Unknown';
  return value.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

function confidenceTone(confidence: number): 'green' | 'amber' | 'rose' {
  if (confidence >= 0.8) return 'green';
  if (confidence >= 0.5) return 'amber';
  return 'rose';
}

function severityTone(severity: PlantSeverity): 'green' | 'amber' | 'rose' {
  if (severity === 'none') return 'green';
  if (severity === 'mild') return 'amber';
  return 'rose';
}

function summarize(result: PlantDiagnosis): string {
  const species = formatLabel(result.species);
  if (result.low_confidence || !result.condition) {
    return `I scanned a ${species} plant but the diagnosis was low-confidence. What should I check next?`;
  }
  const condition = formatLabel(result.condition);
  const extra = result.cause ? ` (likely ${formatLabel(result.cause)}, ${result.severity ?? 'unknown'} severity)` : '';
  return `I scanned a ${species} plant and it was diagnosed with ${condition}${extra}. What should I do about it?`;
}

export default function ScanScreen() {
  const router = useRouter();
  const { session } = useAuth();
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PlantDiagnosis | null>(null);

  async function runDiagnosis(uri: string) {
    if (!session) {
      Alert.alert('Not signed in', 'Please sign in again to scan a plant.');
      return;
    }
    setLoading(true);
    setResult(null);
    try {
      const diagnosis = await diagnosePlant(uri, session.access_token);
      setResult(diagnosis);
    } catch (err: any) {
      Alert.alert('Diagnosis failed', err?.message ?? 'Could not reach the diagnosis service.');
    } finally {
      setLoading(false);
    }
  }

  async function takePhoto() {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Camera permission needed', 'Enable camera access to scan a plant.');
      return;
    }
    const picked = await ImagePicker.launchCameraAsync({ quality: PHOTO_QUALITY, allowsEditing: true });
    if (picked.canceled || !picked.assets?.[0]) return;
    setPhotoUri(picked.assets[0].uri);
    await runDiagnosis(picked.assets[0].uri);
  }

  async function chooseFromLibrary() {
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Alert.alert('Photo library permission needed', 'Enable photo access to scan a plant.');
      return;
    }
    const picked = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      quality: PHOTO_QUALITY,
      allowsEditing: true,
    });
    if (picked.canceled || !picked.assets?.[0]) return;
    setPhotoUri(picked.assets[0].uri);
    await runDiagnosis(picked.assets[0].uri);
  }

  return (
    <SafeAreaView style={styles.flex} edges={['top']}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.title}>Plant Scan</Text>
        <Text style={styles.subtitle}>Identify plants and detect disease from a photo.</Text>

        <Card style={styles.previewCard}>
          {photoUri ? (
            <Image source={{ uri: photoUri }} style={styles.previewImage} resizeMode="cover" />
          ) : (
            <View style={styles.previewPlaceholder}>
              <Feather name="image" size={40} color={colors.textMuted} style={styles.previewIcon} />
              <Text style={styles.previewHint}>No image selected</Text>
            </View>
          )}
        </Card>

        <View style={styles.buttonRow}>
          <Button label="TAKE PHOTO" variant="secondary" onPress={takePhoto} loading={loading} style={styles.rowButton} />
          <Button
            label="CHOOSE FROM LIBRARY"
            variant="secondary"
            onPress={chooseFromLibrary}
            loading={loading}
            style={styles.rowButton}
          />
        </View>

        {result && result.is_plant === false ? (
          <Card style={styles.resultCard}>
            <Text style={styles.resultHeading}>Plant Identification</Text>
            <View style={styles.lowConfidenceBox}>
              <Badge label="NOT A PLANT" tone="rose" />
              <Text style={styles.lowConfidenceHint}>
                {result.notes || "This photo doesn't look like a plant or leaf. Try again with a clear shot of the plant."}
              </Text>
            </View>
          </Card>
        ) : (
          <>
            <Card style={styles.resultCard}>
              <Text style={styles.resultHeading}>Plant Identification</Text>
              {!result ? (
                <ComingSoon label={loading ? 'ANALYZING...' : 'TAKE OR CHOOSE A PHOTO'} />
              ) : (
                <View style={styles.resultRow}>
                  <Text style={styles.resultValue}>{formatLabel(result.species)}</Text>
                  <Badge
                    label={`${Math.round(result.species_confidence * 100)}%`}
                    tone={confidenceTone(result.species_confidence)}
                  />
                </View>
              )}
            </Card>

            <Card style={styles.resultCard}>
              <Text style={styles.resultHeading}>Disease Analysis</Text>
              {!result ? (
                <ComingSoon label={loading ? 'ANALYZING...' : 'TAKE OR CHOOSE A PHOTO'} />
              ) : result.low_confidence ? (
                <View style={styles.lowConfidenceBox}>
                  <Badge label="UNCLEAR PHOTO" tone="amber" />
                  <Text style={styles.lowConfidenceHint}>
                    We're not confident enough in this result to show a diagnosis. Try a closer, well-lit
                    photo of a single leaf.
                  </Text>
                </View>
              ) : (
                <>
                  <View style={styles.resultRow}>
                    <Text style={styles.resultValue}>{formatLabel(result.condition)}</Text>
                    <Badge
                      label={`${Math.round(result.condition_confidence * 100)}%`}
                      tone={confidenceTone(result.condition_confidence)}
                    />
                  </View>
                  {result.severity ? (
                    <View style={styles.resultRow}>
                      <Text style={styles.metaLabel}>
                        Severity{result.affected_area_pct != null ? ` · ${result.affected_area_pct}% affected` : ''}
                        {result.cause ? ` · ${formatLabel(result.cause)}` : ''}
                      </Text>
                      <Badge label={result.severity.toUpperCase()} tone={severityTone(result.severity)} />
                    </View>
                  ) : null}
                </>
              )}
            </Card>

            {result?.symptoms?.length ? (
              <Card style={styles.resultCard}>
                <Text style={styles.resultHeading}>Symptoms</Text>
                {result.symptoms.map((s, i) => (
                  <Text key={i} style={styles.bulletText}>• {s}</Text>
                ))}
              </Card>
            ) : null}

            {result?.treatment?.length ? (
              <Card style={styles.resultCard}>
                <Text style={styles.resultHeading}>Treatment</Text>
                {result.treatment.map((s, i) => (
                  <Text key={i} style={styles.bulletText}>• {s}</Text>
                ))}
              </Card>
            ) : null}

            {result?.prevention?.length ? (
              <Card style={styles.resultCard}>
                <Text style={styles.resultHeading}>Prevention</Text>
                {result.prevention.map((s, i) => (
                  <Text key={i} style={styles.bulletText}>• {s}</Text>
                ))}
              </Card>
            ) : null}
          </>
        )}

        {result ? (
          <Button
            label="ASK ADVISOR ABOUT THIS"
            variant="secondary"
            onPress={() => router.push({ pathname: '/(tabs)/advisor', params: { prefill: summarize(result) } })}
          />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: colors.bgMain },
  scroll: { padding: spacing.lg, paddingBottom: spacing.xxl },
  title: { color: colors.textPrimary, fontSize: 22, fontWeight: '800' },
  subtitle: { color: colors.textSecondary, fontSize: 12, marginTop: spacing.xs, marginBottom: spacing.lg },
  previewCard: { marginBottom: spacing.md, padding: 0, overflow: 'hidden' },
  previewImage: { height: 220, width: '100%', borderRadius: radius.lg },
  previewPlaceholder: {
    height: 220,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.bgSubtle,
    borderRadius: radius.lg,
  },
  previewIcon: { marginBottom: spacing.sm },
  previewHint: { color: colors.textMuted, fontSize: 12, fontFamily: fontMono },
  buttonRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.lg },
  rowButton: { flex: 1 },
  resultCard: { alignItems: 'stretch', marginBottom: spacing.md, gap: spacing.md },
  resultHeading: {
    color: colors.textPrimary,
    fontSize: 13,
    fontWeight: '700',
    fontFamily: fontMono,
    alignSelf: 'flex-start',
    marginBottom: spacing.sm,
  },
  resultRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  resultValue: { color: colors.textPrimary, fontSize: 16, fontWeight: '700' },
  lowConfidenceBox: { alignItems: 'center', gap: spacing.sm },
  lowConfidenceHint: { color: colors.textMuted, fontSize: 12, textAlign: 'center', lineHeight: 18 },
  metaLabel: { color: colors.textSecondary, fontSize: 12, flex: 1, marginRight: spacing.sm },
  bulletText: { color: colors.textPrimary, fontSize: 13, lineHeight: 19 },
});
