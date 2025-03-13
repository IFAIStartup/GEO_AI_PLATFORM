import { create } from "zustand";
import { devtools } from "zustand/middleware";
import { immer } from "zustand/middleware/immer";

import {
  CreateUserParams,
  UpdateUserStatusParams,
  User,
  UpdateUserDataParams,
  UserRoleWithAll,
  CreateGroupParams,
  Group,
} from "@models/user";
import {
  createGroup,
  createUser,
  getGroups,
  getUsers,
  resendInvite,
  updateUser,
  updateUserStatus,
} from "@services/admin";
import { handleError } from "@services/http";
import { useAlertStore } from "./alert.store";
import { FilterSortData, GetDataParams, PaginationData } from "@models/common";

interface AdminState {
  users: User[];
  paginationData: PaginationData;
  filterSortData: FilterSortData<UserRoleWithAll, User>;
  setPaginationData: (paginationData: PaginationData) => Promise<void>;
  setFilterSortData: (
    filterSortData: FilterSortData<UserRoleWithAll, User>
  ) => Promise<void>;
  getUsers: (params: GetDataParams<UserRoleWithAll, User>) => Promise<void>;
  createUser: (params: CreateUserParams) => Promise<void>;
  updateUser: (params: UpdateUserDataParams) => Promise<void>;
  updateUserStatus: (params: UpdateUserStatusParams) => Promise<void>;
  resendInvite: (id: number) => Promise<void>;

  groups: Group[];
  groupsPaginationData: PaginationData;
  groupsFilterSortData: FilterSortData<null, Group>;
  setGroupsPaginationData: (paginationData: PaginationData) => Promise<void>;
  setGroupsFilterSortData: (
    filterSortData: FilterSortData<null, Group>
  ) => Promise<void>;
  getGroups: (params: GetDataParams<null, Group>) => Promise<void>;
  createGroup: (params: CreateGroupParams) => Promise<void>;
}

export const useAdminStore = create<AdminState>()(
  immer(
    devtools(
      (set, get) => ({
        users: [],
        paginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        filterSortData: {
          filter: "all",
        },
        setPaginationData: async (paginationData) => {
          set((state) => {
            state.paginationData = paginationData;
          });
          await get().getUsers({
            page: paginationData.page,
            limit: paginationData.limit,
            ...get().filterSortData,
          });
        },
        setFilterSortData: async (filterSortData) => {
          set((state) => {
            state.filterSortData = filterSortData;
          });
          const { page, limit } = get().paginationData;
          await get().getUsers({
            page,
            limit,
            ...get().filterSortData,
          });
        },
        getUsers: async () => {
          try {
            const { page, limit } = get().paginationData;
            const {
              data: { users, ...paginationData },
            } = await getUsers({
              page,
              limit,
              ...get().filterSortData,
            });
            set((state) => {
              state.users = users;
              state.paginationData = paginationData;
            });
          } catch (e) {
            handleError(e);
          }
        },
        createUser: async (params) => {
          await createUser(params);
          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.createUserSuccess",
          });
          try {
            const { page, limit } = get().paginationData;
            await get().getUsers({
              page,
              limit,
              ...get().filterSortData,
            });
          } catch (e) {
            handleError(e);
          }
        },
        updateUser: async (params) => {
          await updateUser(params);
          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.updateUserSuccess",
          });
          try {
            const { page, limit } = get().paginationData;
            await get().getUsers({
              page,
              limit,
              ...get().filterSortData,
            });
          } catch (e) {
            handleError(e);
          }
        },
        updateUserStatus: async (params) => {
          try {
            await updateUserStatus(params);
            const { page, limit } = get().paginationData;
            await get().getUsers({
              page,
              limit,
              ...get().filterSortData,
            });
            useAlertStore.getState().setAlert({
              severity: "success",
              key: "alerts.updateUserSuccess",
            });
          } catch (e) {
            handleError(e);
          }
        },
        resendInvite: async (id) => {
          try {
            await resendInvite(id);
            useAlertStore.getState().setAlert({
              severity: "success",
              key: "alerts.sendInvitationSuccess",
            });
          } catch (e) {
            handleError(e);
          }
        },

        groups: [],
        groupsPaginationData: {
          limit: 10,
          page: 1,
          pages: 1,
          total: 0,
        },
        groupsFilterSortData: {
          filter: null,
        },
        setGroupsPaginationData: async (paginationData) => {
          set((state) => {
            state.groupsPaginationData = paginationData;
          });
          await get().getGroups({
            page: paginationData.page,
            limit: paginationData.limit,
            ...get().groupsFilterSortData,
          });
        },
        setGroupsFilterSortData: async (filterSortData) => {
          set((state) => {
            state.groupsFilterSortData = filterSortData;
          });
          const { page, limit } = get().groupsPaginationData;
          await get().getGroups({
            page,
            limit,
            ...get().groupsFilterSortData,
          });
        },
        getGroups: async () => {
          try {
            const { page, limit } = get().groupsPaginationData;
            const { data } = await getGroups({
              page,
              limit,
              ...get().groupsFilterSortData,
            });
            set((state) => {
              state.groups = data.groups;
            });
          } catch (e) {
            handleError(e);
          }
        },
        createGroup: async (params) => {
          await createGroup(params);
          useAlertStore.getState().setAlert({
            severity: "success",
            key: "alerts.createGroupSuccess",
          });
          try {
            const { page, limit } = get().groupsPaginationData;
            await get().getGroups({
              page,
              limit,
              ...get().groupsFilterSortData,
            });
          } catch (e) {
            handleError(e);
          }
        },
      }),
      {
        enabled: import.meta.env.DEV,
        store: "admin-store",
      }
    )
  )
);
