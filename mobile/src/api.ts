export class ApiError extends Error {
  constructor(message: string, public status = 0) { super(message); }
}

export type NativeDocument = { kind: 'file'; name: string; contentType: string; response: Response; cancel: () => void };

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
  const timeout = setTimeout(() => abort.abort(), path === 'workspace/' ? 120000 : 15000);
  const multipart = typeof FormData !== 'undefined' && data instanceof FormData;
  let handedOff = false;
  try {
    const transport = path === 'workspace/' ? (await import('expo/fetch')).fetch : fetch;
    const response = await transport(`${server}/api/mobile/v1/${path}`, {
      method: data === undefined ? 'GET' : 'POST', credentials: 'omit', redirect: 'error', cache: 'no-store',
      signal: abort.signal,
      headers: { Accept: 'application/json', ...(data === undefined || multipart ? {} : { 'Content-Type': 'application/json' }),
        ...(token ? { Authorization: `Bearer ${token}` } : {}) },
      ...(data === undefined ? {} : { body: multipart ? data : JSON.stringify(data) }),
    });
    if (path === 'workspace/' && response.ok && response.headers.get('X-IHRMS-Document') === '1') {
      const disposition = response.headers.get('Content-Disposition') || '';
      let name = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1] || disposition.match(/filename="?([^";]+)/i)?.[1] || 'IHRMS-document';
      try { name = decodeURIComponent(name); } catch { /* Keep a safe fallback below. */ }
      name = name.replace(/[\\/\x00-\x1f]/g, '_');
      const extension = name.match(/\.[A-Za-z0-9]{1,8}$/)?.[0] || '';
      name = (extension ? name.slice(0, -extension.length) : name).slice(0, 60) + extension;
      handedOff = true;
      return { kind: 'file', name, contentType: response.headers.get('Content-Type') || 'application/octet-stream',
        response, cancel: () => { clearTimeout(timeout); abort.abort(); } } as T;
    }
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new ApiError(body.error || (response.status === 429
      ? 'Đăng nhập tạm bị khóa. Vui lòng thử lại sau.' : 'Không thể xử lý yêu cầu. Vui lòng thử lại.'), response.status);
    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('Không có kết nối đến IHRMS. Kiểm tra mạng rồi thử lại.');
  } finally { if (!handedOff) clearTimeout(timeout); }
}
