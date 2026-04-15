import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

export type EvaluateJobResponse<T = unknown> = {
  data: T | null
  error: string | null
}

export type GenerateMessageResponse<T = unknown> = {
  data: T | null
  error: string | null
}

export async function evaluateJob<T = unknown>(
  payload: Record<string, unknown>,
): Promise<EvaluateJobResponse<T>> {
  try {
    const response = await api.post<T>('/evaluate', payload)
    return {
      data: response.data,
      error: null,
    }
  } catch (err: unknown) {
    if (axios.isAxiosError(err)) {
      const detail =
        typeof err.response?.data?.detail === 'string'
          ? err.response.data.detail
          : null
      return {
        data: null,
        error: detail ?? err.message ?? 'Request failed',
      }
    }

    return {
      data: null,
      error: 'Unexpected error while calling /evaluate',
    }
  }
}

export async function generateMessage<T = unknown>(
  payload: Record<string, unknown>,
): Promise<GenerateMessageResponse<T>> {
  try {
    const response = await api.post<T>('/generate_message', payload)
    return {
      data: response.data,
      error: null,
    }
  } catch (err: unknown) {
    if (axios.isAxiosError(err)) {
      const detail =
        typeof err.response?.data?.detail === 'string'
          ? err.response.data.detail
          : null
      return {
        data: null,
        error: detail ?? err.message ?? 'Request failed',
      }
    }
    return {
      data: null,
      error: 'Unexpected error while calling /generate_message',
    }
  }
}
