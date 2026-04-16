/**
 * DeepInsight 2.0 API Hook
 * 封装对后端 FastAPI 的调用
 */

import { useState, useCallback } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface ActionQueueItem {
  type: 'text' | 'obs';
  content?: string;
  scene?: string;
}

export interface LiveScriptRequest {
  topic: string;
}

export interface LiveScriptResponse {
  success: boolean;
  topic: string;
  director_outline: string;
  anchor_output: string;
  raw_script: string;
  action_queue: ActionQueueItem[];
  obs_commands: Array<{ order: number; scene: string }>;
}

export interface TutorChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface TutorChatRequest {
  user_question: string;
  course_material: string;
  chat_history: TutorChatMessage[];
}

export interface TutorChatResponse {
  success: boolean;
  answer: string;
}

export interface BusinessAssetsResponse {
  success: boolean;
  course_material: string;
  xiaohongshu: string;
  douyin: string;
}

export interface JudgeReportResponse {
  success: boolean;
  full_report: string;
  radar_scores?: {
    geek_score: number;
    interaction_score: number;
    commerce_score: number;
  };
}

export interface HealthCheckResponse {
  status: string;
  version: string;
  timestamp: string;
}

interface UseApiState<T> {
  data: T | null;
  isLoading: boolean;
  error: string | null;
}

function useApiState<T>() {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const reset = useCallback(() => {
    setData(null);
    setIsLoading(false);
    setError(null);
  }, []);

  return { data, setData, isLoading, setIsLoading, error, setError, reset };
}

async function fetchApi<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

export function useDeepInsightApi() {
  const healthCheck = useApiState<HealthCheckResponse>();
  const liveScript = useApiState<LiveScriptResponse>();
  const tutorChat = useApiState<TutorChatResponse>();
  const businessAssets = useApiState<BusinessAssetsResponse>();
  const judgeReport = useApiState<JudgeReportResponse>();

  const checkHealth = useCallback(async () => {
    healthCheck.setIsLoading(true);
    healthCheck.setError(null);
    try {
      const data = await fetchApi<HealthCheckResponse>('/health');
      healthCheck.setData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '健康检查失败';
      healthCheck.setError(message);
      throw err;
    } finally {
      healthCheck.setIsLoading(false);
    }
  }, []);

  const generateLiveScript = useCallback(async (topic: string) => {
    liveScript.setIsLoading(true);
    liveScript.setError(null);
    try {
      const data = await fetchApi<LiveScriptResponse>('/api/v1/live/generate', {
        method: 'POST',
        body: JSON.stringify({ topic }),
      });
      liveScript.setData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '直播脚本生成失败';
      liveScript.setError(message);
      throw err;
    } finally {
      liveScript.setIsLoading(false);
    }
  }, []);

  const tutorChatAsk = useCallback(async (request: TutorChatRequest) => {
    tutorChat.setIsLoading(true);
    tutorChat.setError(null);
    try {
      const data = await fetchApi<TutorChatResponse>('/api/v1/tutor/chat', {
        method: 'POST',
        body: JSON.stringify(request),
      });
      tutorChat.setData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '助教回答失败';
      tutorChat.setError(message);
      throw err;
    } finally {
      tutorChat.setIsLoading(false);
    }
  }, []);

  const generateBusinessAssets = useCallback(async (actionQueue: ActionQueueItem[]) => {
    businessAssets.setIsLoading(true);
    businessAssets.setError(null);
    try {
      const data = await fetchApi<BusinessAssetsResponse>('/api/v1/business/generate', {
        method: 'POST',
        body: JSON.stringify({ action_queue: actionQueue }),
      });
      businessAssets.setData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '商业资产生成失败';
      businessAssets.setError(message);
      throw err;
    } finally {
      businessAssets.setIsLoading(false);
    }
  }, []);

  const generateJudgeReport = useCallback(async (
    actionQueue: ActionQueueItem[],
    danmuHistory: string = ''
  ) => {
    judgeReport.setIsLoading(true);
    judgeReport.setError(null);
    try {
      const data = await fetchApi<JudgeReportResponse>('/api/v1/judge/generate', {
        method: 'POST',
        body: JSON.stringify({
          action_queue: actionQueue,
          danmu_history: danmuHistory,
        }),
      });
      judgeReport.setData(data);
      return data;
    } catch (err) {
      const message = err instanceof Error ? err.message : '复盘报告生成失败';
      judgeReport.setError(message);
      throw err;
    } finally {
      judgeReport.setIsLoading(false);
    }
  }, []);

  return {
    healthCheck,
    liveScript,
    tutorChat,
    businessAssets,
    judgeReport,
    checkHealth,
    generateLiveScript,
    tutorChatAsk,
    generateBusinessAssets,
    generateJudgeReport,
  };
}

export type { UseApiState };
