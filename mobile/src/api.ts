export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message); }
}

export function serverURL(raw: string): string {
  let url: URL;
  try { url = new URL(raw.trim()); } catch { throw new ApiError('Vui lòng nhập địa chỉ IHRMS hợp lệ.'); }
  if (url.username || url.password || url.search || url.hash || (url.pathname !== '/' && url.pathname !== '')) {
    throw new ApiError('Địa chỉ IHRMS chỉ gồm giao thức, tên máy chủ và cổng nếu có.');
  }
  const privateHost = /^(localhost|127\.0\.0\.1|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)$/.test(url.hostname);
  if (url.protocol !== 'https:' && !(url.protocol === 'http:' && privateHost && process.env.EXPO_PUBLIC_ALLOW_HTTP === 'true')) {
    throw new ApiError('IHRMS yêu cầu kết nối HTTPS.');
  }
  return url.origin;
}

export async function call<T>(server: string, token: string | null, path: string, data?: unknown): Promise<T> {
  const abort = new AbortController();
  const timeout = setTimeout(() => abort.abort(), 15000);
  try {
    const response = await fetch(`${server}/api/mobile/v1/${path}`, {
      method: data === undefined ? 'GET' : 'POST', credentials: 'omit', redirect: 'error', cache: 'no-store',
      signal: abort.signal,
      headers: { Accept: 'application/json', ...(data === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(data === undefined ? {} : { body: JSON.stringify(data) }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new ApiError(body.error || (response.status === 429
      ? 'Đăng nhập tạm bị khóa. Vui lòng thử lại sau.' : 'Không thể xử lý yêu cầu. Vui lòng thử lại.'), response.status);
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Không có kết nối đến IHRMS. Kiểm tra mạng rồi thử lại.');
  } finally { clearTimeout(timeout); }
}
