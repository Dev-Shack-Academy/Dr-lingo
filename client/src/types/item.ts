/**
 * Item type definitions (example CRUD entity)
 */

export interface Item {
  id: number;
  name: string;
  description: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateItemData {
  name: string;
  description: string;
}

export interface UpdateItemData {
  name?: string;
  description?: string;
}

// Legacy alias for backward compatibility
export type ItemCreate = CreateItemData;
