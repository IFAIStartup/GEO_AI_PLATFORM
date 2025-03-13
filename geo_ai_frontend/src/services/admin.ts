import { AxiosResponse } from "axios";

import $api from "@services/http";
import {
  CreateUserParams,
  UpdateUserStatusParams,
  User,
  UpdateUserDataParams,
  GetUsersResponse,
  UserRoleWithAll,
  CreateGroupParams,
  Group,
  GetGroupsResponse,
} from "@models/user";
import { GetDataParams } from "@models/common";

export const getUsers = (
  params: GetDataParams<UserRoleWithAll, User>
): Promise<AxiosResponse<GetUsersResponse>> => {
  return $api.get("/auth/all-users", {
    params: {
      ...params,
      filter: params.filter === "all" ? undefined : params.filter,
    },
  });
};

export const createUser = (
  params: CreateUserParams
): Promise<AxiosResponse<User>> => {
  return $api.post("/auth/create-user", params);
};

export const updateUser = (
  params: UpdateUserDataParams
): Promise<AxiosResponse<User>> => {
  return $api.post<User>("/auth/change-user-data", params);
};

export const updateUserStatus = (
  params: UpdateUserStatusParams
): Promise<AxiosResponse<User>> => {
  return $api.post("/auth/change-status-user", params);
};

export const resendInvite = (id: number): Promise<AxiosResponse> => {
  return $api.get("/auth/invite-user", { params: { id } });
};

export const getGroups = (
  params: GetDataParams<null, Group>
): Promise<AxiosResponse<GetGroupsResponse>> => {
  return $api.get("/auth/all-groups", {
    params: {
      ...params,
      filter: undefined,
    },
  });
};

export const createGroup = (
  params: CreateGroupParams
): Promise<AxiosResponse<Group>> => {
  return $api.post("/auth/create-group", params);
};
