// Plant disease diagnosis — upload a photo, get species + condition back.
// Routes through backend/main.py's /api/plant/predict proxy, never
// directly to the plant-disease serving API — that API's key must stay
// server-side (see plant-disease-implementation-plan.md Phase J).
import { File } from 'expo-file-system';
import { BACKEND_BASE } from './supabase';
import type { PlantDiagnosis } from './types';

function requireBackend() {
  if (!BACKEND_BASE) {
    throw new Error(
      'EXPO_PUBLIC_BACKEND_URL is not set — plant diagnosis needs the FastAPI backend reachable from this phone.'
    );
  }
}

// `photoUri` is whatever expo-image-picker's result.assets[0].uri gives you
// (a local file:// / content:// URI on-device).
export async function diagnosePlant(photoUri: string, token: string): Promise<PlantDiagnosis> {
  requireBackend();

  const filename = photoUri.split('/').pop() || 'photo.jpg';
  const extMatch = /\.(\w+)$/.exec(filename);
  const ext = (extMatch?.[1] || 'jpg').toLowerCase();
  const mimeType = ext === 'png' ? 'image/png' : ext === 'webp' ? 'image/webp' : 'image/jpeg';

  const formData = new FormData();
  // Expo's fetch/FormData (SDK 52+) rejects the old RN {uri, name, type}
  // shape ("unsupported FormDataPart implementation") and wants a real
  // Blob — expo-file-system's File is one. Do NOT set a Content-Type header
  // manually, fetch sets the multipart boundary itself from the FormData body.
  formData.append('file', new File(photoUri), filename);

  const resp = await fetch(`${BACKEND_BASE}/api/plant/predict`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });

  if (!resp.ok) {
    let detail = `Diagnosis request failed (${resp.status})`;
    try {
      const body = await resp.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response body wasn't JSON — keep the generic message
    }
    throw new Error(detail);
  }

  return resp.json();
}
