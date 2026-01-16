import { AxiosRequestConfig, AxiosResponse } from 'axios';
import httpClient from './HttpClient';

type ParamsType = Record<string, unknown>;

/**
 * Wrapper to interact with the API.
 */
const ApiClient = {
  get: async <T>(resource: string, params?: ParamsType, baseURL?: string): Promise<T> => {
    const config: AxiosRequestConfig = {
      method: 'GET',
      url: resource,
      params,
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    };
    const response: AxiosResponse<T> = await httpClient.request<T>(config);
    return response.data;
  },

  delete: async <T>(resource: string, baseURL?: string): Promise<T> => {
    const config: AxiosRequestConfig = {
      method: 'DELETE',
      url: resource,
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    };
    const response: AxiosResponse<T> = await httpClient.request<T>(config);
    return response.data;
  },

  post: async <T>(resource: string, data: any, baseURL?: string): Promise<T> => {
    const config: AxiosRequestConfig = {
      method: 'POST',
      url: resource,
      data,
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    };
    const response: AxiosResponse<T> = await httpClient.request<T>(config);
    return response.data;
  },

  put: async <T>(resource: string, data: any, baseURL?: string): Promise<T> => {
    const config: AxiosRequestConfig = {
      method: 'PUT',
      url: resource,
      data,
      baseURL: baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
    };
    const response: AxiosResponse<T> = await httpClient.request<T>(config);
    return response.data;
  },
};

export default ApiClient;
