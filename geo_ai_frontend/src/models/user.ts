import { PaginationData } from "./common";

export interface User {
  id: number;
  email: string;
  username: string;
  role: Role;
  created_at: Date;
  is_active: boolean;
  external_user: boolean;
}

export interface LoginParams {
  email: string;
  password: string;
}

export interface ChangePasswordParams {
  id: number;
  old_password: string;
  password: string;
  confirm_password: string;
}

export interface RestoreAccessParams {
  email: string;
}

export interface ResetPasswordParams {
  key: string;
  password: string;
  confirm_password: string;
}

export interface CreateUserParams {
  username: string;
  email: string;
  role: Role;
}

export interface UpdateUserDataParams {
  id: number;
  username: string;
  role: Role;
}

export interface UpdateUserStatusParams {
  id: number;
  status: boolean;
}

export enum Role {
  User = "user",
  ML = "ml_user",
  Admin = "admin",
}

export type UserRoleWithAll = Role | "all";

export interface GetUsersResponse extends PaginationData {
  users: User[];
}

export interface CreateGroupParams {
  name: string;
}

export interface Group {
  id: number;
  name: string;
  users: User[];
  created_at: Date;
}

export interface GetGroupsResponse extends PaginationData {
  groups: Group[];
}
